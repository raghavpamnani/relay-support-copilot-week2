# Two-minute demo

Before recording: start Ollama, API and UI; sign in; run one warm-up inference; open GitHub and API
docs in adjacent tabs. Use synthetic tickets. Keep credentials and terminal secrets off screen.

**0:00–0:15 — Problem and product**
"Relay helps support agents turn an incoming ticket into a structured, reviewable response. It is
powered by a real open model and a secure FastAPI service."

**0:15–0:45 — Real local inference**
Select Duplicate charge, choose Local, and Analyze. Show category, priority, summary and draft.
"The response is a draft. It does not claim a refund has been issued. Human review is required."
If inference takes longer, use that time to explain validation; do not edit out time and claim faster latency.

**0:45–1:05 — Execution evidence**
Show the model/provider, timing, token counts, prompt version and validated JSON.
"These values come from the actual request. Local mode never silently switches to the cloud."

**1:05–1:25 — Engineering behavior**
Show a missing-token 401 using API docs or a prepared terminal request. Show a malformed body
rejected with 422. Explain rate/usage controls and output validation.

**1:25–1:45 — Architecture and reproducibility**
Show README architecture link, uv.lock, Dockerfile and GitHub Actions results.
"The interface, API contracts, and model gateway are separate. CI checks types, tests and the image."
Only say CI passed if the current GitHub run is green.

**1:45–2:00 — Close**
"Auto mode prefers local, with an optional configured API fallback. The repository includes setup,
API documentation and evaluation tooling. All customer replies stay under human control."

Record in your own voice. Publish the video with reviewer-accessible permissions and add the
actual URL to the README; no video link is fabricated by this project.
