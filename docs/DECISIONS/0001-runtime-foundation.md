# ADR 0001: Runtime Foundation (v0.1)

Date: 2026-10-17. Status: accepted.

Options evaluated: (A) V8 via deno_core/Rust — best long-term, but multi-GB build, long compile,
toolchain risk on Windows. (B) JavaScriptCore — poor Windows support. (C) QuickJS/rquickjs —
easy embed, but lags on modern ECMAScript/Node compat, maintenance burden.

Decision: Python `gib` CLI + `NodeEngine` subprocess backend (Node 22 V8) behind `Engine` interface.
ECMAScript/async/modules/typed-arrays/fetch come from real V8 — no mock. Startup cost = one node
spawn (~50-100ms); acceptable for v0.1, measured in benchmarks/.

Trade-offs: requires Node at runtime; not an independent JIT; sandbox = OS process + permission flags,
not a secure VM sandbox (documented). Migration path: implement `EmbeddedEngine` (deno_core/Boa)
satisfying same `run_file/run_code` contract; no CLI changes needed.

License: Python stdlib + MIT-licensed Gibrun code; Node dependency is external prerequisite, not bundled.
