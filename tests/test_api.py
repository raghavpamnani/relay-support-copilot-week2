from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.main import create_app
from app.providers import Inference, ProviderError
from app.schemas import Triage
from app.security import password_hasher

PASSWORD = "test-password-for-ci"
HASH = password_hasher.hash(PASSWORD)
TICKET = {"subject": "Duplicate payment", "description": "I was charged twice for my subscription."}
VALID = {
    "category": "billing",
    "priority": "medium",
    "summary": "Duplicate subscription charge.",
    "rationale": "Customer reports two charges.",
    "suggested_reply": "Please share your transaction reference so we can investigate.",
    "next_steps": ["Review the payment history"],
    "needs_human_review": True,
}


class FakeGateway:
    calls = 0

    async def run(self, ticket):
        self.calls += 1
        return Inference(Triage(**VALID), "local", "test-model", 100, 50)


def config(**kwargs):
    return Settings(
        _env_file=None, jwt_secret=SecretStr("x" * 48), demo_password_hash=SecretStr(HASH), **kwargs
    )


def headers(client):
    response = client.post(
        "/api/v1/auth/token", json={"username": "reviewer", "password": PASSWORD}
    )
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def test_auth_validation_and_success():
    gateway = FakeGateway()
    with TestClient(create_app(config(), gateway)) as client:
        assert client.get("/healthz").status_code == 200
        assert client.post("/api/v1/tickets/triage", json=TICKET).status_code == 401
        assert (
            client.post(
                "/api/v1/auth/token", json={"username": "reviewer", "password": "wrong"}
            ).status_code
            == 401
        )
        auth = headers(client)
        for bad in [
            {**TICKET, "subject": 123},
            {**TICKET, "extra": True},
            {**TICKET, "description": " " * 20},
            {**TICKET, "provider": "unknown"},
            {**TICKET, "description": "x" * 4001},
        ]:
            assert client.post("/api/v1/tickets/triage", json=bad, headers=auth).status_code == 422
        assert gateway.calls == 0
        response = client.post("/api/v1/tickets/triage", json=TICKET, headers=auth)
        assert response.status_code == 200
        assert response.json()["metadata"]["provider"] == "local"
        assert response.json()["metadata"]["schema_valid"] is True


@pytest.mark.parametrize("kind", ["expired", "wrong-key", "wrong-user", "wrong-audience"])
def test_reject_bad_jwt(kind):
    now = datetime.now(UTC)
    payload = {
        "sub": "other" if kind == "wrong-user" else "reviewer",
        "iat": now,
        "exp": now + timedelta(minutes=-1 if kind == "expired" else 10),
        "iss": "relay",
        "aud": "wrong" if kind == "wrong-audience" else "relay-api",
    }
    token = jwt.encode(payload, "z" * 48 if kind == "wrong-key" else "x" * 48, algorithm="HS256")
    with TestClient(create_app(config(), FakeGateway())) as client:
        response = client.post(
            "/api/v1/tickets/triage", json=TICKET, headers={"Authorization": "Bearer " + token}
        )
        assert response.status_code == 401


def test_rate_limit_prevents_inference():
    gateway = FakeGateway()
    with TestClient(create_app(config(requests_per_minute=1), gateway)) as client:
        auth = headers(client)
        assert client.post("/api/v1/tickets/triage", json=TICKET, headers=auth).status_code == 200
        assert client.post("/api/v1/tickets/triage", json=TICKET, headers=auth).status_code == 429
        assert gateway.calls == 1


def test_daily_limit():
    with TestClient(create_app(config(daily_request_limit=1), FakeGateway())) as client:
        auth = headers(client)
        assert client.post("/api/v1/tickets/triage", json=TICKET, headers=auth).status_code == 200
        assert client.post("/api/v1/tickets/triage", json=TICKET, headers=auth).status_code == 429


def test_model_failure_has_request_id():
    class Broken:
        async def run(self, ticket):
            raise ProviderError("Model unavailable", retryable=True)

    with TestClient(create_app(config(), Broken())) as client:
        response = client.post("/api/v1/tickets/triage", json=TICKET, headers=headers(client))
        assert response.status_code == 503
        assert response.json()["detail"]["request_id"]


def test_total_inference_deadline():
    import asyncio

    class Slow:
        async def run(self, ticket):
            await asyncio.sleep(0.1)

    with TestClient(create_app(config(inference_timeout=0.01), Slow())) as client:
        response = client.post("/api/v1/tickets/triage", json=TICKET, headers=headers(client))
        assert response.status_code == 503
        assert "deadline" in response.json()["detail"]["message"]
