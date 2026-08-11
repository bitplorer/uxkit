
"""Typed pub/sub channels for domain events."""
from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional

Handler = Callable[[Any], Any]
_REGISTRY: Dict[str, "Channel"] = {}


@dataclass
class Subscription:
    channel: "Channel"
    topic: str
    handler: Handler
    once: bool = False

    def off(self) -> None:
        self.channel.unsubscribe(self)

    def __enter__(self) -> "Subscription":
        return self

    def __exit__(self, *args: Any) -> None:
        self.off()


@dataclass
class Channel:
    name: str
    strict: bool = True
    history_limit: int = 0
    _subs: Dict[str, List[Subscription]] = field(default_factory=lambda: defaultdict(list), repr=False)
    _history: Dict[str, Deque] = field(default_factory=dict, repr=False)

    def subscribe(self, topic: str, handler: Handler) -> Subscription:
        sub = Subscription(self, topic, handler)
        self._subs[topic].append(sub)
        return sub

    def once(self, topic: str, handler: Handler) -> Subscription:
        sub = Subscription(self, topic, handler, once=True)
        self._subs[topic].append(sub)
        return sub

    def unsubscribe(self, sub: Subscription) -> None:
        lst = self._subs.get(sub.topic, [])
        if sub in lst:
            lst.remove(sub)

    def publish(self, topic: str, payload: Any = None) -> int:
        if self.history_limit > 0:
            hist = self._history.setdefault(topic, deque(maxlen=self.history_limit))
            hist.append(payload)
        subs = list(self._subs.get(topic, []))
        delivered = 0
        for sub in subs:
            try:
                sub.handler(payload)
                delivered += 1
            except Exception:
                if self.strict:
                    raise
            if sub.once:
                self.unsubscribe(sub)
        return delivered

    def history(self, topic: str) -> List[Any]:
        return list(self._history.get(topic, ()))

    def clear(self, topic: Optional[str] = None) -> None:
        if topic is None:
            self._subs.clear()
            self._history.clear()
        else:
            self._subs.pop(topic, None)
            self._history.pop(topic, None)

    def topics(self) -> List[str]:
        return sorted(self._subs.keys())


def channel(name: str = "default", **kwargs: Any) -> Channel:
    if name not in _REGISTRY:
        _REGISTRY[name] = Channel(name, **kwargs)
    return _REGISTRY[name]
