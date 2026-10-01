"""Conservative claim filter; a backstop, not a prompt-injection security guarantee."""

import re

# We have no tools that perform these actions or establish live investigation status.
UNSUPPORTED_ACTION = re.compile(
    r"\b(?:we|i|our team)\s+(?:have\s+|has\s+|already\s+)?"
    r"(?:refunded|approved|processed|issued|completed|resolved|fixed|marked)\b"
    r"|\b(?:we|i|our team)\s+(?:are|am|is)\s+(?:\w+\s+){0,2}"
    r"(?:investigating|working|processing)\b"
    r"|\brefund\b.{0,35}\b(?:completed|approved|issued|processed)\b"
    r"|\b(?:we|i)\s+will\b.{0,35}\b(?:refund|compensat\w*)\b",
    re.IGNORECASE,
)


def has_unsupported_action(reply: str) -> bool:
    return bool(UNSUPPORTED_ACTION.search(reply))
