"""Small in-memory rate limiter. Version 1 runs one API process, so memory is enough."""

import time
from collections.abc import Hashable

_limiters: list["RateLimiter"] = []


class RateLimiter:
    """At most `limit` hits per key in a fixed window of `window` seconds."""

    def __init__(self, limit: int, window: float) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[Hashable, tuple[float, int]] = {}
        _limiters.append(self)

    def allow(self, key: Hashable, cost: int = 1) -> bool:
        now = time.monotonic()
        start, count = self._hits.get(key, (now, 0))
        if now - start >= self.window:
            start, count = now, 0
        if count + cost > self.limit:
            return False
        self._hits[key] = (start, count + cost)
        if len(self._hits) > 10_000:
            self._hits = {k: v for k, v in self._hits.items() if now - v[0] < self.window}
        return True


def reset_all() -> None:
    """Forget every counter (tests)."""
    for limiter in _limiters:
        limiter._hits.clear()
