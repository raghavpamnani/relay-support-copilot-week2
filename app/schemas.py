from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class Login(StrictModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class Ticket(StrictModel):
    subject: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=15, max_length=4000)
    provider: Literal["auto", "local", "cloud"] = "auto"


class Triage(StrictModel):
    category: Literal["billing", "account", "technical", "delivery", "other"]
    priority: Literal["low", "medium", "high", "urgent"]
    summary: str = Field(min_length=10, max_length=600)
    rationale: str = Field(min_length=10, max_length=600)
    suggested_reply: str = Field(min_length=20, max_length=2000)
    next_steps: list[str] = Field(min_length=1, max_length=5)
    needs_human_review: bool


class Metadata(StrictModel):
    request_id: str
    provider: Literal["local", "cloud"]
    model: str
    prompt_version: str
    latency_ms: int
    input_tokens: int | None
    output_tokens: int | None
    fallback_used: bool
    schema_valid: bool = True


class TicketResult(StrictModel):
    triage: Triage
    metadata: Metadata
