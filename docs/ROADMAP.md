# Gibrun Roadmap

- [x] v0.1 vertical slice: `gib --version/--help/run/eval/info`, Node-backed engine, ESM, timers/promises.
- [x] TS type-stripping run, `fmt` (real formatter), `check` (tsc if present else scoped validation).
- [x] `test` runner (discovers `*.test.{js,ts}`), `init/add/remove/install/update`, lockfile, `runx`, `build`, package scripts.
- [ ] Harden permissions (network interception tests), JSX pipeline, `node:` compat matrix expansion.
- [ ] Embedded engine experiment (deno_core or rquickjs) behind same `Engine` interface.
- [ ] CI, benchmarks vs Node/Deno/Bun, SBOM, signed releases (needs authorization).

See CHANGELOG.md for verified status. Unverified = planned/blocked, never claimed complete.
