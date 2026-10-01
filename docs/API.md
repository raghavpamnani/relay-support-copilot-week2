# API contract v1

Interactive OpenAPI documentation is at `/docs` while the API runs.

| Method and path | Authentication | Purpose |
|---|---|---|
| GET `/healthz` | None | API liveness; not model readiness |
| POST `/api/v1/auth/token` | Username/password JSON | JWT valid for 30 minutes |
| GET `/api/v1/providers` | Bearer JWT | Local readiness, cloud configuration, limits |
| POST `/api/v1/tickets/triage` | Bearer JWT | Structured triage + metadata |

Login JSON: `{"username":"reviewer","password":"your-private-password"}`.
Copy the returned `access_token` into the Swagger Authorize dialog.

Triage JSON:
```json
{
  "subject": "Duplicate charge on subscription",
  "description": "My monthly subscription was charged twice yesterday. Please investigate.",
  "provider": "local"
}
```

Response fields: `triage.category`, `priority`, `summary`, `rationale`, `suggested_reply`,
`next_steps`, `needs_human_review`; plus `metadata.request_id`, `provider`, `model`,
`prompt_version`, `latency_ms`, `input_tokens`, `output_tokens`, `fallback_used`, `schema_valid`.
Missing provider token counts remain null; they are never fabricated.

Errors: 401 unauthenticated/expired session; 422 invalid input; 429 quota exceeded;
502 unconfigured provider or invalid model output; 503 model busy/unavailable/timeout.
A failed inference includes a request ID. No partial invalid draft is returned.

Contracts reject unknown fields and coercion. Subject: 5–200 characters; description: 15–4000.
Provider values: auto/local/cloud. A future incompatible contract should receive `/api/v2`.
