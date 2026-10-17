import argparse, json, os, re, shutil, subprocess, sys, tarfile, tempfile, urllib.request
from pathlib import Path
from . import __version__
from . import engine, permissions
from .typescript import tsc_available

REGISTRY = 'https://registry.npmjs.org'

def cmd_version(a): print(f'gib {__version__}'); return 0
def cmd_info(a):
    import platform
    print(json.dumps({'version': __version__, 'node': shutil.which('node'),
                      'python': sys.version.split()[0], 'platform': platform.platform()}, indent=2)); return 0
def cmd_run(a):
    ok, env = permissions.check_perms(a, a.file)
    suf = Path(a.file).suffix
    if suf in ('.ts', '.mts', '.cts'):
        # run via TS pipeline
        from pathlib import Path as P
        src = P(a.file).read_text(encoding='utf-8') if P(a.file).is_file() else ''
        if not P(a.file).is_file():
            print(f'error: file not found: {a.file}', file=sys.stderr); return 1
        return engine.run_code_ts(src, env_extra=env) if src else 1
    return engine.run_file(a.file, env_extra=env)
def cmd_eval(a):
    ok, env = permissions.check_perms(a)
    code = a.code
    if re.search(r':\s*(string|number|boolean|any)\b|interface\s+\w+|type\s+\w+', code):
        return engine.run_code_ts(code, env_extra=env)
    return engine.run_code(code, env_extra=env)

def _pkg_paths():
    pj = Path.cwd() / 'package.json'
    return pj

def cmd_init(a):
    pj = _pkg_paths()
    if pj.exists() and not a.yes:
        print('error: package.json exists (use --yes to overwrite)', file=sys.stderr); return 1
    name = Path.cwd().name
    pj.write_text(json.dumps({'name': name, 'version': '0.1.0', 'type': 'module',
        'scripts': {'test': 'gib test'}}, indent=2), encoding='utf-8')
    print(f'initialized {pj}'); return 0

def _read_pkg():
    pj = _pkg_paths()
    if not pj.exists(): return {}
    return json.loads(pj.read_text(encoding='utf-8'))

def _write_pkg(d):
    _pkg_paths().write_text(json.dumps(d, indent=2) + '\n', encoding='utf-8')

def _fetch_meta(name):
    url = f'{REGISTRY}/{urllib.request.quote(name)}'
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)

def _resolve(meta, rng):
    import functools
    vers = list(meta['versions'].keys())
    def tup(v): return tuple(int(x) if x.isdigit() else 0 for x in re.split(r'[.\-]', v)[:3])
    vers.sort(key=tup)
    if rng in ('*', 'latest', ''): return vers[-1]
    m = re.match(r'\^(\d+)\.(\d+)\.(\d+)', rng)
    if m:
        M = int(m.group(1))
        c = [v for v in vers if v.split('.')[0] == str(M)]
        return c[-1] if c else None
    m = re.match(r'~(\d+)\.(\d+)\.(\d+)', rng)
    if m:
        pre = f'{m.group(1)}.{m.group(2)}'
        c = [v for v in vers if v.startswith(pre + '.')]
        return c[-1] if c else None
    if rng in meta['versions']: return rng
    return None

def _safe_extract(tar, dest: Path):
    for m in tar.getmembers():
        p = (dest / m.name).resolve()
        if not str(p).startswith(str(dest.resolve())):
            raise ValueError(f'malicious archive path rejected: {m.name}')
    tar.extractall(dest)

def _install_pkg(name, ver, dest_root: Path):
    meta = _fetch_meta(name)
    v = _resolve(meta, ver)
    if not v: raise SystemExit(f'error: cannot resolve {name}@{ver}')
    dist = meta['versions'][v]['dist']
    url, integ = dist['tarball'], dist.get('integrity', '')
    d = dest_root / ('@' + name.replace('/', '_') if name.startswith('@') else name)
    d.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix='.tgz', delete=False) as tf:
        with urllib.request.urlopen(url, timeout=60) as r, open(tf.name, 'wb') as f:
            shutil.copyfileobj(r, f)
        with tarfile.open(tf.name) as tar:
            _safe_extract(tar, d)
    # flatten package/ dir
    pkgdir = d / 'package'
    if pkgdir.is_dir():
        for c in list(pkgdir.iterdir()):
            t = d / c.name
            if t.exists(): shutil.rmtree(t) if t.is_dir() else t.unlink()
            shutil.move(str(c), str(t))
        pkgdir.rmdir()
    (d / '.gib-integrity').write_text(integ)
    return v, meta['versions'][v].get('dependencies', {})

