import time
from typing import Any, Dict, Optional, Tuple

class CacheEntry:
    def __init__(self, outputs: Dict[int, Any], timestamp: float):
        self.outputs = outputs
        self.timestamp = timestamp

class NodeCache:
    """
    Simple in-memory cache for node outputs.
    Keys are (node_id, input_hash).
    """
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._access_history = []  # For LRU eviction

    def get(self, key: str) -> Optional[Dict[int, Any]]:
        if key in self._cache:
            # Move to end of history (most recently used)
            if key in self._access_history:
                self._access_history.remove(key)
            self._access_history.append(key)
            return self._cache[key].outputs
        return None

    def set(self, key: str, outputs: Dict[int, Any]):
        if key in self._cache:
            self._access_history.remove(key)
        
        self._cache[key] = CacheEntry(outputs, time.time())
        self._access_history.append(key)

        # Evict if too big
        if len(self._cache) > self._max_size:
            oldest_key = self._access_history.pop(0)
            del self._cache[oldest_key]

    def clear(self):
        self._cache.clear()
        self._access_history.clear()
