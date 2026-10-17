import time, subprocess, sys, os, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ENV = dict(os.environ); ENV['PYTHONPATH'] = str(ROOT / 'src')
HW = f"{os.cpu_count()}cpu win"

def bench(args, n=5):
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        subprocess.run([sys.executable, '-m', 'gib', *args], capture_output=True, cwd=str(ROOT), env=ENV)
        ts.append((time.perf_counter() - t) * 1000)
    return round(statistics.median(ts), 1)

if __name__ == '__main__':
    print(f'startup-eval-ms: {bench(["eval", "1"])}')
    print(f'run-hello-ms: {bench(["run", "examples/hello.js"])}')
    print(f'size-src-kb: {sum(f.stat().st_size for f in (ROOT/"src").rglob("*.py"))//1024}')
