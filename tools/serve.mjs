// Minimal local static preview; no dependencies or Python installation required.
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const port = Number(process.argv[2] || 8505);
const types = { '.html': 'text/html', '.htm': 'text/html', '.js': 'text/javascript',
  '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.md': 'text/plain; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.gif': 'image/gif',
  '.glb': 'model/gltf-binary' };
http.createServer(async (req, res) => {
  try {
    if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405).end(); return; }
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    const relative = path.relative(root, file);
    const type = types[path.extname(file).toLowerCase()];
    if (relative.startsWith('..') || path.isAbsolute(relative) || !type || relative.split(/[\\/]/).some(p => p.startsWith('.'))) {
      res.writeHead(403).end('Forbidden'); return;
    }
    const body = await fs.readFile(file);
    res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
    res.end(req.method === 'HEAD' ? undefined : body);
  } catch (error) {
    const status = error.code === 'ENOENT' || error.code === 'EISDIR' ? 404 : 400;
    res.writeHead(status).end(status === 404 ? 'Not found' : 'Bad request');
  }
}).listen(port, '127.0.0.1', () => console.log(`U-505 preview: http://127.0.0.1:${port}/`));
