
"""Regions & Outlets — composition that beats React children/slots.

React forces you into one of:
  - prop drilling ``header={...}``
  - render props ``header={() => ...}``
  - compound statics ``Dialog.Title = ...`` (awkward in JS)
  - context + portals for distant injection

Python gives us context managers + a region bag. Result::

    with Shell() as app:
        with Region("sidebar"):
            Nav()
        with Region("main"):
            Dashboard()

    class Shell(View):
        def body(self):
            with HStack() as root:
                Outlet("sidebar").frame(width=64)
                Outlet("main").frame(width="full")
            return root

Outlets pull whatever was filled into the active RegionScope.
Unfilled outlets render their default children (or nothing).
"""
from __future__ import annotations
import contextvars
from typing import Any, Dict, List, Optional
from ux_dom.element import Child, Fragment, flatten_children
from ux_dom.view import View, ViewChild, _resolve
from ux_dom.tw import cn

# Active fills: name → list of view children
_FILLS: contextvars.ContextVar[Optional[Dict[str, List[ViewChild]]]] = contextvars.ContextVar(
    "ux_dom_fills", default=None
)
# Stack of region names being filled (allows nested Region scopes)
_FILL_STACK: contextvars.ContextVar[Optional[list]] = contextvars.ContextVar(
    "ux_dom_fill_stack", default=None
)


def _fills() -> Dict[str, List[ViewChild]]:
    bag = _FILLS.get()
    if bag is None:
        bag = {}
        _FILLS.set(bag)
    return bag


class RegionScope(View):
    """Open a composition scope. Children may use Region/Fill; body may use Outlet.

        with RegionScope() as scope:
            with Region("header"):
                Text("Title")
            # if you also build the layout here:
            with VStack():
                Outlet("header")
                Outlet("main")
    """

    def __init__(self, *children: ViewChild, **props: Any):
        super().__init__(*children, **props)
        self._bag: Dict[str, List[ViewChild]] = {}
        self._token = None
        self._prev = None
        self._layout: List[ViewChild] = []
        self._layout_token = None

    def __enter__(self):
        self._prev = _FILLS.get()
        self._bag = {}
        self._token = _FILLS.set(self._bag)
        # also act as a builder so layout views inside the scope collect
        from ux_dom.layout import _BUILDER
        self._parent_builder = _BUILDER.get()
        self._layout = []
        self._layout_token = _BUILDER.set(self._layout)
        return self

    def __exit__(self, *exc):
        from ux_dom.layout import _BUILDER
        _BUILDER.reset(self._layout_token)
        _FILLS.reset(self._token)
        self.children = flatten_children(list(self.children) + self._layout)
        if self._parent_builder is not None:
            # region scope itself may sit inside a stack
            pass
        return False

    def body(self) -> ViewChild:
        # Resolve outlets against *this* bag even if context was reset
        token = _FILLS.set(self._bag)
        try:
            kids = [_resolve(c) for c in self.children]
            return Fragment(*kids) if kids else Fragment()
        finally:
            _FILLS.reset(token)


class Region(View):
    """Fill a named region. Content is stored, not rendered in place.

        with Region("sidebar"):
            NavItem("Home")
            NavItem("Settings")
    """

    def __init__(self, name: str, *children: ViewChild, **props: Any):
        self.name = name
        from ux_dom.view import _suspend_push
        with _suspend_push():
            super().__init__(*children, **props)
        self._collected: List[ViewChild] = []
        self._token = None
        self._stack_token = None

    def __enter__(self):
        from ux_dom.layout import _BUILDER
        self._collected = []
        self._token = _BUILDER.set(self._collected)
        stack = list(_FILL_STACK.get() or [])
        stack.append(self.name)
        self._stack_token = _FILL_STACK.set(stack)
        return self

    def __exit__(self, *exc):
        from ux_dom.layout import _BUILDER
        _BUILDER.reset(self._token)
        _FILL_STACK.reset(self._stack_token)
        bag = _fills()
        bag.setdefault(self.name, []).extend(self._collected)
        bag[self.name].extend(self.children)
        # Region is a filler, not a visual node — remove from parent builder if auto-pushed
        parent = _BUILDER.get()
        if parent is not None:
            while self in parent:
                parent.remove(self)
        return False

    def body(self) -> ViewChild:
        # If used without `with`, treat children as the fill immediately
        if self.children:
            bag = _fills()
            bag.setdefault(self.name, []).extend(self.children)
        return Fragment()  # invisible


# Alias
Fill = Region


class Outlet(View):
    """Render the contents of a named region (or defaults).

        Outlet("main")
        Outlet("sidebar", Text("No sidebar"))   # default if unfilled
    """

    def __init__(self, name: str, *default: ViewChild, **props: Any):
        # Construct default children without leaking them into the ambient
        # VStack/HStack builder; the Outlet itself must still auto-register.
        from ux_dom.view import _suspend_push
        with _suspend_push():
            defaults = tuple(default)
        super().__init__(*defaults, **props)
        self.name = name

    def body(self) -> ViewChild:
        bag = _FILLS.get() or {}
        filled = bag.get(self.name)
        if filled:
            return Fragment(*[_resolve(c) for c in filled])
        if self.children:
            return Fragment(*[_resolve(c) for c in self.children])
        return Fragment()

    def frame(self, **kwargs):
        # Outlets often need layout constraints; wrap resolved content
        super().frame(**kwargs)
        return self


class Slot(Outlet):
    """Semantic alias for Outlet — reads well in compound components."""
    pass


def region_contents(name: str) -> List[ViewChild]:
    """Inspect fills (useful in tests / tooling)."""
    return list((_FILLS.get() or {}).get(name, []))


# ── Compound helper ──────────────────────────────────────────────────────────

class Compound(View):
    """Base for compound components with declared region names.

        class Dialog(Compound):
            regions = ("title", "body", "actions")

            def body(self):
                with VStack(spacing=12) as root:
                    Outlet("title").font("title")
                    Outlet("body")
                    with HStack(spacing=8):
                        Outlet("actions")
                return root.padding(24).background("surface-raised").corner_radius("xl")

        with Dialog() as dlg:
            with Region("title"):
                Text("Delete file?")
            with Region("body"):
                Text("This cannot be undone.")
            with Region("actions"):
                Button("Cancel")
                Button("Delete")
    """

    regions: tuple = ()

    def __init__(self, *children: ViewChild, **props: Any):
        super().__init__(*children, **props)
        self._bag: Dict[str, List[ViewChild]] = {}
        self._token = None
        self._builder_token = None
        self._layout: List[ViewChild] = []

    def __enter__(self):
        self._prev = _FILLS.get()
        self._bag = {}
        self._token = _FILLS.set(self._bag)
        from ux_dom.layout import _BUILDER
        self._layout = []
        self._builder_token = _BUILDER.set(self._layout)
        return self

    def __exit__(self, *exc):
        from ux_dom.layout import _BUILDER
        _BUILDER.reset(self._builder_token)
        _FILLS.reset(self._token)
        # layout expressions inside `with Compound()` are unusual; fills matter
        return False

    def build(self) -> Child:
        # Ensure outlets see this compound's bag
        token = _FILLS.set(self._bag)
        try:
            return super().build()
        finally:
            _FILLS.reset(token)
