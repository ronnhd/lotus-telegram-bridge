import time
from typing import Optional

class MediaRegistry:
    """In-memory cache mapping file_id -> signed CDN URL.
    
    Lotus Chat does not support the Telegram getFile API (it answers 'File ID invalid').
    The only way to download media sent by users is via the signed link_cdn property
    provided in the inbound webhook update.
    """
    def __init__(self, ttl_seconds: int = 259200):  # ~3 days TTL
        self._cache: dict[str, dict] = {}
        self._ttl = ttl_seconds

    def register(self, file_id: str, url: str) -> None:
        if not file_id or not url:
            return
        self._cache[str(file_id)] = {
            "url": str(url),
            "ts": time.time(),
        }

    def get(self, file_id: str) -> Optional[str]:
        entry = self._cache.get(str(file_id))
        if not entry:
            return None
        # Check expiry
        if time.time() - entry["ts"] > self._ttl:
            return None
        return entry["url"]

registry = MediaRegistry()
