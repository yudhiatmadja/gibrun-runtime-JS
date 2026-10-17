import os, shutil, subprocess, sys, tempfile
from pathlib import Path
from .typescript import strip_types

NODE = shutil.which('node') or 'node'
TIMEOUT = 30

class EngineError(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg); self.code = code

def _run_node(entry: Path, cwd: Path, env_extra: dict, timeout=TIMEOUT) -> int:
    env = dict(os.environ); env.update(env_extra)
    try:
        p = subprocess.run([NODE, str(entry)], cwd=str(cwd), env=env,
                           stdout=sys.stdout, stderr=sys.stderr, timeout=timeout)
        return p.returncode
    except subprocess.TimeoutExpired:
        print('error: execution timed out', file=sys.stderr); return 124
    except FileNotFoundError:
        print('error: node executable not found; install Node.js >=18', file=sys.stderr); return 127

def _stage(source: str, suffix: str, is_ts: bool) -> Path:
    if is_ts:
        source = strip_types(source)
        suffix = '.mjs'
    f = tempfile.NamedTemporaryFile('w', suffix=suffix, delete=False, encoding='utf-8')
    f.write(source); f.close()
    return Path(f.name)

def run_file(path: str, timeout=TIMEOUT, env_extra=None) -> int:
    p = Path(path)
    if not p.is_file():
        print(f'error: file not found: {path}', file=sys.stderr); return 1
    src = p.read_text(encoding='utf-8')
    is_ts = p.suffix in ('.ts', '.tsx', '.mts', '.cts')
    if p.suffix == '.tsx':
        print('error: .tsx requires JSX pipeline (not yet implemented)', file=sys.stderr); return 1
    if is_ts:
        staged = _stage(src, '.mjs', True)
        try:
            return _run_node(staged, p.parent.resolve(), env_extra or {})
        finally:
            staged.unlink(missing_ok=True)
    return _run_node(p.resolve(), p.parent.resolve(), env_extra or {})

def run_code(code: str, timeout=TIMEOUT, env_extra=None) -> int:
    staged = _stage(code, '.mjs', code.lstrip().startswith('// @ts'))
    # Heuristic: try type-strip if TS syntax detected and plain run fails? Keep simple: strip on demand.
    try:
        return _run_node(staged, Path.cwd(), env_extra or {})
    finally:
        staged.unlink(missing_ok=True)

def run_code_ts(code: str, timeout=TIMEOUT, env_extra=None) -> int:
    staged = _stage(code, '.mjs', True)
    try:
        return _run_node(staged, Path.cwd(), env_extra or {})
    finally:
        staged.unlink(missing_ok=True)
