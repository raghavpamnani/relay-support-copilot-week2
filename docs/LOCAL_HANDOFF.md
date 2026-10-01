# Local handoff

The prepared workspace includes a private `.env`, an ignored `.local-runtime` directory with
Ollama/model files, and a `.venv`. These machine-specific files are not in GitHub.

While the services started during preparation are running:

- UI: http://localhost:8501
- API documentation: http://localhost:8000/docs
- Username: `reviewer`
- Generated password: open `.local-runtime/demo-password.txt` locally. Do not share or record it.

If only the API/UI need restarting, from this folder run:

```bash
.venv/bin/python scripts/run_demo.py
```

If Ollama is also stopped, use the standard Ollama setup in README, or start the downloaded
`.local-runtime/ollama` runtime with `OLLAMA_MODELS` pointing to this folder's
`.local-runtime/models`. Keep the server bound to loopback for the native demo.

For another computer or a fresh clone, follow README instead: install uv and Ollama, sync locked
Python dependencies, generate your own credentials, and pull the configured model.

Record with synthetic tickets and a warm model. The final submission still needs your recorded
video URL and completion of the official submission form.
