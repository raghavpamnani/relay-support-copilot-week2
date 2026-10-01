# ◈ Relay — Support Ticket Copilot

[![Quality and container](https://github.com/raghavpamnani/relay-support-copilot-week2/actions/workflows/ci.yml/badge.svg)](https://github.com/raghavpamnani/relay-support-copilot-week2/actions/workflows/ci.yml)

**Turn a customer issue into structured triage and a considered reply draft.**

Relay is a Week 2 AI engineering demo: a JWT-protected FastAPI microservice, a Streamlit
support desk, and real open-model inference. It classifies tickets, identifies urgency,
and drafts next steps with typed, validated JSON and visible execution evidence.

> Human-reviewed drafts only. Relay never sends a customer message or performs refunds.
> Course PDFs, credentials, model weights, and local runtime files are excluded from Git.

## Start locally

Prerequisites: Python 3.12, [uv](https://docs.astral.sh/uv/getting-started/installation/),
[Ollama](https://ollama.com/download). The default Qwen3 4B is a small open-weight model;
quality and latency must be evaluated for your workload. Internet is needed for initial downloads.

```bash
uv sync --frozen
uv run python scripts/setup_local.py
ollama pull qwen3:4b
# Start `ollama serve` in another terminal if the Ollama service is not running.
uv run uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

In a second terminal, from the repository directory:

```bash
uv run streamlit run ui/app.py --server.address 127.0.0.1
```

Open **http://localhost:8501**. Sign in as `reviewer` using the password chosen during setup.
API docs: **http://localhost:8000/docs**. Liveness: **http://localhost:8000/healthz**.

Try **Duplicate charge**, then **Production outage**. Inspect Execution evidence and export the JSON.
The first inference can be slower because model loading is included. There is no fake inference mode.

After setup, you can start both app services together with `uv run python scripts/run_demo.py`.
Ollama must already be running for local mode. Stop with Ctrl+C.

## Provider selection

| Mode | Behavior |
|---|---|
| Local | Only Ollama; an unavailable model produces an explicit error. |
| Cloud | Only Groq; requires a private `GROQ_API_KEY` in `.env`. |
| Auto | Local first; eligible availability failures may use Groq only when `ALLOW_CLOUD_FALLBACK=true` and a key is configured. |

Cloud mode sends ticket text to the provider. Use synthetic tickets for demos. A malformed model
response is rejected, not silently retried with a cloud provider. Every successful result identifies
the actual provider, model, prompt version, latency, reported token counts, and whether fallback occurred.
Groq's `llama-3.3-70b-versatile` is configurable; confirm availability and account limits before use.
Cloud uses JSON mode plus application-side schema validation, not a claim of provider-enforced strict schema.

## Containers

```bash
# Create .env and pull the model first, as above.
docker compose up --build
```

FastAPI and Streamlit run as a non-root user in containers. Ollama runs on the host to allow native
Apple Silicon acceleration. Docker Desktop must allow containers to reach the host Ollama service;
if your host binding does not allow that, configure Ollama's host binding for your trusted local
network. Never expose an unauthenticated Ollama port to the internet. Linux also needs an accessible
host binding; the Compose file supplies `host.docker.internal:host-gateway`.

For an API-only setup, configure Groq and choose Cloud in the UI; no local model is required.
The final image excludes the build toolchain, private PDFs, credentials, and model weights.

## Quality gates

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest -q
uv run pre-commit install
uv run python scripts/evaluate.py --provider local
```

CI runs formatting, lint, strict application typing, automated API/provider tests, a private-file
check, and a Docker build/health smoke test. Tests use explicit injected fakes and HTTP mocks;
the evaluation command uses real inference. Its report is written to ignored `reports/evaluation.json`.
The six examples are smoke checks, not an independent accuracy benchmark.

## Project map

- `app/`: configuration, authentication, contracts, limits, provider adapters, HTTP routes.
- `prompts/`: versioned system prompt and few-shot policy examples.
- `ui/`: Streamlit reviewer interface using the HTTP API via requests.
- `tests/`: security, schema, rate/usage control, and provider failure cases.
- `examples/`: synthetic tickets and expected classification labels.
- `docs/`: architecture, API guide, curriculum mapping, demo script, verification and submission notes.
- `scripts/`: private credential setup and real-model evaluation.

## Scope and limitations

This is an engineering demo, not a production support platform. It uses one configured reviewer
account and in-memory rate limits with a single API worker. Restarts reset quotas. Production needs
an identity provider, shared quota storage, durable audit records, TLS, and broader model evaluation.
Input length, output tokens, concurrency, per-minute requests, and daily requests are bounded.
Request quotas include failed/busy attempts; they are not billing-grade token accounting.
A conservative phrase filter withholds certain unsupported action claims, but can have false positives
and miss paraphrases. Schema validity does not prove factual accuracy or prompt-injection resistance. Review every reply.
No ticket persistence is implemented; signing out clears the browser session's result.

## References

- [FastAPI JWT authentication](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
- [Qwen3 model family](https://ollama.com/library/qwen3)
- [Groq JSON mode](https://console.groq.com/docs/structured-outputs)
- [uv with Docker](https://docs.astral.sh/uv/guides/integration/docker/)

See [the demo script](docs/DEMO_SCRIPT.md) and [submission checklist](docs/SUBMISSION.md).
