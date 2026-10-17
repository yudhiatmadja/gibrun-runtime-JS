# Gibrun — `gib` JS/TS runtime (v0.1)

Requires Python 3.10+ and Node.js 18+ (engine backend).

```bash
set PYTHONPATH=src
python -m gib --version
python -m gib run examples/hello.js
python -m gib run examples/hello.ts
python -m gib eval "console.log(2+2)"
python -m gib info
gib init; gib add left-pad; gib install; gib test; gib fmt; gib check; gib build
```

Docs: `docs/PROJECT_ASSESSMENT.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`,
`docs/DECISIONS/0001-runtime-foundation.md`. Tests: `python -m pytest tests/ -q`.
License status: MIT draft in LICENSE (copyright holder TBD — authorization needed before publishing).
Security: deny-by-default env/net; no lifecycle scripts executed; tarball path-traversal rejected.
Not production-ready: embedded engine, JSX, full sandbox pending — see ROADMAP.
