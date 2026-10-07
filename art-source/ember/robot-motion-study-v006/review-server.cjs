// 仅给本轮动作试样提供本机预览；不读取项目其他目录。
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(process.argv[2] || __dirname);
const port = Number(process.argv[3] || 8137);
const mime = {'.html':'text/html; charset=utf-8','.png':'image/png','.gif':'image/gif','.webp':'image/webp','.json':'application/json; charset=utf-8','.md':'text/plain; charset=utf-8'};
http.createServer(async (req,res) => {
  try {
    const url = new URL(req.url, 'http://127.0.0.1');
    const relativeUrl = decodeURIComponent(url.pathname === '/' ? '/review.html' : url.pathname);
    const file = path.resolve(root, '.' + relativeUrl);
    const relativeFile = path.relative(root, file);
    if (relativeFile.startsWith('..') || path.isAbsolute(relativeFile)) {
      res.writeHead(403); res.end('Forbidden'); return;
    }
    const bytes = await fs.readFile(file);
    res.writeHead(200, {'Content-Type':mime[path.extname(file)] || 'application/octet-stream','Cache-Control':'no-store'});
    res.end(bytes);
  } catch {
    res.writeHead(404); res.end('Not found');
  }
}).listen(port,'127.0.0.1',() => process.stdout.write('Motion-study preview: http://127.0.0.1:' + port + '/review.html\n'));

