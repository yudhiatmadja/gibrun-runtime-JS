import time, subprocess, sys, os, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ENV = dict(os.environ); ENV['PYTHONPATH'] = str(ROOT / 'src')

def med(args, n=5, node=False):
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        if node:
            subprocess.run(['node', *args], capture_output=True, cwd=str(ROOT))
        else:
            subprocess.run([sys.executable, '-m', 'gib', *args], capture_output=True, cwd=str(ROOT), env=ENV)
        ts.append((time.perf_counter() - t) * 1000)
    return round(statistics.median(ts), 1)

if __name__ == '__main__':
    g_eval = med(['eval', '1'])
    n_eval = med(['-e', '1'], node=True)
    g_hello = med(['run', 'examples/hello.js'])
    n_hello = med(['examples/hello.js'], node=True)
    print(f'gib eval: {g_eval}ms | node -e: {n_eval}ms | overhead ~{round(g_eval-n_eval,1)}ms (python+spawn)')
    print(f'gib run hello: {g_hello}ms | node hello: {n_hello}ms')
    print('env: Windows, CPython 3.10, Node 22.16. Method: median-of-5, cold spawn each.')
