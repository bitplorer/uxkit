# Enterprise checklist

| Capability | Status |
| --- | --- |
| XSS-safe render + URL allowlist | yes |
| CSP + security headers | yes |
| CSRF double-submit | yes |
| POST body limits | yes |
| Path-traversal-safe static | yes |
| Strict security mode | yes |
| Declarative validation | yes |
| Theme tokens | yes |
| a11y defaults + skip link | yes |
| shadcn-style local components CLI | yes |
| Python-native View system (State, context managers) | yes |
| Regions / Outlets / Compound composition | yes |
| Declarative `@action` + ActionForm / dispatch | yes |
| Devtools a11y audit + tree inspect | yes |
| Typed package (`py.typed`) | yes |

## Automation defaults (opt-out, not opt-in)

Ceremony that is not feature work stays automatic:

- CSRF cookie + form field injection
- CSP and hardened response headers
- Skip-link and toast host
- Client runtime for `data-action` / `data-on-*`
- Action registry wiring on the App shell

Disable only when deliberately extending the contract or making a breaking change.

## Production

1. `UXKIT_SECRET` for signed CSRF
2. `UXKIT_SECURE_COOKIES=1` behind HTTPS
3. `UXKIT_DEBUG=0` in production
4. Prefer `strict_security=True` after audit
5. Own critical components via `uxkit add` (you control the source)
6. Treat `ux-dom` / `ux-channel` as versioned cores; do not fork their Element/render/signal paths inside app code

## Composition guidance

| Need | Use |
| --- | --- |
| New declarative screen / feature | `View` + `State` + `with VStack` |
| Distant injection (shell, dialog slots) | `Compound` + `Region` / `Outlet` |
| Server/client handler | `@action` + `.action(…)` or `ActionForm` |
| Polished design-system control | uxkit Component (`Button`, `Field`, …) |
| One-off Element tree | `div(…, class_=cn(…))` |
