"""Simple in-memory cache untuk master data yang jarang berubah."""
import time

_cache: dict = {}
_TTL = 300  # 5 menit


def get(key: str):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < _TTL:
        return entry["data"]
    return None


def set(key: str, data):
    _cache[key] = {"data": data, "ts": time.time()}


def invalidate(key: str):
    _cache.pop(key, None)


def invalidate_all():
    _cache.clear()
