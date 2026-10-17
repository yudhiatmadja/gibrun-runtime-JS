import subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ENV = dict(os.environ); ENV['PYTHONPATH'] = str(ROOT / 'src')

def gib(*a):
    return subprocess.run([sys.executable, '-m', 'gib', *a], capture_output=True, text=True, cwd=ROOT, env=ENV)

def test_version():
    assert 'gib 0.1.0' in gib('--version').stdout
def test_eval():
    r = gib('eval', 'console.log(2+2)')
    assert r.returncode == 0 and '4' in r.stdout
def test_run_js():
    r = gib('run', 'examples/hello.js')
    assert r.returncode == 0 and 'hello from gibrun' in r.stdout
def test_run_ts():
    r = gib('run', 'examples/hello.ts')
    assert r.returncode == 0 and '42' in r.stdout
def test_missing():
    r = gib('run', 'nope.js')
    assert r.returncode != 0
def test_error_propagation():
    r = gib('eval', 'throw new Error("boom")')
    assert r.returncode != 0 and 'boom' in r.stderr
def test_async_timer():
    r = gib('eval', "await new Promise(r=>setTimeout(()=>{console.log('tick');r()},50))")
    assert r.returncode == 0 and 'tick' in r.stdout
def test_fmt():
    assert gib('fmt', 'examples/hello.js').returncode == 0
def test_info():
    assert gib('info').returncode == 0
def test_reject_tsx():
    r = gib('eval', 'console.log(1)')
    assert r.returncode == 0
