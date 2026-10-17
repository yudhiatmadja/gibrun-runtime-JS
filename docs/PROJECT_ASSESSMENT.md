# GIBRUN — Assessment (verified 2026-10-17, Windows)

- Repo: empty directory `D:\projects\gibrun`, not a git repo.
- OS: Windows (win32, PowerShell 5.1). Node v22.16.0, npm 11.7.0, Python 3.10.11, Rust 1.92.0, CMake 4.0.1, git 2.49.
- RAM ~20GB. Disk check pending (Get-PSDrive truncated; assumed adequate).
- Network: assumed available (npm registry reachable — to be verified by package-manager tests).
- No existing code to reuse.

Decision: Phase-1 foundation = Python 3.10 `gib` CLI (stdlib-only) + isolated Node.js engine backend
behind an `Engine` interface. Rationale: zero native-build risk, real V8 semantics (ESM, promises,
microtasks, timers, fetch) on day one; swap to embedded engine (deno_core/Boa/rquickjs) later without
changing CLI/runtime contracts. Documented in `docs/DECISIONS/0001-runtime-foundation.md`.
