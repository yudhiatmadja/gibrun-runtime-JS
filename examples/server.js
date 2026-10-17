const http = await import('node:http');
const srv = http.createServer((q,s)=>{s.end('hi')});
srv.listen(0,()=>{console.log('port '+srv.address().port);srv.close()});

