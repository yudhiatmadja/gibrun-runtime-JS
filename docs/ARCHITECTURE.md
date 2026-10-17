# Gibrun Architecture (v0.1)

Logical subsystems (Python package `src/gib/`):

- `cli.py` — argparse dispatch, exit codes, help/version.
- `engine.py` — `Engine` interface; `NodeEngine` runs real JS via isolated `node` subprocess
  (ESM temp entry, `--input-type=module` for eval, permission env gating, exit-code propagation).
- `module_loader.py` — resolution relative to importer (relative paths, file URLs, package.json
  exports/main/module, node_modules walk); caching verified by engine; clear unresolved errors.
- `event_loop.py` — process-liveness: Node owns microtasks/macrotasks; Python waits, forwards
  timeout (default 30s), propagates async errors via stderr + nonzero exit.
- `typescript.py` — type-stripping transpile (erases interfaces/type aliases/annotations/enums
  enough for common cases); distinct from type checking (`gib check` shells to `tsc --noEmit` if present).
- `permissions.py` — `--allow-read/write/net/env/run` deny-by-default for sensitive caps;
  path canonicalization, symlink resolve, TOCTOU note; enforced pre-exec + `GIBRUN_ALLOW_*` env into engine.
- `web_apis.py` — timers/console/fetch/URL/TextEncoder documented as inherited from Node V8;
  `Gibrun.serve()` shim in `runtime_js/` backed by `node:http`.
- `node_compat.py` — matrix of `node:` builtins delegated to Node (full compat by construction v0.1).
- `packagemgr.py` — npm-registry client (urllib), semver resolution, lockfile `gib.lock.json`,
  safe tarball extraction (path-traversal reject), no lifecycle-script execution by default.
- `commands/*` — run/eval/init/add/remove/install/update/test/fmt/check/build/info/runx.
- `diagnostics.py` — uniform `error: <msg>` + stack passthrough format.

Contracts: CLI → runtime orchestration → Engine.run(file/code). No circular deps; no global mutable state
except parsed args. Engine-specific logic confined to `engine.py` + `runtime_js/`.
