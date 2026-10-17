const srv = Gibrun.serve(() => 'hi gibrun', { port: 0 });
await new Promise(r => srv.on('listening', r));
const port = srv.address().port;
const res = await fetch(`http://127.0.0.1:${port}/`);
const text = await res.text();
console.log('serve-ok:' + text);
srv.close();