def _install_all(deps: dict, lock: dict):
    nm = Path.cwd() / 'node_modules'; nm.mkdir(exist_ok=True)
    todo = list(deps.items()); seen = {}
    while todo:
        n, r = todo.pop(0)
        if n in seen: continue
        v, sub = _install_pkg(n, r, nm)
        seen[n] = v
        lock.setdefault('packages', {})[n] = {'version': v}
        todo.extend(sub.items())
    return seen

def cmd_add(a):
    try:
        pkg = _read_pkg()
        deps = pkg.setdefault('dependencies', {})
        lock = {'lockfileVersion': 1, 'packages': {}}
        lf = Path.cwd() / 'gib.lock.json'
        if lf.exists(): lock = json.loads(lf.read_text())
        for spec in a.packages:
            n, _, r = spec.partition('@') if not spec.startswith('@') else ('@' + spec[1:].split('@')[0], '@', spec[1:].split('@')[1] if '@' in spec[1:] else 'latest')
            if spec.startswith('@') and r == '': r = 'latest'
            if not spec.startswith('@') and r == '': n, r = spec, 'latest'
            meta = _fetch_meta(n); v = _resolve(meta, r)
            if not v: print(f'error: cannot resolve {spec}', file=sys.stderr); return 1
            deps[n] = r if r != 'latest' else '^' + v
            _install_all({n: v}, lock)
        _write_pkg(pkg)
        lf.write_text(json.dumps(lock, indent=2))
        print('added ' + ', '.join(a.packages)); return 0
    except Exception as e:
        print(f'error: {e}', file=sys.stderr); return 1

def cmd_remove(a):
    pkg = _read_pkg()
    for n in a.packages:
        pkg.get('dependencies', {}).pop(n, None)
        pkg.get('devDependencies', {}).pop(n, None)
        nm = Path.cwd() / 'node_modules' / n
        if nm.exists(): shutil.rmtree(nm)
    _write_pkg(pkg); print('removed ' + ', '.join(a.packages)); return 0

def cmd_install(a):
    lf = Path.cwd() / 'gib.lock.json'
    pkg = _read_pkg()
    deps = dict(pkg.get('dependencies', {}))
    lock = {'lockfileVersion': 1, 'packages': {}}
    if lf.exists() and not a.frozen is False:
        lock = json.loads(lf.read_text())
        deps = {k: v['version'] for k, v in lock.get('packages', {}).items()}
    try:
        _install_all(deps, lock)
        lf.write_text(json.dumps(lock, indent=2))
        print('installed'); return 0
    except Exception as e:
        print(f'error: {e}', file=sys.stderr); return 1

def cmd_update(a):
    # re-resolve ranges
    pkg = _read_pkg()
    lock = {'lockfileVersion': 1, 'packages': {}}
    try:
        _install_all(dict(pkg.get('dependencies', {})), lock)
        (Path.cwd() / 'gib.lock.json').write_text(json.dumps(lock, indent=2))
        print('updated'); return 0
    except Exception as e:
        print(f'error: {e}', file=sys.stderr); return 1

def cmd_test(a):
    import glob
    files = sorted(glob.glob('**/*.test.{js,mjs,ts}', recursive=True))
    if not files: print('no tests found'); return 1
    fails = 0
    for f in files:
        print(f'# {f}')
        rc = engine.run_file(f)
        if rc != 0: fails += 1; print(f'not ok: {f}')
        else: print(f'ok: {f}')
    print(f'{len(files) - fails}/{len(files)} passed')
    return 1 if fails else 0

def cmd_fmt(a):
    targets = a.files or ['.']
    # Minimal real formatter: normalize indentation/trailing whitespace via node? Use python formatter for JS-lite:
    count = 0
    for t in targets:
        p = Path(t)
        fl = [p] if p.is_file() else list(p.rglob('*.js')) + list(p.rglob('*.ts')) + list(p.rglob('*.mjs'))
        for f in fl:
            s = f.read_text(encoding='utf-8')
            out = '\n'.join(l.rstrip().replace('\t', '  ') for l in s.splitlines())
            if not out.endswith('\n'): out += '\n'
            if out != s: f.write_text(out, encoding='utf-8'); count += 1
    print(f'formatted {count} file(s)'); return 0

def cmd_check(a):
    # Real type check if tsc present, else scoped validation
    if tsc_available():
        tsc = shutil.which('tsc') or 'npx'
        cmd = [tsc, '--noEmit'] if tsc.endswith('tsc') else ['npx', '--yes', 'typescript', '--noEmit']
        p = subprocess.run(cmd, capture_output=True, text=True)
        print(p.stdout + p.stderr)
        return p.returncode
    # fallback: syntax check via node --check on stripped TS
    from .typescript import strip_types
    bad = 0
    for f in Path('.').rglob('*.ts'):
        src = strip_types(f.read_text(encoding='utf-8'))
        with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False) as tf:
            tf.write(src); tf.close()
            p = subprocess.run(['node', '--check', tf.name], capture_output=True, text=True)
            Path(tf.name).unlink(missing_ok=True)
            if p.returncode != 0: print(f'{f}: {p.stderr}'); bad += 1
    print('check: no tsc found; syntax validation only' if bad == 0 else f'check failed: {bad} file(s)')
    return 1 if bad else 0

