import json

import httpx
import pytest
from pydantic import SecretStr

from app.providers import ModelGateway, ProviderError
from app.schemas import Ticket
from tests.test_api import TICKET, VALID, config


@pytest.mark.asyncio
async def test_local_schema_and_metadata():
    def handle(request):
        body = json.loads(request.content)
        assert body["format"]["additionalProperties"] is False
        assert body["think"] is False
        return httpx.Response(
            200,
            json={
                "message": {"content": json.dumps(VALID)},
                "prompt_eval_count": 90,
                "eval_count": 40,
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await ModelGateway(config(), client).run(Ticket(**TICKET))
        assert result.triage.category == "billing"
        assert result.input_tokens == 90
        assert not result.fallback_used


@pytest.mark.parametrize(
    "provider,allow,expected",
    [("auto", False, False), ("auto", True, True), ("local", True, False)],
)
async def test_fallback_requires_opt_in(provider, allow, expected):
    visited = []

    def handle(request):
        visited.append(request.url.host)
        if request.url.host == "127.0.0.1":
            return httpx.Response(503)
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(VALID)}}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        gateway = ModelGateway(
            config(allow_cloud_fallback=allow, groq_api_key=SecretStr("test")), client
        )
        ticket = Ticket(**TICKET, provider=provider)
        if expected:
            result = await gateway.run(ticket)
            assert result.fallback_used and result.provider == "cloud"
        else:
            with pytest.raises(ProviderError):
                await gateway.run(ticket)
            assert visited == ["127.0.0.1"]


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "{}",
        json.dumps({**VALID, "priority": "critical"}),
        json.dumps({**VALID, "needs_human_review": "yes"}),
    ],
)
async def test_invalid_output_never_accepted_or_cloud_retried(content):
    visited = []

    def handle(request):
        visited.append(request.url.host)
        return httpx.Response(200, json={"message": {"content": content}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        gateway = ModelGateway(
            config(allow_cloud_fallback=True, groq_api_key=SecretStr("test")), client
        )
        with pytest.raises(ProviderError, match="invalid response"):
            await gateway.run(Ticket(**TICKET))
        assert visited == ["127.0.0.1"]


async def test_timeout_and_missing_cloud_key():
    def handle(request):
        raise httpx.ReadTimeout("timeout")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        gateway = ModelGateway(config(), client)
        with pytest.raises(ProviderError, match="timed out"):
            await gateway.run(Ticket(**TICKET))
        with pytest.raises(ProviderError, match="not configured"):
            await gateway.run(Ticket(**TICKET, provider="cloud"))
