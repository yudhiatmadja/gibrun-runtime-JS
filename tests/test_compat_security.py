import subprocess, sys, os, json, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ENV = dict(os.environ); ENV['PYTHONPATH'] = str(ROOT / 'src')

def gib(*a, cwd=None):
    return subprocess.run([sys.executable, '-m', 'gib', *a], capture_output=True, text=True,
                          cwd=str(cwd or ROOT), env=ENV)

def test_node_path_url_util():
    r = gib('eval', "import('node:path').then(async m=>{const u=await import('node:url');console.log(m.join('a','b'));console.log(u.fileURLToPath('file:///C:/x/y'))})")
    assert r.returncode == 0, r.stderr

def test_node_events_buffer_assert():
    r = gib('eval', "import('node:events').then(async m=>{const {EventEmitter}=m;const e=new EventEmitter();e.on('x',v=>console.log('ev:'+v));e.emit('x',1);const b=(await import('node:buffer')).Buffer.from('hi');console.log(b.toString());(await import('node:assert')).strictEqual(1,1);console.log('assert-ok')})")
    assert r.returncode == 0 and 'assert-ok' in r.stdout, r.stderr

def test_esm_relative_and_circular(tmp_path):
    (tmp_path / 'b.mjs').write_text("import './c.mjs'; export const b = 'b';")
    (tmp_path / 'c.mjs').write_text("export const c = 'c';")
    (tmp_path / 'a.mjs').write_text("import {b} from './b.mjs'; import {c} from './c.mjs'; console.log('esm:'+b+c); const m = await import('./b.mjs'); console.log('dyn:'+m.b);")
    r = gib('run', str(tmp_path / 'a.mjs'))
    assert r.returncode == 0 and 'esm:bc' in r.stdout and 'dyn:b' in r.stdout, r.stderr

def test_unresolved_module_error():
    r = gib('eval', "await import('./does-not-exist-xyz.mjs')")
    assert r.returncode != 0

def test_serve_roundtrip():
    r = gib('run', '--allow-net', 'examples/serve.js')
    assert r.returncode == 0 and 'serve-ok:hi gibrun' in r.stdout, r.stderr

def test_net_denied_by_default():
    r = gib('run', 'examples/serve.js')
    assert r.returncode != 0 and 'GIBRUN_ENETDENY' in r.stderr

def test_env_stripped_by_default():
    env = dict(ENV); env['MY_SECRET_TOKEN_XYZ'] = 's3cret'
    r = subprocess.run([sys.executable, '-m', 'gib', 'eval', 'console.log(process.env.MY_SECRET_TOKEN_XYZ ?? "stripped")'],
                       capture_output=True, text=True, cwd=str(ROOT), env=env)
    assert 'stripped' in r.stdout, r.stdout + r.stderr

def test_env_allowed_with_flag():
    env = dict(ENV); env['MY_SECRET_TOKEN_XYZ'] = 's3cret'
    r = subprocess.run([sys.executable, '-m', 'gib', 'eval', '--allow-env', 'console.log(process.env.MY_SECRET_TOKEN_XYZ)'],
                       capture_output=True, text=True, cwd=str(ROOT), env=env)
    assert 's3cret' in r.stdout, r.stdout + r.stderr
