from __future__ import annotations

import hashlib
import threading
import time


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = float(refill_rate)
        self.last_refill = time.monotonic()

    def allow(self, amount: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.last_refill = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


_LOCK = threading.Lock()
_BUCKETS: dict[str, TokenBucket] = {}


def build_rate_limit_key(auth_header: str | None, fallback: str = "anonymous") -> str:
    raw = auth_header or fallback
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def allow_request(key: str, requests_per_minute: int) -> bool:
    rpm = max(1, requests_per_minute)
    with _LOCK:
        bucket = _BUCKETS.get(key)
        if bucket is None:
            bucket = TokenBucket(capacity=rpm, refill_rate=rpm / 60.0)
            _BUCKETS[key] = bucket
        return bucket.allow(1.0)
