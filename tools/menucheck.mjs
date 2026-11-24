// Browser checks for the shipped menu system. Run: node tools/menucheck.mjs
// MENU_PLAYWRIGHT / MENU_CHROME override browser dependencies; --offline uses
// MENU_THREE (or the adjacent project's Three.js) when the CDN is unavailable.
import assert from 'node:assert/strict';
import http from 'node:http';
import { createRequire } from 'node:module';
import { access, mkdir, readFile, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const root = fileURLToPath(new URL('../', import.meta.url));
const shared = path.resolve(root, '../3d-floorplans/raincross/sandbox/node_modules');
const artifacts = path.resolve(process.env.MENU_ARTIFACTS_DIR || path.join(os.tmpdir(), 'u505-menu-checks'));
const offline = process.argv.includes('--offline') || !!process.env.MENU_THREE;
function installed(name) { try { return require.resolve(name); } catch (error) { if (error.code !== 'MODULE_NOT_FOUND') throw error; } }
const { chromium } = require(process.env.MENU_PLAYWRIGHT || installed('playwright-core') || path.join(shared, 'playwright-core'));
const three = process.env.MENU_THREE || path.join(shared, 'three');
const chrome = process.env.MENU_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.svg': 'image/svg+xml',
  '.glb': 'model/gltf-binary', '.wasm': 'application/wasm', '.woff2': 'font/woff2', '.webp': 'image/webp' };
const server = http.createServer(async (req, res) => {
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    const file = path.resolve(root, '.' + (pathname === '/' ? '/index.html' : pathname));
    const relative = path.relative(root, file);
    if (relative.startsWith('..') || path.isAbsolute(relative) || relative.split(/[\\/]/).some(part => part.startsWith('.'))) {
      res.writeHead(403).end(); return;
    }
    const body = await readFile(file);
    res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(body);
  } catch { res.writeHead(404).end(); }
});

