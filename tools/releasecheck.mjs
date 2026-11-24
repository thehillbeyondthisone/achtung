// Smoke-test the staged static release with a fresh browser context per case.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const require = createRequire(import.meta.url);
const shared = path.resolve(root, '../3d-floorplans/raincross/sandbox/node_modules/playwright-core');
const { chromium } = require(process.env.MENU_PLAYWRIGHT || (existsSync(shared) ? shared : 'playwright-core'));
const chrome = process.env.MENU_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const servers = [];

function startServer(release) {
  const args = [path.join(root, 'tools', 'serve.mjs'), '0'];
  if (release) args.push('--release');
  const child = spawn(process.execPath, args, { stdio: ['ignore', 'pipe', 'inherit'], windowsHide: true });
  servers.push(child);
  return new Promise((resolve, reject) => {
    child.on('error', reject);
    child.on('exit', code => reject(new Error(`Preview exited (${code}) before it was ready.`)));
    child.stdout.on('data', bytes => {
      const address = bytes.toString().match(/http:\/\/127\.0\.0\.1:\d+\//)?.[0];
      if (address) resolve(address);
    });
  });
}

async function check(browser, name, address, missing, throttle = false) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  try {
    const origin = new URL(address).origin;
    const requests = [];
    const external = [];
    await context.route('**/*', route => {
      const url = new URL(route.request().url());
      if (url.origin !== origin) { external.push(url.href); return route.abort(); }
      requests.push(url.pathname);
      if (missing && url.pathname.endsWith(`/art/${missing}`)) return route.fulfill({ status: 404 });
      return route.continue();
    });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    if (throttle) {
      const cdp = await context.newCDPSession(page);
      await cdp.send('Network.emulateNetworkConditions', {
        offline: false, latency: 80, downloadThroughput: 2_500_000, uploadThroughput: 1_250_000,
      });
    }

    assert.equal((await page.goto(address, { waitUntil: 'domcontentloaded' })).status(), 200);
    await page.locator('[data-menu-action="enter"]').waitFor({ state: 'visible' });
    const menuMs = Math.round(await page.evaluate(() => performance.now()));
    await page.locator('[data-menu-action="enter"]').click();
    await page.locator('[data-menu-action="board"]').click();
    await page.locator('#board-game:visible').click();
    await page.waitForFunction(() => __u505.story.act === 2 && !__u505.menus.active);
    await page.keyboard.press('g');

    const sources = await page.locator('#glossary a[href]').evaluateAll(links => links.map(link => link.getAttribute('href')));
    assert(sources.length > 0 && sources.every(link => /^https?:\/\//.test(link)), 'Notebook links should point to online sources.');
    if (missing !== 'u505_game.glb') await page.waitForFunction(() => !!__u505.exterior.scene.getObjectByName('U-505 model'));
    if (missing !== 'u505_interior.glb') await page.waitForFunction(() => __u505.interior.loaded().includes('diesel'));
    if (missing === 'u505_game.glb') assert(await page.evaluate(() => !__u505.exterior.scene.getObjectByName('U-505 model')));
    if (missing === 'u505_interior.glb') assert.deepEqual(await page.evaluate(() => __u505.interior.loaded()), []);
    assert(requests.some(url => url.endsWith('/art/u505_game.glb')) && requests.some(url => url.endsWith('/art/u505_interior.glb')));
    if (missing !== 'u505_game.glb') assert(requests.some(url => url.endsWith('/draco_decoder.wasm')));
    await page.keyboard.press('g');
    const before = await page.evaluate(() => ({ x: __u505.player.x, side: __u505.player.side }));
    await page.keyboard.down('w');
    try {
      await page.waitForFunction(previous => Math.hypot(__u505.player.x - previous.x, __u505.player.side - previous.side) > .1, before);
      if (missing) await page.waitForFunction(() => __u505.target?.type === 'deckHatch');
    }
    finally { await page.keyboard.up('w'); }
    if (missing) {
      const bridgeTime = await page.evaluate(() => __u505.sim.s.t);
      await page.keyboard.press('e');
      await page.waitForFunction(time => !__u505.story.onDeck && __u505.sim.s.t > time, bridgeTime);
    }
    assert.deepEqual(external, []);
    assert.deepEqual(errors, []);
    console.log(`PASS ${name}. Fresh menu ${menuMs} ms${throttle ? ' at 20 Mbps / 80 ms' : ''}.`);
  } finally {
    await context.close();
  }
}

let browser;
try {
  assert(existsSync(path.join(root, 'dist', 'u505', 'index.html')), 'Run node tools/stage-release.mjs first.');
  const rootAddress = await startServer(true);
  const subpath = new URL('dist/u505/', await startServer(false)).href;
  browser = await chromium.launch({ executablePath: existsSync(chrome) ? chrome : undefined,
    headless: !process.argv.includes('--headed'), args: ['--enable-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  console.log(`Chromium ${browser.version()} at 1280 × 720, device scale 1.`);
  await check(browser, 'Site root with both models', rootAddress, null, true);
  await check(browser, 'Site subpath with both models', subpath);
  await check(browser, 'Missing exterior model uses the fallback', rootAddress, 'u505_game.glb');
  await check(browser, 'Missing interior model uses the fallback', subpath, 'u505_interior.glb');
} finally {
  await browser?.close();
  for (const server of servers) server.kill();
}
