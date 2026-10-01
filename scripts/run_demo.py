"""Run the API and UI together; Ollama must already be running for local inference."""

import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent.parent
if not (root / ".env").exists():
    raise SystemExit("Run uv run python scripts/setup_local.py first.")
children = []
try:
    children.append(
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            cwd=root,
        )
    )
    children.append(
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "ui/app.py",
                "--server.address",
                "127.0.0.1",
                "--server.port",
                "8501",
            ],
            cwd=root,
        )
    )
    print("Relay: http://localhost:8501 | API: http://localhost:8000/docs")
    print("Press Ctrl+C to stop these two processes.")
    while all(child.poll() is None for child in children):
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    for child in children:
        if child.poll() is None:
            child.terminate()
    for child in children:
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