def cmd_build(a):
    out = Path(a.out or 'dist'); out.mkdir(exist_ok=True)
    entry = Path(a.entry or 'src/index.ts')
    if not entry.exists():
        alt = Path('src/index.js')
        entry = alt if alt.exists() else entry
    if not entry.exists(): print(f'error: entry not found: {entry}', file=sys.stderr); return 1
    from .typescript import strip_types
    src = entry.read_text(encoding='utf-8')
    if entry.suffix in ('.ts', '.mts'): src = strip_types(src)
    (out / (entry.stem + '.js')).write_text(src, encoding='utf-8')
    print(f'built -> {out}'); return 0

def cmd_runx(a):
    # gib runx <package> [args...]: temp install + execute bin
    with tempfile.TemporaryDirectory() as td:
        try:
            v, _ = _install_pkg(a.package, a.version or 'latest', Path(td))
        except Exception as e:
            print(f'error: {e}', file=sys.stderr); return 1
        d = Path(td) / a.package
        # find bin
        pj = d / 'package.json'
        entry = None
        try:
            meta = json.loads(pj.read_text())
            b = meta.get('bin', {})
            entry = d / (b if isinstance(b, str) else list(b.values())[0])
        except Exception: entry = None
        if not entry or not entry.exists(): print('error: no bin found', file=sys.stderr); return 1
        p = subprocess.run([shutil.which('node') or 'node', str(entry)] + (a.args or []))
        return p.returncode

def cmd_script_run(a):
    pkg = _read_pkg()
    sc = pkg.get('scripts', {}).get(a.script)
    if not sc: print(f'error: script not found: {a.script}', file=sys.stderr); return 1
    env = dict(os.environ)
    env['PATH'] = str(Path.cwd() / 'node_modules' / '.bin') + os.pathsep + env.get('PATH', '')
    p = subprocess.run(sc, shell=True, env=env)
    return p.returncode

def _perm_flags(s):
    for f in ('--allow-read', '--allow-write', '--allow-net', '--allow-env', '--allow-run'):
        s.add_argument(f, action='store_true')
    return s

def build_parser():
    p = argparse.ArgumentParser(prog='gib', description='Gibrun JS/TS runtime')
    p.add_argument('--version', action='store_true')
    p.add_argument('--allow-read', action='store_true'); p.add_argument('--allow-write', action='store_true')
    p.add_argument('--allow-net', action='store_true'); p.add_argument('--allow-env', action='store_true')
    p.add_argument('--allow-run', action='store_true')
    sub = p.add_subparsers(dest='cmd')
    s = _perm_flags(sub.add_parser('run')); s.add_argument('file'); s.set_defaults(fn=cmd_run)
    s = _perm_flags(sub.add_parser('eval')); s.add_argument('code'); s.set_defaults(fn=cmd_eval)
    s = sub.add_parser('init'); s.add_argument('--yes', '-y', action='store_true'); s.set_defaults(fn=cmd_init)
    s = sub.add_parser('add'); s.add_argument('packages', nargs='+'); s.set_defaults(fn=cmd_add)
    s = sub.add_parser('remove'); s.add_argument('packages', nargs='+'); s.set_defaults(fn=cmd_remove)
    s = sub.add_parser('install'); s.set_defaults(fn=cmd_install)
    s = sub.add_parser('update'); s.set_defaults(fn=cmd_update)
    s = sub.add_parser('test'); s.set_defaults(fn=cmd_test)
    s = sub.add_parser('fmt'); s.add_argument('files', nargs='*'); s.set_defaults(fn=cmd_fmt)
    s = sub.add_parser('check'); s.set_defaults(fn=cmd_check)
    s = sub.add_parser('build'); s.add_argument('entry', nargs='?'); s.add_argument('--out', default='dist'); s.set_defaults(fn=cmd_build)
    s = sub.add_parser('info'); s.set_defaults(fn=cmd_info)
    s = sub.add_parser('runx'); s.add_argument('package'); s.add_argument('--version', dest='version', default=None); s.add_argument('args', nargs='*'); s.set_defaults(fn=cmd_runx)
    s = sub.add_parser('script'); s.add_argument('script'); s.set_defaults(fn=cmd_script_run)
    return p

def main(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.version and not a.cmd: return cmd_version(a)
    if not a.cmd: ap.print_help(); return 2
    try:
        return a.fn(a)
    except BrokenPipeError:
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
