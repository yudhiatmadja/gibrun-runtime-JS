import os, shutil, subprocess, sys, tempfile
from pathlib import Path
from .typescript import strip_types

NODE = shutil.which('node') or 'node'
TIMEOUT = 30
PRELOAD = Path(__file__).parent / 'runtime_js' / 'preload.mjs'

class EngineError(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg); self.code = code

def _run_node_import(entry: Path, cwd: Path, env_extra: dict, timeout=TIMEOUT) -> int:
    env = dict(os.environ); env.update(env_extra)
    if env.get('GIBRUN_ALLOW_ENV') != '1':
        for k in list(env):
            if any(s in k for s in ('KEY', 'SECRET', 'TOKEN', 'PASSWORD')) and k not in (
                    'GIBRUN_ALLOW_ENV', 'GIBRUN_ALLOW_NET'):
                if k not in ('PATH', 'SystemRoot', 'SYSTEMROOT', 'TEMP', 'TMP', 'HOME', 'NODE_PATH',
                             'PATHEXT', 'WINDIR', 'COMSPEC'):
                    del env[k]
    try:
        p = subprocess.run([NODE, '--import', PRELOAD.resolve().as_uri(), str(entry)],
                           cwd=str(cwd), env=env,
                           stdout=sys.stdout, stderr=sys.stderr, timeout=timeout)
        return p.returncode
    except subprocess.TimeoutExpired:
        print('error: execution timed out', file=sys.stderr); return 124
    except FileNotFoundError:
        print('error: node executable not found; install Node.js >=18', file=sys.stderr); return 127

def _run_node(entry: Path, cwd: Path, env_extra: dict, timeout=TIMEOUT) -> int:
    env = dict(os.environ); env.update(env_extra)
    # Strip secret-ish vars unless explicitly allowed.
    if env.get('GIBRUN_ALLOW_ENV') != '1':
        for k in list(env):
            if k.startswith('__STRIP__'):
                del env[k]
            elif k not in ('PATH', 'SystemRoot', 'SYSTEMROOT', 'TEMP', 'TMP', 'HOME', 'NODE_PATH',
                           'GIBRUN_ALLOW_ENV', 'GIBRUN_ALLOW_NET', 'PATHEXT', 'WINDIR', 'COMSPEC'):
                if any(s in k for s in ('KEY', 'SECRET', 'TOKEN', 'PASSWORD')):
                    del env[k]
    try:
        p = subprocess.run([NODE, str(entry)], cwd=str(cwd), env=env,
                           stdout=sys.stdout, stderr=sys.stderr, timeout=timeout)
        return p.returncode
    except subprocess.TimeoutExpired:
        print('error: execution timed out', file=sys.stderr); return 124
    except FileNotFoundError:
        print('error: node executable not found; install Node.js >=18', file=sys.stderr); return 127

def _with_preload(source: str) -> str:
    uri = PRELOAD.resolve().as_uri()
    return f'import {uri!r};\n' + source

def _stage(source: str, is_ts: bool, hint_dir: Path) -> Path:
    if is_ts:
        source = strip_types(source)
    source = _with_preload(source)
    hint_dir.mkdir(parents=True, exist_ok=True)
    f = tempfile.NamedTemporaryFile('w', suffix='.mjs', dir=str(hint_dir), delete=False, encoding='utf-8')
    f.write(source); f.close()
    return Path(f.name)

def _stage_inline(source: str, cwd: Path) -> Path:
    cache = cwd / '.gib' / 'cache'
    return _stage(source, False, cache)

def _run_wrapped(src: str, cwd: Path, env_extra, timeout=TIMEOUT) -> int:
    staged = _stage(src, False, cwd / '.gib' / 'cache')
    try:
        return _run_node(staged, cwd, env_extra or {}, timeout)
    finally:
        staged.unlink(missing_ok=True)

def run_file(path: str, timeout=TIMEOUT, env_extra=None) -> int:
    p = Path(path)
    if not p.is_file():
        print(f'error: file not found: {path}', file=sys.stderr); return 1
    if p.suffix == '.tsx':
        print('error: .tsx requires JSX pipeline (not yet implemented)', file=sys.stderr); return 1
    is_ts = p.suffix in ('.ts', '.mts', '.cts')
    src = p.read_text(encoding='utf-8')
    if is_ts:
        import uuid
        staged = p.parent / f'.gib-run-{p.stem}-{uuid.uuid4().hex[:8]}.mjs'
        try:
            staged.write_text(strip_types(src), encoding='utf-8')
            return _run_node_import(staged, p.parent.resolve(), env_extra or {}, timeout)
        finally:
            staged.unlink(missing_ok=True)
    return _run_node_import(p.resolve(), p.parent.resolve(), env_extra or {}, timeout)

def run_code(code: str, timeout=TIMEOUT, env_extra=None) -> int:
    return _run_wrapped(code, Path.cwd(), env_extra, timeout)

def run_code_ts(code: str, timeout=TIMEOUT, env_extra=None) -> int:
    staged = _stage(code, True, Path.cwd() / '.gib' / 'cache')
    try:
        return _run_node(staged, Path.cwd(), env_extra or {}, timeout)
    finally:
        staged.unlink(missing_ok=True)
