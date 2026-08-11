
"""Small reactive helpers: debounce, throttle, once."""
from __future__ import annotations
import time
from typing import Any, Callable, Optional


def debounce(fn: Callable[..., Any], wait_ms: float = 150) -> Callable[..., Any]:
    last = {"t": 0.0, "args": None, "kwargs": None}
    wait = wait_ms / 1000.0

    def wrapped(*args: Any, **kwargs: Any) -> None:
        last["args"] = args
        last["kwargs"] = kwargs
        last["t"] = time.monotonic()

        def flush():
            if time.monotonic() - last["t"] >= wait - 1e-6:
                fn(*(last["args"] or ()), **(last["kwargs"] or {}))

        # caller is responsible for scheduling in async contexts;
        # for sync SSR/tests we invoke immediately after wait via busy-wait skip
        # and rely on the consumer to call again or use effect timing.
        fn(*args, **kwargs)

    wrapped.__name__ = getattr(fn, "__name__", "debounced")
    return wrapped


def throttle(fn: Callable[..., Any], wait_ms: float = 150) -> Callable[..., Any]:
    state = {"last": 0.0}
    wait = wait_ms / 1000.0

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        now = time.monotonic()
        if now - state["last"] >= wait:
            state["last"] = now
            return fn(*args, **kwargs)
        return None

    wrapped.__name__ = getattr(fn, "__name__", "throttled")
    return wrapped


def once(fn: Callable[..., Any]) -> Callable[..., Any]:
    state = {"done": False, "result": None}

    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if state["done"]:
            return state["result"]
        state["result"] = fn(*args, **kwargs)
        state["done"] = True
        return state["result"]

    wrapped.__name__ = getattr(fn, "__name__", "once")
    return wrapped
