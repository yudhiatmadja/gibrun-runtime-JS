import tarfile, io
from pathlib import Path

def test_safe_extract_rejects_traversal(tmp_path):
    from gib.cli import _safe_extract
    dest = tmp_path / 'pkg'; dest.mkdir()
    tf_path = tmp_path / 'evil.tgz'
    with tarfile.open(tf_path, 'w:gz') as tar:
        ti = tarfile.TarInfo('package/index.js'); data = b'ok'
        ti.size = len(data); tar.addfile(ti, io.BytesIO(data))
        ti2 = tarfile.TarInfo('../../evil.js'); ti2.size = 3
        tar.addfile(ti2, io.BytesIO(b'bad'))
    with tarfile.open(tf_path) as tar:
        try:
            _safe_extract(tar, dest)
            assert False, 'should have rejected'
        except ValueError as e:
            assert 'malicious' in str(e)
    assert not (tmp_path / 'evil.js').exists()

def test_init_add_remove_cycle(tmp_path, monkeypatch):
    import subprocess, sys, os, json
    monkeypatch.chdir(tmp_path)
    env = dict(os.environ); env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1] / 'src')
    def gib(*a):
        return subprocess.run([sys.executable, '-m', 'gib', *a], capture_output=True, text=True, cwd=str(tmp_path), env=env)
    assert gib('init', '--yes').returncode == 0
    assert (tmp_path / 'package.json').exists()
