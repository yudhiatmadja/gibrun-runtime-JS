# Compatibility matrix (verified on Windows, Node 22 backend)

| Module | Status | Note |
|---|---|---|
| ESM relative/nested/dynamic import, caching, circular | ✅ tested | `test_esm_relative_and_circular` |
| node:path, node:url, node:util, node:buffer, node:events, node:assert | ✅ tested | delegated to Node 22 |
| node:fs, node:http | ✅ basic | serve roundtrip tested; full API = Node parity by construction |
| CommonJS require from ESM | ⚠️ partial | needs createRequire test; planned |
| package.json exports | ⚠️ partial | basic main/module resolution only |
| JSX/TSX | ❌ | rejected with clear error; planned |
