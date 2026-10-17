# Security model (v0.1, honest scope)

- Flags: `--allow-net` (default deny: fetch/serve throw GIBRUN_ENETDENY), `--allow-env`
  (default strips *KEY/*SECRET/*TOKEN/*PASSWORD from engine env), `--allow-read/write/run`
  (parsed, enforced for fs ops in future embedded engine; currently documented).
- Tarball extraction rejects `..`/absolute paths (tested). No lifecycle scripts executed (by design).
- NOT claimed: VM-level sandbox, symlink-TOCTOU-proof fs jail. Engine = OS process isolation.
  Do not run untrusted code with `--allow-run --allow-net` combined.
