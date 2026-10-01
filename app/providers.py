import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import ValidationError

from app.config import Settings
from app.schemas import Ticket, Triage

PROMPT_VERSION = "triage-v1"
PROMPT = (Path(__file__).resolve().parent.parent / "prompts/triage-v1.txt").read_text()


class ProviderError(Exception):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


@dataclass
class Inference:
    triage: Triage
    provider: Literal["local", "cloud"]
    model: str
    input_tokens: int | None
    output_tokens: int | None
    fallback_used: bool = False


def token_count(value: Any) -> int | None:
    return value if type(value) is int and value >= 0 else None


class ModelGateway:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self.settings = settings
        self.client = client

    async def run(self, ticket: Ticket) -> Inference:
        if ticket.provider == "cloud":
            return await self._infer(ticket, "cloud")
        try:
            return await self._infer(ticket, "local")
        except ProviderError as exc:
            if (
                ticket.provider == "auto"
                and exc.retryable
                and self.settings.allow_cloud_fallback
                and self.settings.groq_api_key.get_secret_value()
            ):
                result = await self._infer(ticket, "cloud")
                result.fallback_used = True
                return result
            raise

    async def _infer(self, ticket: Ticket, provider: Literal["local", "cloud"]) -> Inference:
        schema = Triage.model_json_schema()
        messages = [
            {"role": "system", "content": PROMPT + "\nOutput schema:\n" + json.dumps(schema)},
            {
                "role": "user",
                "content": json.dumps(
                    {"subject": ticket.subject, "description": ticket.description}
                ),
            },
        ]
        if provider == "local":
            model = self.settings.ollama_model
            url = self.settings.ollama_url.rstrip("/") + "/api/chat"
            headers: dict[str, str] = {}
            body: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "format": schema,
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "num_predict": 700, "num_ctx": 4096},
            }
        else:
            key = self.settings.groq_api_key.get_secret_value()
            if not key:
                raise ProviderError(
                    "Cloud provider is not configured. Use Local or configure Groq."
                )
            model = self.settings.groq_model
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {key}"}
            # JSON mode is portable; Pydantic performs strict application-side validation.
            body = {
                "model": model,
                "messages": messages,
                "temperature": 0,
                "max_tokens": 700,
                "response_format": {"type": "json_object"},
            }
        try:
            response = await self.client.post(
                url, headers=headers, json=body, timeout=self.settings.inference_timeout
            )
            if response.status_code >= 400:
                retryable = response.status_code in {404, 429, 500, 502, 503, 504}
                raise ProviderError(
                    f"{provider.title()} model unavailable ({response.status_code}).",
                    retryable=retryable,
                )
            data = response.json()
            if provider == "local":
                content = data["message"]["content"]
                incoming = token_count(data.get("prompt_eval_count"))
                outgoing = token_count(data.get("eval_count"))
            else:
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage") or {}
                incoming = token_count(usage.get("prompt_tokens"))
                outgoing = token_count(usage.get("completion_tokens"))
            triage = Triage.model_validate_json(content)
            if triage.priority == "urgent":
                triage.needs_human_review = True
            return Inference(triage, provider, model, incoming, outgoing)
        except httpx.TimeoutException as exc:
            raise ProviderError(
                f"{provider.title()} model timed out. Please retry.", retryable=True
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(
                f"Cannot reach {provider} model. Check provider setup.", retryable=True
            ) from exc
        except (ValidationError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                "Model returned an invalid response. No draft was accepted."
            ) from exc