let browser;
const results = [], errors = [];
try {
  await mkdir(artifacts, { recursive: true });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(Number(process.env.MENU_PORT || 8516), '127.0.0.1', resolve); });
  const address = `http://127.0.0.1:${server.address().port}/`;
  let executablePath;
  try { await access(chrome); executablePath = chrome; } catch { /* Use Playwright's installed Chromium. */ }
  browser = await chromium.launch({ executablePath, headless: !process.argv.includes('--headed'), args: [
    '--enable-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist',
    '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
  ] });
  if (offline) {
    const version = JSON.parse(await readFile(path.join(three, 'package.json'), 'utf8')).version;
    console.log(`Offline dependency override: Three.js ${version} (${three})`);
  }
  async function createContext() {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
    if (offline) await context.route('https://cdn.jsdelivr.net/npm/three@0.160.0/**', async route => {
      const prefix = '/npm/three@0.160.0/';
      const pathname = new URL(route.request().url()).pathname;
      const relative = pathname.slice(pathname.indexOf(prefix) + prefix.length);
      try { await route.fulfill({ contentType: mime[path.extname(relative)] || 'application/octet-stream', body: await readFile(path.join(three, relative)) }); }
      catch (error) { await route.fulfill({ status: 404, body: error.message }); }
    });
    return context;
  }
  const context = await createContext();
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  const menu = page.locator('#fleet-menu');
  const action = name => menu.locator(`[data-menu-action="${name}"]:visible`).first();
  const setting = name => menu.locator(`[data-setting="${name}"]:visible`).first();
  const state = () => menu.getAttribute('data-screen');
  const waitScreen = name => page.waitForFunction(screen => document.querySelector('#fleet-menu')?.dataset.screen === screen, name);
  const check = async (name, fn) => {
    try { await fn(); results.push({ name, pass: true }); console.log(`PASS ${name}`); }
    catch (error) { results.push({ name, pass: false, error: error.message }); console.error(`FAIL ${name}: ${error.message}`); await page.screenshot({ path: path.join(artifacts, `failure-${results.length}.png`) }).catch(() => {}); }
  };
  const snapshot = async name => {
    await page.waitForTimeout(650); // Let the page's arrival animation settle.
    await page.screenshot({ path: path.join(artifacts, `${name}.png`) });
  };
  const settings = () => page.evaluate(() => ({ ...__u505.menus.settings }));
  const diagnostics = () => page.evaluate(() => {
    const u = __u505;
    return { ...(u.menus.diagnostics?.() || {}), exposure: u.lights.renderer.toneMappingExposure, pixelRatio: u.lights.renderer.getPixelRatio() };
  });
  async function change(name, fraction) {
    if (await setting(name).getAttribute('role') === 'switch') {
      const value = fraction > .5;
      if ((await setting(name).getAttribute('aria-checked') === 'true') !== value) await setting(name).click();
      assert.equal(await setting(name).getAttribute('aria-checked'), String(value));
      return value;
    }
    return setting(name).evaluate((element, f) => {
      let value;
      if (element.type === 'checkbox') { element.checked = f > .5; value = element.checked; }
      else if (element.tagName === 'SELECT') { const option = element.options[Math.round((element.options.length - 1) * f)]; element.value = option.value; value = element.value; }
      else if (element.type === 'range' || element.type === 'number') {
        const min = Number(element.min || 0), max = Number(element.max || 100), step = Number(element.step || 1);
        value = min + Math.round((max - min) * f / step) * step; element.value = String(value); value = Number(element.value);
      } else throw Error(`Unsupported setting control ${element.tagName}/${element.type}`);
      element.dispatchEvent(new Event('input', { bubbles: true })); element.dispatchEvent(new Event('change', { bubbles: true })); return value;
    }, fraction);
  }
  async function frozen() {
    const before = await page.evaluate(() => ({ t: __u505.sim.s.t, x: __u505.player.x, yaw: __u505.player.yaw }));
    await page.keyboard.down('w');
    await page.evaluate(() => __u505.tick(.8));
    await page.keyboard.up('w');
    const after = await page.evaluate(() => ({ t: __u505.sim.s.t, x: __u505.player.x, yaw: __u505.player.yaw }));
    assert.deepEqual(after, before, 'Game advanced while a menu was open');
  }
  async function menuHidden() { await page.waitForFunction(() => { const el = document.querySelector('#fleet-menu'); return !el || getComputedStyle(el).display === 'none' || el.hidden; }); }
  async function noOverflow() {
    const value = await page.evaluate(() => {
      const menu = document.querySelector('#fleet-menu'), bounds = menu.getBoundingClientRect();
      const body = menu.querySelector('.fm-body'), screen = menu.querySelector('.fm-screen:not([hidden])');
      const outside = [...menu.querySelectorAll('button,input,select')].filter(el => el.getClientRects().length).map(el => {
        const box = el.getBoundingClientRect();
        return { name: el.dataset.menuAction || el.dataset.setting || el.textContent.trim().slice(0, 30), left: box.left, right: box.right };
      }).filter(box => box.left < -1 || box.right > innerWidth + 1);
      return { screen: menu.dataset.screen, viewport: innerWidth, left: bounds.left, right: bounds.right, scroll: menu.scrollWidth, width: menu.clientWidth,
        contentScroll: body.scrollWidth, contentWidth: body.clientWidth, screenScroll: screen.scrollWidth, screenWidth: screen.clientWidth,
        documentScroll: document.documentElement.scrollWidth, outside };
    });
    // The clipped chart/background intentionally extends beyond the root. Check
    // actual page content and controls rather than counting that decoration.
    assert(value.left >= -1 && value.right <= value.viewport + 1 && value.contentScroll <= value.contentWidth + 1 &&
      value.screenScroll <= value.screenWidth + 1 && value.documentScroll <= value.viewport + 1 && !value.outside.length, JSON.stringify(value));
  }

  await page.goto(address, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => globalThis.__u505?.menus, null, { timeout: 45000 });
  await check('Splash is visible and freezes the operation', async () => { await waitScreen('splash'); await frozen(); await snapshot('01-splash'); });
  await check('Keyboard opens and navigates the main menu', async () => {
    await page.keyboard.press('Enter'); await waitScreen('main');
    assert(await action('board').evaluate(element => element === document.activeElement));
    await page.keyboard.press('ArrowRight');
    assert(await action('chapters').evaluate(element => element === document.activeElement));
    await page.keyboard.press('ArrowLeft'); await snapshot('02-main');
  });
  for (const screen of ['chapters', 'record', 'controls', 'credits']) {
    await check(`${screen} opens and returns to main`, async () => { await action(screen).click(); await waitScreen(screen); await frozen(); await action('back').click(); await waitScreen('main'); });
  }
  await check('Settings exposes each working tab', async () => {
    await action('settings').click(); await waitScreen('settings');
    for (const tab of ['audio', 'display', 'controls', 'accessibility']) {
      await menu.locator(`[data-settings-tab="${tab}"]`).click();
      assert(await menu.locator('[data-setting]:visible').count(), `${tab} has no setting controls`);
    }
    await frozen();
  });
  let saved;
  await check('Settings update renderer and persist after reload', async () => {
    await menu.locator('[data-settings-tab="audio"]').click(); await change('masterVolume', .35);
    await menu.locator('[data-settings-tab="display"]').click();
    const before = await diagnostics();
    await change('brightness', .7); await change('renderScale', .75); const fov = await change('fov', .7);
    const after = await diagnostics();
    assert.notEqual(after.exposure, before.exposure, 'Brightness did not change renderer exposure');
    assert.notEqual(after.pixelRatio, before.pixelRatio, 'Render scale did not change the drawing-buffer scale');
    assert(after.pixelRatio > 0);
    if ('cameraFov' in after) assert.equal(after.cameraFov, fov);
    await snapshot('03-settings-display');
    await menu.locator('[data-settings-tab="controls"]').click(); await change('sensitivity', .3); await change('invertY', 1);
    await menu.locator('[data-settings-tab="accessibility"]').click();
    await change('reducedMotion', 1); await change('captions', 0); await change('hints', 0);
    saved = await settings();
    await snapshot('03-settings'); await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => globalThis.__u505?.menus);
    assert.deepEqual(await settings(), saved, 'Preferences did not survive reload');
    if (await state() === 'splash') { await action('enter').click(); await waitScreen('main'); }
  });
  await check('Boarding starts at the bridge and the ladder starts the flood clock', async () => {
    if (await state() !== 'main') { await action('back').click(); await waitScreen('main'); }
    await page.emulateMedia({ reducedMotion: 'no-preference' });
    await action('settings').click(); await menu.locator('[data-settings-tab="accessibility"]').click();
    await change('reducedMotion', 0); await action('back').click(); await waitScreen('main');
    await action('board').click(); await waitScreen('briefing'); await frozen(); await snapshot('04-briefing');
    const firstOrder = await page.locator('.fm-briefing-order').textContent();
    await page.locator('#board-game:visible').click(); await menuHidden();
    assert.equal(await page.locator('#deck-command').textContent(), firstOrder);
    assert.equal(await page.locator('#cutscene-controls').isVisible(), false);
    const bridge = await page.evaluate(() => {
      const u = __u505, before = u.sim.s.t;
      u.tick(.5);
      return { t: before, clock: u.sim.clock(), unchanged: before === u.sim.s.t,
        onDeck: u.story.onDeck, hatch: u.exterior.nearDeckHatch(), act: u.story.act };
    });
    assert.deepEqual(bridge, { t: bridge.t, clock: '11:46:00', unchanged: true, onDeck: true, hatch: false, act: 2 });
    await snapshot('04-bridge');
    await page.keyboard.press('e'); await page.keyboard.press('f');
    assert(await page.evaluate(() => !__u505.story.boardingEntry.descent && !__u505.waiting));
    await page.keyboard.down('w'); await page.evaluate(() => __u505.tick(.59)); await page.keyboard.up('w');
    await page.waitForFunction(() => __u505.exterior.nearDeckHatch());
    assert.match(await page.locator('#prompt').textContent(), /^\[F\].*bridge hatch/);
    await page.keyboard.press('f');
    assert(await page.evaluate(() => !!__u505.story.boardingEntry?.descent));
    await page.keyboard.press('g'); await page.locator('#glossary').waitFor({ state: 'visible' });
    assert(await page.evaluate(() => {
      const u = __u505, start = u.story.boardingEntry.descent.time;
      u.tick(3);
      return u.story.boardingEntry.descent.time === start;
    }), 'The ladder moved while the notebook was open');
    await page.keyboard.press('g');
    await page.keyboard.press('p'); await page.locator('#pause').waitFor({ state: 'visible' }); await frozen();
    await page.locator('#resume').click();
    const landing = await page.evaluate(() => {
      const u = __u505, seededTime = u.sim.s.t;
      if (u.story.boardingEntry) u.tick(2);
      const atFoot = u.sim.s.t === seededTime && u.player.comp === u.sim.comps.findIndex(room => room.id === 'control') &&
        u.player.x === u.sim.hull.hatch.x_m - .55 && !u.story.onDeck && !u.story.boardingEntry;
      u.tick(.5);
      return { seededTime, atFoot, advanced: u.sim.s.t > seededTime };
    });
    assert.deepEqual(landing, { seededTime: bridge.t, atFoot: true, advanced: true });
    const currentOrder = page.locator('#current-order');
    await currentOrder.waitFor({ state: 'visible' });
    const belowDeckOrder = await currentOrder.textContent();
    assert.match(belowDeckOrder, /diesel room/);
    await page.keyboard.press('g');
    assert.equal(await page.locator('#notebook-order').textContent(), belowDeckOrder);
    await page.keyboard.press('g');
    await snapshot('04-ladder');
  });
  await check('Sensitivity and inversion affect mouse look', async () => {
    const delta = await page.evaluate(() => {
      const u = __u505, canvas = document.querySelector('#view'), before = { yaw: u.player.yaw, pitch: u.player.pitch };
      canvas.dispatchEvent(new MouseEvent('mousedown', { button: 0, clientX: 400, clientY: 300, bubbles: true }));
      dispatchEvent(new MouseEvent('mousemove', { clientX: 450, clientY: 320, movementX: 50, movementY: 20 }));
      dispatchEvent(new MouseEvent('mouseup'));
      return { yaw: u.player.yaw - before.yaw, pitch: u.player.pitch - before.pitch, settings: { ...u.menus.settings } };
    });
    assert(delta.yaw < 0, 'Mouse movement did not turn the camera');
    assert(delta.pitch > 0, 'Inverted Y did not reverse vertical look');
  });
  await check('Pause opens, freezes the operation, and returns from settings', async () => {
    await page.keyboard.press('p'); await page.locator('#pause').waitFor({ state: 'visible' }); await frozen(); await snapshot('05-pause');
    await page.locator('[data-pause-action="settings"]:visible').click(); await waitScreen('settings'); await frozen();
    await menu.locator('[data-settings-tab="controls"]').click(); await setting('sensitivity').focus();
    await page.keyboard.press('Enter'); await page.keyboard.press('p'); await page.keyboard.press('g');
    assert.equal(await state(), 'settings', 'A gameplay shortcut escaped the settings menu');
    assert(await page.evaluate(() => __u505.playPaused), 'Settings resumed the operation'); await frozen();
    await action('back').click(); await page.locator('#pause').waitFor({ state: 'visible' });
    await page.locator('#resume').click(); await page.locator('#pause').waitFor({ state: 'hidden' });
    assert.equal(await page.evaluate(() => __u505.playPaused), false);
  });
  await check('Master volume controls the actual audio output', async () => {
    const adjustFromPlay = async fraction => {
      await page.keyboard.press('p'); await page.locator('#pause').waitFor({ state: 'visible' });
      await page.locator('[data-pause-action="settings"]:visible').click(); await waitScreen('settings');
      await menu.locator('[data-settings-tab="audio"]').click(); await change('masterVolume', fraction);
      await action('back').click(); await page.locator('#pause').waitFor({ state: 'visible' }); await page.locator('#resume').click();
      await page.waitForTimeout(650);
      return page.evaluate(() => __u505.audio.output());
    };
    const silent = await adjustFromPlay(0);
    assert(silent.gain < .0001 && silent.rms < .0001, JSON.stringify(silent));
    const audible = await adjustFromPlay(.6);
    assert(audible.state === 'running' && audible.gain > .1 && audible.rms > .0001, JSON.stringify(audible));
  });
  await check('Return to main preserves a frozen operation', async () => {
    await page.keyboard.press('p'); await page.locator('#pause').waitFor({ state: 'visible' });
    await page.locator('[data-pause-action="main"]:visible').click(); await waitScreen('main'); await frozen();
  });
  await check('Cancelling a chapter restart returns to pause', async () => {
    await action('resume').click(); await menuHidden(); await page.keyboard.press('p');
    await page.locator('[data-pause-action="restart"]:visible').click(); await waitScreen('confirm'); await frozen();
    await action('cancel').click(); await menuHidden(); await page.locator('#pause').waitFor({ state: 'visible' });
    assert(await page.evaluate(() => __u505.playPaused), 'Cancel resumed the operation');
    await page.locator('[data-pause-action="main"]:visible').click(); await waitScreen('main');
  });
  await check('Menus fit narrow and short viewports', async () => {
    for (const viewport of [{ width: 390, height: 844 }, { width: 844, height: 390 }, { width: 1024, height: 768 }]) {
      await page.setViewportSize(viewport); await noOverflow();
      if (viewport.width > viewport.height) {
        const nav = await menu.locator('.fm-nav').boundingBox();
        const body = await menu.locator('.fm-body').boundingBox();
        assert(nav && body && nav.y + nav.height <= body.y + body.height + 1, 'The command strip is below the fold');
      }
      await action('settings').click(); await waitScreen('settings'); await noOverflow();
      await snapshot(`responsive-${viewport.width}x${viewport.height}`);
      await action('back').click(); await waitScreen('main');
    }
  });
  await check('Story overlays remain accessible after menu navigation', async () => {
    await page.setViewportSize({ width: 1440, height: 900 }); await action('resume').click(); await menuHidden();
    await page.keyboard.press('g'); await page.locator('#glossary').waitFor({ state: 'visible' }); await snapshot('06-notebook');
    await page.keyboard.press('g');
    await page.evaluate(() => {
      const u = __u505; u.jump('act2'); u.dismissIntro();
      u.sim.valves.forEach((valve, index) => { if (valve.kind === 'vent') u.sim.s.valve[index] = 1; });
      u.sim.advance(3600); u.tick(.01);
    });
    await page.locator('#banner').waitFor({ state: 'visible' }); await snapshot('07-loss');
    await page.evaluate(() => __u505.jump('final')); await page.locator('#banner').waitFor({ state: 'visible' }); await snapshot('08-final');
  });
  await check('Debug final restart opens main and leaves the real campaign checkpoint available', async () => {
    await page.keyboard.press('r'); await waitScreen('main');
    assert(await page.evaluate(() => !__u505.menus.state.hasRun), 'Finished debug operation remains live');
    assert.equal(await action('resume').count(), 1, 'Debug final cleared the real operation'); await frozen();
  });
  await check('Chapter I launches and restarts the approach', async () => {
    await action('chapters').click(); await waitScreen('chapters'); await menu.locator('[data-chapter="approach"]').click();
    if (await state() === 'confirm') await action('confirm').click();
    await menuHidden();
    assert.equal(await page.evaluate(() => __u505.story.act), 1);
    assert(await page.evaluate(() => __u505.exterior.running), 'Chapter I did not start');
    await page.locator('#current-order').waitFor({ state: 'visible' });
    assert.match(await page.locator('#current-order').textContent(), /Watch from Pillsbury/);
    await page.keyboard.press('p'); await page.locator('[data-pause-action="restart"]:visible').click(); await waitScreen('confirm');
    await action('confirm').click(); await menuHidden();
    assert.equal(await page.evaluate(() => __u505.story.act), 1, 'Restart changed the selected chapter');
    await page.locator('#intro').waitFor({ state: 'visible' }); await snapshot('09-approach-restart');
    const before = await page.evaluate(() => __u505.exterior.clock); await page.evaluate(() => __u505.tick(2));
    assert.equal(await page.evaluate(() => __u505.exterior.clock), before, 'Approach advanced behind its briefing');
    await page.locator('#intro-continue').click();
    assert(await page.evaluate(() => __u505.exterior.running), 'Restarted approach did not begin');
  });
  await check('Watch skip enters the same bridge and reduced motion descends immediately', async () => {
    await page.keyboard.press('p'); await page.locator('#pause').waitFor({ state: 'visible' });
    await page.locator('[data-pause-action="main"]:visible').click(); await waitScreen('main');
    await action('settings').click(); await menu.locator('[data-settings-tab="accessibility"]').click();
    await change('reducedMotion', 1); await action('back').click(); await waitScreen('main');
    await action('board').click(); await waitScreen('briefing'); await menu.locator('[data-menu-action="approach"]').click();
    await waitScreen('confirm'); await action('confirm').click(); await menuHidden();
    assert(await page.evaluate(() => __u505.story.act === 1 && __u505.exterior.running));
    await page.keyboard.press('Enter');
    assert(await page.evaluate(() => __u505.story.act === 2 && __u505.story.onDeck && __u505.sim.clock() === '11:46:00'));
    assert.match(await page.locator('#deck-command').textContent(), /Enter the bridge hatch/);
    await page.keyboard.down('w'); await page.evaluate(() => __u505.tick(.59)); await page.keyboard.up('w');
    assert(await page.evaluate(() => __u505.exterior.nearDeckHatch()));
    await page.keyboard.press('e');
    assert(await page.evaluate(() => !__u505.story.boardingEntry && !__u505.story.onDeck && !document.body.classList.contains('boarding-descent')));
  });
  await check('Natural approach completion reaches the visible fallback bridge hatch', async () => {
    await page.goto(`${address}?boatart=0&interiorart=0`, { waitUntil: 'domcontentloaded' });
    await waitScreen('splash'); await action('enter').click(); await waitScreen('main');
    await action('board').click(); await waitScreen('briefing'); await menu.locator('[data-menu-action="approach"]').click();
    await waitScreen('confirm'); await action('confirm').click(); await menuHidden();
    const fallback = await page.evaluate(() => {
      const u = __u505;
      u.tick(u.data.act1.seconds + 5);
      return { act: u.story.act, onDeck: u.story.onDeck, clock: u.sim.clock(),
        hatch: u.exterior.scene.getObjectByName('Bridge hatch fallback')?.visible };
    });
    assert.deepEqual(fallback, { act: 2, onDeck: true, clock: '11:46:00', hatch: true });
    await snapshot('10-fallback-bridge');
    await page.keyboard.down('w'); await page.evaluate(() => __u505.tick(.59)); await page.keyboard.up('w');
    await page.keyboard.press('e');
    assert(await page.evaluate(() => !__u505.story.onDeck && !__u505.story.boardingEntry));
  });
  await check('A corrupted checkpoint hides Resume and cancelling a replacement preserves the new valid checkpoint', async () => {
    const isolated = await createContext();
    try {
      const savePage = await isolated.newPage();
      savePage.on('pageerror', error => errors.push(error.message));
      await savePage.goto(address, { waitUntil: 'domcontentloaded' });
      await savePage.evaluate(() => localStorage.setItem('u505.operation.v1', '{invalid'));
      await savePage.reload({ waitUntil: 'domcontentloaded' });
      const menuAction = name => savePage.locator(`[data-menu-action="${name}"]:visible`).first();
      await menuAction('enter').click();
      assert.equal(await menuAction('resume').count(), 0, 'Corrupt data appeared resumable');
      await menuAction('board').click(); await savePage.locator('#board-game:visible').click();
      const saved = await savePage.evaluate(() => localStorage.getItem('u505.operation.v1'));
      assert.equal(JSON.parse(saved).stage, 'bridge');
      await savePage.keyboard.press('p'); await savePage.locator('[data-pause-action="main"]:visible').click();
      await menuAction('board').click(); await savePage.locator('#board-game:visible').click();
      await menuAction('cancel').click();
      assert.equal(await savePage.evaluate(() => localStorage.getItem('u505.operation.v1')), saved);
      await savePage.reload({ waitUntil: 'domcontentloaded' });
      await menuAction('enter').click(); await menuAction('resume').click();
      assert.match(await savePage.locator('#deck-command').textContent(), /Enter the bridge hatch/);
      await savePage.keyboard.down('w'); await savePage.evaluate(() => __u505.tick(.59)); await savePage.keyboard.up('w');
      await savePage.keyboard.press('f');
      await savePage.evaluate(() => { if (__u505.story.boardingEntry) __u505.tick(2); });
      assert.equal(await savePage.evaluate(() => JSON.parse(localStorage.getItem('u505.operation.v1')).stage), 'ladder');
      await savePage.reload({ waitUntil: 'domcontentloaded' });
      await menuAction('enter').click(); await menuAction('resume').click();
      await savePage.locator('#current-order').waitFor({ state: 'visible' });
      assert.match(await savePage.locator('#current-order').textContent(), /diesel room/);
    } finally {
      await isolated.close();
    }
  });
  await check('No uncaught browser errors', () => assert.deepEqual(errors, []));
  await writeFile(path.join(artifacts, 'results.json'), JSON.stringify({ address, offline, results, errors }, null, 2));
  console.log(`\n${results.filter(result => result.pass).length}/${results.length} checks passed. Artifacts: ${artifacts}`);
  if (results.some(result => !result.pass)) process.exitCode = 1;
} finally {
  await browser?.close();
  await new Promise(resolve => server.close(resolve));
}
