from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import Settings

password_hasher = PasswordHash.recommended()


def issue_token(settings: Settings) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": settings.demo_username,
            "iat": now,
            "exp": now + timedelta(minutes=30),
            "iss": "relay",
            "aud": "relay-api",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def decode_token(token: str, settings: Settings) -> str:
    payload = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=["HS256"],
        issuer="relay",
        audience="relay-api",
        options={"require": ["exp", "sub", "iat"]},
    )
    subject = payload["sub"]
    if not isinstance(subject, str) or subject != settings.demo_username:
        raise jwt.InvalidTokenError("Unknown user")
    return subject
