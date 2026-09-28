"""Cache simples em memória com expiração (TTL) e limite de entradas."""

import time
from collections import OrderedDict
from collections.abc import Hashable
from typing import Generic, TypeVar

V = TypeVar("V")


class TTLCache(Generic[V]):
    """Guarda até ``max_entries`` valores por ``ttl_seconds`` segundos.

    Por ser um dicionário por processo, cada worker do uvicorn tem o seu próprio
    cache. É o suficiente para este projeto, que roda em um único processo com
    SQLite; com vários workers, o caminho natural seria um Redis.
    """

    def __init__(self, ttl_seconds: float, max_entries: int = 256) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: OrderedDict[Hashable, tuple[float, V]] = OrderedDict()

    def get(self, key: Hashable) -> V | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            del self._entries[key]
            return None
        return value

    def set(self, key: Hashable, value: V) -> None:
        self._entries[key] = (time.monotonic() + self.ttl_seconds, value)
        self._entries.move_to_end(key)
        # Ao estourar o limite, descarta a entrada mais antiga.
        while len(self._entries) > self.max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)
