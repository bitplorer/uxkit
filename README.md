# uxkit 2.0

**Enterprise Python UX library** — Tailwind UI polish, shadcn-style local components, Python-native Views (better ergonomics than SwiftUI), Regions & Actions, hardened by default.

Built on **ux-dom** (document + View system) and **ux-channel** (fine-grained reactivity).

## Install

```bash
pip install -e ".[dev]"
```

```bash
pytest -q
python demo/app.py   # gallery on :8080
```

## Quick start

```python
from uxkit import App, Button, Card, Heading, Text

app = App(title="Hello", csrf=True, enable_csp=True)

@app.page("/")
def home():
    return Card(
        Heading("Ship faster"),
        Text("Pure Python UI. Secure by default.", muted=True),
        Button("Docs", href="/docs", right_icon="arrow-right"),
    )

app.run()
```

## Python-native Views

Descriptors, context managers, and contextvars — not a SwiftUI port.

```python
from ux_dom import View, State, VStack, HStack, Text, Button

class Counter(View):
    count = State(0)

    def body(self):
        with VStack(spacing=12) as root:
            Text(f"{self.count}").font("title")
            with HStack(spacing=8):
                Button("-").on_tap("dec")
                Button("+").on_tap("inc")
            for i in range(self.count):          # plain Python
                Text(f"item {i}").font("caption")
        return root.padding(24).corner_radius("xl")

print(Counter().render_html())
```

| Concern | SwiftUI | ux-dom |
| --- | --- | --- |
| Hierarchy | `@ViewBuilder` macro | `with VStack():` |
| State | `@State` property wrapper | `State` descriptor |
| Environment | `@Environment` | `contextvars` + `Environment` |
| Lists | `ForEach` only | `ForEach` **or** plain `for` |
| Functions as views | limited | `@view` decorator |

## Regions & Actions

```python
from ux_dom import Compound, Region, Outlet, VStack, HStack, Text, Button, action, ActionResult

class Shell(Compound):
    def body(self):
        with HStack() as root:
            Outlet("sidebar").frame(width=64)
            Outlet("main").frame(width="full")
        return root

@action
def save_profile(name: str, email: str):
    return ActionResult(ok=True, flash="Saved", redirect="/profile")

with Shell() as app:
    with Region("sidebar"):
        Text("Nav")
    with Region("main"):
        Button("Save").action(save_profile)
```

## shadcn-style CLI

```bash
uxkit init
uxkit add button card field
uxkit list
uxkit doctor
```

Components are **copied into your project** — you own the source. Registry: `uxkit/registry/ui/`.

## Security defaults (opt-out)

- HTML-escaped text, URL allowlist, event-handler stripping
- CSP + hardened headers
- CSRF double-submit (signed when `UXKIT_SECRET` is set)
- POST body limits, path-traversal-safe static
- `strict_security=True` raises instead of soft-fallback

## Architecture

| Layer | Package | Role |
| --- | --- | --- |
| Reactivity | `ux_channel` | Signals, Computed, Effects, Binding, Channel, Store |
| Document | `ux_dom` | Element tree, secure render, Tailwind, View / Regions / Actions |
| Design system | `uxkit` | Theme, components, App shell, validation, CSRF/CSP, CLI |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/API.md](docs/API.md) · [docs/ENTERPRISE.md](docs/ENTERPRISE.md) · [docs/PYTHON_VIEW.md](docs/PYTHON_VIEW.md) · [docs/REGIONS_ACTIONS.md](docs/REGIONS_ACTIONS.md)

## License

MIT
