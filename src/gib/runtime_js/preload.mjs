// Gibrun runtime preload — injected before every user entry. Real socket I/O via node:http.
import http from 'node:http';

const allowNet = (process.env.GIBRUN_ALLOW_NET ?? '1') !== '0';

function denyNet(what) {
  const e = new Error(`network denied: ${what} (use --allow-net)`);
  e.code = 'GIBRUN_ENETDENY';
  throw e;
}

if (!allowNet) {
  const origFetch = globalThis.fetch;
  globalThis.fetch = (...a) => Promise.reject(denyNet('fetch'));
}

globalThis.Gibrun = {
  version: '0.1.0',
  serve(handler, opts = {}) {
    if (!allowNet) denyNet('serve');
    const port = opts.port ?? 0;
    const server = http.createServer(async (req, res) => {
      try {
        const url = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`);
        let body = '';
        for await (const c of req) body += c;
        const result = await handler({ method: req.method, url: url.pathname + url.search, headers: req.headers, body });
        if (typeof result === 'string') { res.writeHead(200, { 'content-type': 'text/plain' }); res.end(result); }
        else if (result && typeof result === 'object') {
          res.writeHead(result.status ?? 200, result.headers ?? { 'content-type': 'text/plain' });
          res.end(result.body ?? '');
        } else { res.writeHead(200); res.end(String(result ?? '')); }
      } catch (e) { res.writeHead(500); res.end('handler error: ' + (e && e.message)); }
    });
    server.listen(port);
    return server;
  },
};
