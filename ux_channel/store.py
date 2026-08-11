
"""Keyed bag of Signals with snapshot."""
from __future__ import annotations
from typing import Any, Dict, Optional
from ux_channel.reactive import Signal, signal


class Store:
    def __init__(self, name: str = "store"):
        self.name = name
        self._data: Dict[str, Signal] = {}

    def get(self, key: str, default: Any = None) -> Any:
        s = self._data.get(key)
        if s is None:
            return default
        return s.get()

    def set(self, key: str, value: Any) -> Signal:
        s = self._data.get(key)
        if s is None:
            s = signal(value, name=f"{self.name}.{key}")
            self._data[key] = s
        else:
            s.set(value)
        return s

    def signal(self, key: str, default: Any = None) -> Signal:
        if key not in self._data:
            self._data[key] = signal(default, name=f"{self.name}.{key}")
        return self._data[key]

    def snapshot(self) -> Dict[str, Any]:
        return {k: s.peek() for k, s in self._data.items()}

    def __repr__(self) -> str:
        return f"Store({self.name!r}, keys={list(self._data)})"
