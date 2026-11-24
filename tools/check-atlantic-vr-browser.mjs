import assert from 'node:assert/strict';
import http from 'node:http';
import { createRequire } from 'node:module';
import { access, readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const root = fileURLToPath(new URL('../', import.meta.url));
const shared = path.resolve(root, '../3d-floorplans/raincross/sandbox/node_modules');
const installed = name => { try { return require.resolve(name); } catch (error) { if (error.code !== 'MODULE_NOT_FOUND') throw error; } };
const { chromium } = require(process.env.MENU_PLAYWRIGHT || installed('playwright-core') || path.join(shared, 'playwright-core'));
const three = process.env.MENU_THREE || path.join(shared, 'three');
const chrome = process.env.MENU_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.glb': 'model/gltf-binary', '.png': 'image/png', '.wasm': 'application/wasm' };

const server = http.createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = path.resolve(root, '.' + pathname);
    const relative = path.relative(root, file);
    if (relative.startsWith('..') || path.isAbsolute(relative)) return res.writeHead(403).end();
    const body = await readFile(file);
    res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(body);
  } catch { res.writeHead(404).end(); }
});

let browser;
try {
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(8517, '127.0.0.1', resolve); });
  let executablePath;
  try { await access(chrome); executablePath = chrome; } catch { /* use bundled Chromium */ }
  browser = await chromium.launch({ executablePath, headless: true, args: ['--enable-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  await page.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', async route => {
    const prefix = '/npm/three@0.160.0/';
    const pathname = new URL(route.request().url()).pathname;
    const relative = pathname.slice(pathname.indexOf(prefix) + prefix.length);
    try { await route.fulfill({ contentType: mime[path.extname(relative)] || 'text/javascript', body: await readFile(path.join(three, relative)) }); }
    catch (error) { await route.fulfill({ status: 404, body: error.message }); }
  });
  await page.goto('http://127.0.0.1:8517/tools/atlantic-vr.html', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => globalThis.__atlanticVr?.loaded, null, { timeout: 30000 });
  const result = await page.evaluate(() => {
    let meshes = 0;
    const names = [];
    __atlanticVr.vehicle.traverse(object => { if (object.isMesh) meshes += 1; names.push(object.name); });
    return {
      meshes,
      names,
      xrEnabled: __atlanticVr.renderer.xr.enabled,
      status: document.querySelector('#status')?.textContent,
      canvas: document.querySelector('canvas')?.getBoundingClientRect().toJSON(),
      vrButton: !!document.querySelector('#VRButton'),
    };
  });
  assert.equal(result.meshes, 20);
  assert(result.names.includes('Viewport_Pilot') && result.names.includes('Viewport_Passenger'));
  assert.equal(result.xrEnabled, true);
  assert(result.vrButton);
  assert(result.status.startsWith('Ready'));
  assert(result.canvas.width === 1440 && result.canvas.height === 900);
  assert.deepEqual(errors, []);
  await page.getByRole('button', { name: 'Pilot seat' }).click();
  await page.waitForTimeout(250);
  const pilotDistance = await page.evaluate(() => {
    const anchor = __atlanticVr.vehicle.getObjectByName('XR_HEAD_PILOT');
    const position = anchor.getWorldPosition(anchor.position.clone());
    return __atlanticVr.camera.position.distanceTo(position);
  });
  assert(pilotDistance < 0.001, 'pilot view uses the authored XR head anchor');
  await page.screenshot({ path: path.join(root, 'art/atlantic_explorer/atlantic_explorer_vr_pilot.png') });
  await page.getByRole('button', { name: 'Exterior' }).click();
  await page.screenshot({ path: path.join(root, 'art/atlantic_explorer/atlantic_explorer_vr_browser.png') });
  console.log('Atlantic Explorer browser OK: GLB loaded, 20 meshes, WebXR enabled, clean console');
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
