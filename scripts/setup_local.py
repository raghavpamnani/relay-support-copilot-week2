"""Generate local credentials without printing or committing secrets."""

import getpass
import os
import secrets
from pathlib import Path

from pwdlib import PasswordHash

path = Path(".env")
if path.exists():
    raise SystemExit(".env already exists; preserved. Edit it manually if needed.")
password = getpass.getpass("Choose a demo password (at least 12 characters): ")
if len(password) < 12:
    raise SystemExit("Use at least 12 characters.")
content = (
    f"JWT_SECRET={secrets.token_urlsafe(48)}\nDEMO_USERNAME=reviewer\n"
    f"DEMO_PASSWORD_HASH='{PasswordHash.recommended().hash(password)}'\n"
    "OLLAMA_URL=http://127.0.0.1:11434\nOLLAMA_MODEL=qwen3:1.7b\n"
    "ALLOW_CLOUD_FALLBACK=false\n"
)
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as stream:
    stream.write(content)
print("Created private .env. Sign in as reviewer with your chosen password.")
