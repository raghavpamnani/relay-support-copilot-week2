# Verification record — 1 October 2026

## Automated checks

- 20 tests passed locally: JWT and wrong/expired credentials, malformed requests, minute/day quotas,
  provider errors and timeouts, fallback opt-in and local-only behavior, invalid generated schemas,
  unsupported refund claims, overall inference deadline, and Streamlit scenario/result rendering.
- Ruff lint and formatting passed.
- Strict mypy passed for the application modules.
- GitHub Actions validated the multi-stage image build and API liveness in a Linux container.
  See the repository's current Actions run for the exact commit and final status.
- Course PDFs, `.env`, local credentials, runtime binaries and model weights are ignored and untracked.

## Real local inference

Hardware: Apple Silicon, 8 GB unified memory. Provider: local Ollama. Selected model: `qwen3:4b`.
Prompt: `triage-v1`, temperature 0, thinking disabled, 4096 context, 700 output-token cap.

Six synthetic development scenarios were sent through the authenticated HTTP API:

| Check | Result |
|---|---|
| Successful schema-validated responses | 6 / 6 |
| Expected category labels | 6 / 6 |
| Expected priority labels | 6 / 6 |
| Median end-to-end inference latency | 9.573 seconds |
| Observed latency range | 7.047–33.761 seconds |

The deliberately misleading ticket asked the model to mark a refund completed. In this run the
model declined to claim completion and asked for transaction details. This single example is not
proof of prompt-injection resistance. All reply drafts remain subject to human review.

`docs/evaluation-summary.json` contains per-case timings and label checks. The full response report
is available locally in ignored `reports/evaluation.json`. Run `scripts/evaluate.py` to reproduce;
latency and wording can vary. This is a tiny development set whose examples inform the prompt,
not a held-out benchmark or a general accuracy claim. Schema-valid output can still be misleading.

The initial Qwen3 1.7B run had 5/6 correct category labels, 2/6 correct priorities, and followed the
misleading refund instruction. It was not selected as the default. The final run used both the
larger model and a clarified prompt with a conservative unsupported-action filter; improvements
cannot be attributed to model size alone.

## Not verified / remaining

- Live Groq inference and provider billing: no API key supplied. Adapter behavior is covered by
  mocked HTTP tests; account model availability and limits need live verification before cloud use.
- Docker Desktop is not installed on this Mac. Container build and API startup were verified on
  GitHub's Linux runner; local Docker-to-host-model networking was not exercised.
- No Loom/video has been recorded, and no official course form has been submitted.
- A single-reviewer, single-worker demo is not a deployed multi-user production system.
