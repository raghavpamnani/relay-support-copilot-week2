import asyncio
import time
from collections import defaultdict, deque
from datetime import UTC, datetime

from fastapi import HTTPException


class UsageControl:
    """Single-process demo limits. Share this state in Redis before scaling workers."""

    def __init__(self, per_minute: int, per_day: int) -> None:
        self.per_minute = per_minute
        self.per_day = per_day
        self.windows: dict[str, deque[float]] = defaultdict(deque)
        self.daily: dict[str, int] = defaultdict(int)
        self.day = datetime.now(UTC).date()
        self.lock = asyncio.Lock()

    async def consume(self, identity: str) -> None:
        async with self.lock:
            day = datetime.now(UTC).date()
            if day != self.day:
                self.daily.clear()
                self.day = day
            now = time.monotonic()
            window = self.windows[identity]
            while window and now - window[0] >= 60:
                window.popleft()
            if len(window) >= self.per_minute or self.daily[identity] >= self.per_day:
                raise HTTPException(
                    429, "Usage limit reached. Try again later.", headers={"Retry-After": "60"}
                )
            window.append(now)
            self.daily[identity] += 1
