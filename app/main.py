import asyncio
import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any, Protocol

import httpx
import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings
from app.limits import UsageControl
from app.providers import PROMPT_VERSION, Inference, ModelGateway, ProviderError
from app.schemas import Login, Metadata, Ticket, TicketResult
from app.security import decode_token, issue_token, password_hasher

logger = logging.getLogger("relay")
bearer = HTTPBearer(auto_error=False)


class Gateway(Protocol):
    async def run(self, ticket: Ticket) -> Inference: ...


def create_app(settings: Settings | None = None, gateway: Gateway | None = None) -> FastAPI:
    config = settings or Settings()
    usage = UsageControl(config.requests_per_minute, config.daily_request_limit)
    login_usage = UsageControl(10, 500)
    slots = asyncio.Semaphore(config.max_concurrent)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        async with httpx.AsyncClient() as client:
            app.state.gateway = gateway or ModelGateway(config, client)
            yield

    app = FastAPI(
        title="Relay · Support Copilot",
        version="1.0.0",
        lifespan=lifespan,
        description="Authenticated, local-first support triage. Drafts need agent review.",
    )

    def authenticated(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> str:
        if credentials is None:
            raise HTTPException(
                401, "Sign in to use Relay.", headers={"WWW-Authenticate": "Bearer"}
            )
        try:
            return decode_token(credentials.credentials, config)
        except jwt.InvalidTokenError as exc:
            raise HTTPException(
                401,
                "Invalid or expired session. Sign in again.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    @app.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "relay", "version": "1.0.0"}

    @app.post("/api/v1/auth/token")
    async def login(body: Login, request: Request) -> dict[str, str | int]:
        await login_usage.consume("login")
        # Verify even for an unknown username to reduce account enumeration via timing.
        valid_password = await asyncio.to_thread(
            password_hasher.verify, body.password, config.demo_password_hash.get_secret_value()
        )
        if body.username != config.demo_username or not valid_password:
            raise HTTPException(401, "Invalid username or password.")
        return {"access_token": issue_token(config), "token_type": "bearer", "expires_in": 1800}

    @app.get("/api/v1/providers")
    async def providers(user: Annotated[str, Depends(authenticated)]) -> dict[str, Any]:
        ready = False
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get(config.ollama_url.rstrip("/") + "/api/tags")
                response.raise_for_status()
                ready = any(
                    m.get("name") == config.ollama_model for m in response.json().get("models", [])
                )
        except (httpx.HTTPError, ValueError, TypeError):
            pass
        return {
            "local": {"ready": ready, "model": config.ollama_model},
            "cloud": {
                "configured": bool(config.groq_api_key.get_secret_value()),
                "model": config.groq_model,
            },
            "cloud_fallback": config.allow_cloud_fallback,
            "limits": {
                "requests_per_minute": config.requests_per_minute,
                "daily_requests": config.daily_request_limit,
            },
        }

    @app.post("/api/v1/tickets/triage", response_model=TicketResult)
    async def triage(
        body: Ticket, request: Request, user: Annotated[str, Depends(authenticated)]
    ) -> TicketResult:
        await usage.consume(user)
        if slots.locked():
            raise HTTPException(
                503, "Model is busy. Please retry shortly.", headers={"Retry-After": "5"}
            )
        request_id = str(uuid.uuid4())
        started = time.perf_counter()
        async with slots:
            try:
                async with asyncio.timeout(config.inference_timeout):
                    result = await request.app.state.gateway.run(body)
            except TimeoutError as exc:
                raise HTTPException(
                    503, {"message": "Inference deadline exceeded.", "request_id": request_id}
                ) from exc
            except ProviderError as exc:
                logger.warning("inference_failed request_id=%s", request_id)
                raise HTTPException(
                    503 if exc.retryable else 502, {"message": str(exc), "request_id": request_id}
                ) from exc
        latency = round((time.perf_counter() - started) * 1000)
        logger.info(
            "triage request_id=%s provider=%s latency_ms=%d", request_id, result.provider, latency
        )
        return TicketResult(
            triage=result.triage,
            metadata=Metadata(
                request_id=request_id,
                provider=result.provider,
                model=result.model,
                prompt_version=PROMPT_VERSION,
                latency_ms=latency,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                fallback_used=result.fallback_used,
            ),
        )

    return app
