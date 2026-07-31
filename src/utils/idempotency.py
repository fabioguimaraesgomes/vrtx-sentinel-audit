from __future__ import annotations

import threading
import time
from typing import Any


_LOCK = threading.Lock()
_STORE: dict[str, tuple[float, dict[str, Any]]] = {}


def _full_key(scope: str, key: str) -> str:
    return f"{scope}:{key}"


def get_cached_response(scope: str, key: str, ttl_seconds: int) -> dict[str, Any] | None:
    now = time.time()
    lookup_key = _full_key(scope, key)
    with _LOCK:
        record = _STORE.get(lookup_key)
        if not record:
            return None
        created_at, payload = record
        if now - created_at > ttl_seconds:
            _STORE.pop(lookup_key, None)
            return None
        return payload


def cache_response(scope: str, key: str, payload: dict[str, Any]) -> None:
    lookup_key = _full_key(scope, key)
    with _LOCK:
        _STORE[lookup_key] = (time.time(), payload)
