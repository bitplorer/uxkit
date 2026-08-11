
"""Two-way Binding over a Signal."""
from __future__ import annotations
from typing import Any, Callable, Generic, Optional, TypeVar
from ux_channel.reactive import Signal

T = TypeVar("T")


def bind(sig: Signal[T]) -> "Binding[T]":
    return Binding(sig)


class Binding(Generic[T]):
    """Read/write handle that forwards to an underlying Signal."""

    __slots__ = ("_sig",)

    def __init__(self, sig: Signal[T]):
        self._sig = sig

    def get(self) -> T:
        return self._sig.get()

    def set(self, value: T) -> None:
        self._sig.set(value)

    def update(self, fn: Callable[[T], T]) -> None:
        self._sig.update(fn)

    @property
    def signal(self) -> Signal[T]:
        return self._sig

    def __repr__(self) -> str:
        return f"Binding({self._sig!r})"
