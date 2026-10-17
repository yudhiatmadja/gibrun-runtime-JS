import subprocess, sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ENV = dict(os.environ); ENV['PYTHONPATH'] = str(ROOT / 'src')

def gib(*a, cwd=None):
    return subprocess.run([sys.executable, '-m', 'gib', *a], capture_output=True, text=True,
                          cwd=str(cwd or ROOT), env=ENV)

def test_cjs_require_interop(tmp_path):
    (tmp_path / 'lib.cjs').write_text("module.exports = { add: (a,b) => a + b };")
    (tmp_path / 'main.mjs').write_text(
        "import { createRequire } from 'node:module';\n"
        "const req = createRequire(import.meta.url);\n"
        "const lib = req('./lib.cjs');\n"
        "console.log('cjs:' + lib.add(20, 22));")
    r = gib('run', str(tmp_path / 'main.mjs'))
    assert r.returncode == 0 and 'cjs:42' in r.stdout, r.stderr

def test_exports_map_resolution(tmp_path):
    pkg = tmp_path / 'node_modules' / 'mypkg'
    pkg.mkdir(parents=True)
    (pkg / 'package.json').write_text('{"name":"mypkg","version":"1.0.0","type":"module",'
        '"exports":{".":"./entry.js","./feat":"./feat.js"}}')
    (pkg / 'entry.js').write_text("export const v = 'entry-ok';")
    (pkg / 'feat.js').write_text("export const v = 'feat-ok';")
    (tmp_path / 'main.mjs').write_text(
        "import { v as a } from 'mypkg';\nimport { v as b } from 'mypkg/feat';\n"
        "console.log(a + '+' + b);")
    r = gib('run', str(tmp_path / 'main.mjs'))
    assert r.returncode == 0 and 'entry-ok+feat-ok' in r.stdout, r.stderr

def test_ts_relative_import(tmp_path):
    (tmp_path / 'util.ts').write_text("export const n: number = 6 * 7;")
    (tmp_path / 'main.ts').write_text("import { n } from './util.ts';\nconsole.log('ts-rel:' + n);")
    r = gib('run', str(tmp_path / 'main.ts'))
    assert r.returncode == 0 and 'ts-rel:42' in r.stdout, r.stderr
