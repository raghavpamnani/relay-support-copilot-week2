# Week 2 alignment: Days 6–9

| Course topic | Project evidence |
|---|---|
| Day 6: strict typing, Pydantic v2 | Strict request/output schemas, strict mypy on app |
| uv packaging, reproducibility | pyproject.toml, uv.lock, uv sync --frozen |
| Streamlit, requests, JSON | Authenticated UI calling HTTP API; JSON export |
| Async Python | Async model calls and bounded inference concurrency |
| Day 7: AI service/API boundaries | App factory, auth dependency, separate model gateway |
| Authentication | Argon2id credentials and expiring verified JWTs |
| AI usage controls | Input/output bounds, concurrency, request quotas, timeouts |
| Versioned contracts | /api/v1 routes and OpenAPI documentation |
| Day 8: GitHub Actions | Lint/types/tests and container smoke workflow |
| Pre-commit and review | Local hooks; review checklist below |
| Docker/multi-stage | Builder + non-root runtime; Compose UI/API |
| Day 9: role/instruction prompting | prompts/triage-v1.txt; role, rules, few-shot examples |
| Reusable prompts | Version reported in each inference response |
| AI-assisted development | Reviewed generated code; tests and real model checks |

No Day 10 handout was provided. This scope uses Days 6–9 and the kickoff's open-model,
containerized FastAPI, JWT, validation, public repository and two-minute demo requirements.

## Code review checklist

- Does the contract reject malformed and unexpected fields?
- Can external ticket text override system rules or induce invented actions?
- Do provider errors avoid leaking keys and upstream response bodies?
- Are secrets, course PDFs, local runtimes and model weights excluded?
- Does an explicit local request stay local?
- Are reported tests actual runs, and are mocks separated from real inference?

AI assistance was used to draft implementation and tests. Review focused on authentication,
secret handling, outbound provider selection, failure paths and truthful execution metadata.
Model behavior remains probabilistic; a small smoke set is not a security or accuracy guarantee.
