// The front end stays independent of the simulation; the bridge owns game actions.
const STORAGE_KEY = 'u505.settings.v1';
const DEFAULTS = Object.freeze({ masterVolume: 80, muted: false, renderScale: 'auto', brightness: 100,
  fov: 74, sensitivity: 100, invertY: false, reducedMotion: false, captions: true, hints: true });
export function readMenuSettings() {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') || {}; } catch {}
  const result = { ...DEFAULTS };
  for (const name of ['masterVolume', 'brightness', 'fov', 'sensitivity']) {
    const bounds = { masterVolume: [0, 100], brightness: [65, 140], fov: [60, 100], sensitivity: [25, 200] }[name];
    if (typeof saved[name] === 'number' && Number.isFinite(saved[name])) result[name] = Math.min(bounds[1], Math.max(bounds[0], saved[name]));
  }
  for (const name of ['muted', 'invertY', 'reducedMotion', 'captions', 'hints']) if (typeof saved[name] === 'boolean') result[name] = saved[name];
  if (['auto', '1', '1.5', '2'].includes(saved.renderScale)) result.renderScale = saved.renderScale;
  return result;
}
const escape = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const navItem = (action, title, primary = false, extra = '') => `<button type="button" class="fm-nav-item${primary ? ' is-primary' : ''}" data-menu-action="${action}" ${extra}><span>${title}</span><span aria-hidden="true">${primary ? '→' : '↗'}</span></button>`;
const button = (action, title, primary = false, extra = '') => `<button type="button" class="fm-button${primary ? ' is-primary' : ''}" data-menu-action="${action}" ${extra}>${title}${primary ? '<span aria-hidden="true">→</span>' : ''}</button>`;
const back = `<button type="button" class="fm-back" data-menu-action="back"><span aria-hidden="true">←</span> Back <kbd class="fm-key">Esc</kbd></button>`;
const heading = (title, text) => `<header class="fm-page-heading"><h1 tabindex="-1">${title}</h1>${text ? `<p>${text}</p>` : ''}</header>`;
const operationMap = `<svg viewBox="0 0 480 390" class="fm-operation-map" role="img" aria-label="Stylized chart of the Atlantic off northwest Africa, marking the operation area"><defs><pattern id="fm-map-grid" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="currentColor" stroke-width=".5" opacity=".2"/></pattern></defs><rect x="1" y="1" width="478" height="388" fill="url(#fm-map-grid)" stroke="currentColor" opacity=".5"/><path d="M340 0l-18 38 10 20-22 32 2 32-35 31-20 40 8 35-24 27 8 44-20 32-3 59H480V0Z" fill="currentColor" opacity=".07"/><path d="M340 0l-18 38 10 20-22 32 2 32-35 31-20 40 8 35-24 27 8 44-20 32-3 59" fill="none" stroke="currentColor" opacity=".65"/><path d="M50 330C90 280 75 205 160 185S212 140 248 119" fill="none" stroke="currentColor" stroke-dasharray="4 7" opacity=".6"/><circle cx="163" cy="183" r="62" fill="none" stroke="currentColor" opacity=".22"/><circle cx="163" cy="183" r="36" fill="none" stroke="currentColor" opacity=".5"/><circle cx="163" cy="183" r="5" fill="currentColor"/><path d="M163 103v35m0 90v35m-80-80h35m90 0h35" stroke="currentColor"/><g fill="currentColor" font-family="monospace" font-size="10" letter-spacing="2"><text x="32" y="40">NORTH ATLANTIC</text><text x="335" y="190" transform="rotate(-73 335 190)">WEST AFRICA</text><text x="265" y="116">RIO DE ORO</text><text x="25" y="366">OPERATION AREA / 4 JUN 1944</text><text x="150" y="88">N</text></g><path d="M163 49l-5 16h10Z" fill="currentColor"/></svg>`;

export function createMenus(bridge, settings) {
  const root = document.createElement('section');
  root.id = 'fleet-menu'; root.className = 'fm-menu'; root.dataset.screen = 'splash';
  root.setAttribute('role', 'dialog'); root.setAttribute('aria-modal', 'true'); root.setAttribute('aria-label', 'U-505 game menu');
  root.innerHTML = `<header class="fm-topbar"><span class="fm-brand">U.S. Navy <b>/</b> Task Group 22.3</span><div class="fm-top-meta"><span>4 June 1944</span><button type="button" class="fm-icon-button" data-menu-action="fullscreen" aria-label="Toggle fullscreen" title="Toggle fullscreen">⛶</button></div></header>
    <div class="fm-body">
      <section class="fm-screen fm-splash" data-screen="splash"><div class="fm-cover"><h1 class="fm-title">U-505 <span>Boarding Party</span></h1><button type="button" class="fm-enter" data-menu-action="enter">Open operation file <kbd class="fm-key" aria-hidden="true">Enter ↵</kbd></button></div></section>
      <section class="fm-screen fm-main" data-screen="main" hidden><div class="fm-front-spread"><header class="fm-hero"><p class="fm-kicker">Capture &amp; salvage</p><h1 class="fm-title" tabindex="-1">U-505 <span>Boarding Party</span></h1><p class="fm-deck">The crew has abandoned ship. The diesels are still turning. Get below and stop the flooding.</p></header><figure class="fm-plate"><div class="fm-plate-image"><img src="docs/visuals/blender/u505_broadside_atlantic.jpg" alt="Broadside reconstruction of U-505 running on the surface" width="1920" height="1080"><span class="fm-sighting" aria-hidden="true"></span></div><figcaption><span>U-505 / Broadside</span><span>Exterior reconstruction</span></figcaption></figure></div>
        <nav class="fm-nav" aria-label="Main menu"><div class="fm-orders-tab">${navItem('resume', 'Resume operation', true, 'hidden')}${navItem('board', 'Begin operation', true)}</div>${navItem('chapters', 'Select chapter')}${navItem('record', 'Service record')}${navItem('settings', 'Settings')}${navItem('credits', 'About the operation')}</nav>
      </section>
      <section class="fm-screen fm-page" data-screen="briefing" hidden>${back}<div class="fm-briefing-grid"><div class="fm-briefing-copy"><p class="fm-kicker">4 June 1944 / 11:46 GCT</p>${heading('Boarding orders', 'You are part of the American boarding party sent aboard U-505. Her crew has abandoned ship. Below deck, the diesels are running and seawater is pouring in.')}<p class="fm-briefing-order"><strong>${escape(bridge.boardingOrder)}</strong></p><div class="fm-actions">${button('launch', 'Board U-505', true, 'id="board-game"')}${button('approach', 'Watch the approach')}</div><p class="fm-muted">The route and flooding model are simplified. The notebook distinguishes reports from assumptions.</p></div><figure class="fm-chart-sheet">${operationMap}<figcaption>Schematic of the operation area</figcaption></figure></div></section>
      <section class="fm-screen fm-page" data-screen="settings" hidden>${back}${heading('Settings')}<div class="fm-settings-layout"><div class="fm-settings-tabs" role="tablist" aria-label="Settings categories">${['audio','display','controls','accessibility'].map((name, i) => `<button type="button" role="tab" id="fm-tab-${name}" aria-controls="fm-settings-panel" aria-selected="${i === 0}" tabindex="${i === 0 ? 0 : -1}" data-settings-tab="${name}">${name}</button>`).join('')}</div><div class="fm-settings-sheet"><div id="fm-settings-panel" role="tabpanel" aria-labelledby="fm-tab-audio"></div><div class="fm-actions">${button('reset-settings', 'Restore defaults')}${button('controls', 'View controls')}</div><p class="fm-settings-note" id="fm-settings-status" role="status">All changes saved automatically.</p></div></div></section>
      <section class="fm-screen fm-page" data-screen="chapters" hidden>${back}${heading('Select chapter')}<ol class="fm-chapters">${[
        ['approach','I','The approach','4 JUN · 11:09','Watch from Pillsbury as the hunt brings U-505 to the surface.'],
        ['boarding','II','Boarding party','4 JUN · 11:46','Go below. Stop the flooding and secure the submarine.'],
        ['salvage','III','Keep her afloat','4 JUN · 12:40','Survey the flooded rooms and rig the portable pumps.'],
        ['rescue','IV','The long way home','7 JUN','Return to a settling boat. Power the pumps and save her.']
      ].map(([id, number, title, date, text]) => `<li><button type="button" class="fm-chapter" data-chapter="${id}"><span class="fm-chapter-date">${date}</span><span class="fm-chapter-number" aria-label="Chapter ${number}">${number}</span><strong>${title}</strong><span class="fm-chapter-desc">${text}</span><span class="fm-chapter-link" aria-hidden="true">→</span></button></li>`).join('')}</ol><p class="fm-muted">Chapters begin at reconstructed checkpoints. Starting one replaces the current operation. Your service record carries over.</p></section>
      <section class="fm-screen fm-page" data-screen="record" hidden>${back}${heading('Service record')}<div id="fm-record-content" class="fm-record-layout"></div></section>
      <section class="fm-screen fm-page" data-screen="controls" hidden>${back}${heading('Field manual')}<div class="fm-control-grid">${[
        ['MOVEMENT', [['W A S D','Move'],['SHIFT','Run'],['MOUSE','Look around'],['CLICK + DRAG','Look if mouse capture is unavailable']]],
        ['ABOARD THE BOAT', [['E','Use / hold to turn a valve'],['F','Second action / ladder / handoff / knock on a shut hatch'],['L','Hand lamp on or off'],['G','Open the notebook'],['ENTER','Skip the approach or tow']]],
        ['YOUR STATION', [['P / ESC','Pause / release mouse'],['M','Toggle sound'],['R','Retry after a loss'],['TAB / ENTER','Navigate / select in menus']]]
      ].map(([title, rows]) => `<div class="fm-control-group"><h2 class="fm-section-label">${title}</h2><dl>${rows.map(([key,value]) => `<dt><kbd class="fm-key">${key}</kbd></dt><dd>${value}</dd>`).join('')}</dl></div>`).join('')}</div><p class="fm-muted">Press F at the bridge hatch to board, or at the control-room ladder to climb out. On deck, F waits or hands off the pumps. Press E beside the hatch to return below.</p></section>
      <section class="fm-screen fm-page" data-screen="credits" hidden>${back}${heading('About the operation')}<div class="fm-credits-copy"><p>On 4 June 1944, the U.S. Navy’s Task Group 22.3 captured the German submarine U-505 off West Africa. The boarding and salvage parties kept her afloat through flooding, a long tow, and a second fight to save her days later.</p><p>The game follows the crew’s work securing machinery, stopping the ingress, and rigging pumps. The route, interaction procedures, timing, and buoyancy model include simplifications and assumptions.</p><h2>The historical record</h2><p>The in-game notebook collects the reports, technical terms, source disagreements, and model assumptions as you explore. Open it with <kbd class="fm-key">G</kbd> during an operation.</p><div class="fm-actions">${button('controls', 'Read the field manual')}${button('record', 'Open service record')}</div><p class="fm-muted">Built with Three.js. Exterior artwork rendered from the project’s U-505 model.</p></div></section>
      <section class="fm-screen fm-page fm-confirm" data-screen="confirm" hidden><h1 tabindex="-1" id="fm-confirm-title"></h1><p id="fm-confirm-copy"></p><div class="fm-actions">${button('confirm', 'Proceed', true)}${button('cancel', 'Go back')}</div></section>
    </div><footer class="fm-footer"><span>North Atlantic <b>/</b> Off Rio de Oro</span><button type="button" class="fm-footer-help" data-menu-action="controls">Field manual <span aria-hidden="true">↗</span></button></footer>`;
  document.body.append(root);
  let active = true, screen = 'splash', hasRun = false, tab = 'audio', stack = [], confirmAction = null;
  let lastFocus = null;
  const body = root.querySelector('.fm-body');
  const pages = [...root.querySelectorAll('.fm-screen')];
  const focusPage = () => {
    const page = pages.find(p => !p.hidden);
    const el = screen === 'splash' ? page.querySelector('button') : screen === 'main' ? page.querySelector('.fm-nav-item:not([hidden])') : page.querySelector('h1');
    el?.focus({ preventScroll: true });
  };
  function show(next, push = true) {
    if (push && active && screen !== next) stack.push({ screen, focus: document.activeElement, scroll: body.scrollTop });
    if (!active) lastFocus = document.activeElement;
    active = true; screen = next; root.hidden = false; root.dataset.screen = next;
    document.body.classList.add('fm-menu-open'); bridge.freeze();
    for (const page of pages) page.hidden = page.dataset.screen !== next;
    const resumable = hasRun || bridge.hasCheckpoint();
    root.querySelector('[data-menu-action="resume"]').hidden = !resumable;
    root.querySelector('[data-menu-action="board"]').classList.toggle('is-primary', !resumable);
    if (next === 'record') renderRecord();
    if (next === 'settings') renderSettings();
    body.scrollTop = 0;
    focusPage();
  }
  function hide() {
    active = false; root.hidden = true; document.body.classList.remove('fm-menu-open'); stack = [];
  }
  function goBack() {
    if (screen === 'splash') return;
    const previous = stack.pop();
    if (previous?.screen === 'pause') { hide(); bridge.showPause(); lastFocus?.focus({ preventScroll: true }); return; }
    show(previous?.screen || 'main', false);
    body.scrollTop = previous?.scroll ?? 0;
    if (previous?.focus?.isConnected && !previous.focus.closest('[hidden]')) previous.focus.focus({ preventScroll: true });
  }
  function save() {
    let saved = true;
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(settings)); } catch { saved = false; }
    bridge.applySettings(settings);
    document.getElementById('fm-settings-status').textContent = saved ? 'All changes saved automatically.' : 'Settings applied for this session. Device storage is unavailable.';
  }
  const range = (name, title, text, min, max, step, unit = '%') => `<div class="fm-setting-row"><label class="fm-setting-copy" for="fm-setting-${name}"><strong>${title}</strong><small>${text}</small></label><div class="fm-setting-control"><input id="fm-setting-${name}" data-setting="${name}" type="range" min="${min}" max="${max}" step="${step}" value="${settings[name]}"><output for="fm-setting-${name}">${settings[name]}${unit}</output></div></div>`;
  const toggle = (name, title, text) => `<div class="fm-setting-row"><div class="fm-setting-copy" id="fm-label-${name}"><strong>${title}</strong><small>${text}</small></div><button type="button" class="fm-toggle" data-setting="${name}" role="switch" aria-checked="${settings[name]}" aria-labelledby="fm-label-${name}"><span>${settings[name] ? 'On' : 'Off'}</span><i aria-hidden="true"></i></button></div>`;
  function renderSettings() {
    const content = {
      audio: range('masterVolume','Master volume','The sea, the machinery, and every creak of the hull.',0,100,1) + toggle('muted','Mute all sound','Also available during play with M.'),
      display: `<div class="fm-setting-row"><label class="fm-setting-copy" for="fm-setting-renderScale"><strong>Render quality</strong><small>Pixel density. Lower settings ease the load on your station.</small></label><select id="fm-setting-renderScale" data-setting="renderScale">${[['auto','Automatic'],['1','Performance · 1×'],['1.5','Balanced · 1.5×'],['2','High · 2×']].map(([v,label]) => `<option value="${v}" ${settings.renderScale === v ? 'selected' : ''}>${label}</option>`).join('')}</select></div>` + range('brightness','Brightness','Adjust the visibility of the interior compartments.',65,140,5) + range('fov','Field of view','Your view below deck. Wider angles show more of the room.',60,100,1,'°') + `<div class="fm-setting-row"><div class="fm-setting-copy"><strong>Fullscreen</strong><small>Give the Atlantic your full attention.</small></div>${button('fullscreen','Toggle fullscreen')}</div>`,
      controls: range('sensitivity','Mouse sensitivity','Set the speed of your view. 100% is the original setting.',25,200,5) + toggle('invertY','Invert vertical look','Move the mouse up to look down.') + `<p class="fm-settings-note">WASD to move · E to use · F for a second action · G for the notebook.</p>`,
      accessibility: toggle('reducedMotion','Reduce motion','Steady menu effects and soften camera movement. Your system preference is also respected.') + toggle('captions','Story captions','Show the historical captions during exterior sequences.') + toggle('hints','Control hints','Show the persistent keyboard guide during play.')
    };
    const panel = document.getElementById('fm-settings-panel');
    panel.setAttribute('aria-labelledby', `fm-tab-${tab}`);
    panel.innerHTML = content[tab];
    for (const el of root.querySelectorAll('[data-settings-tab]')) { const selected = el.dataset.settingsTab === tab; el.setAttribute('aria-selected', selected); el.tabIndex = selected ? 0 : -1; }
  }
  function renderRecord() {
    const record = bridge.getRecord();
    const completion = Math.round(record.found / Math.max(1, record.total) * 100);
    document.getElementById('fm-record-content').innerHTML = `<aside class="fm-record-stats"><div class="fm-stat"><strong>${record.found}<small> / ${record.total}</small></strong><span>Archive entries</span><meter min="0" max="100" value="${completion}" aria-label="Archive completion">${completion}%</meter><small>${completion}% complete</small></div><div class="fm-stat"><strong>${record.terms}</strong><span>Naval terms discovered</span></div><p class="fm-muted">Discoveries and the latest campaign checkpoint are saved in this browser.</p></aside><ol class="fm-record-list">${record.entries.map(entry => `<li class="fm-record-entry${entry.found ? ' is-found' : ''}"><div><h2>${escape(entry.found ? entry.title : 'Undiscovered account')}</h2>${entry.found ? `<p>${escape(entry.summary || 'Filed in your notebook. Press G during the operation to read the account.')}</p>` : ''}</div><span class="fm-record-state">${entry.found ? 'Filed' : 'Sealed'}</span></li>`).join('')}</ol>`;
  }
  function ask(title, copy, action) {
    document.getElementById('fm-confirm-title').textContent = title;
    document.getElementById('fm-confirm-copy').textContent = copy;
    confirmAction = action; show('confirm');
  }
  function launch(chapter) {
    hide(); hasRun = true; bridge.launch(chapter);
  }
  function handle(action) {
    if (action === 'enter') { stack = []; show('main', false); return; }
    if (action === 'back' || action === 'cancel') { goBack(); return; }
    if (action === 'board') { show('briefing'); return; }
    if (action === 'launch' || action === 'approach') {
      const chapter = action === 'launch' ? 'boarding-bridge' : 'watch-approach';
      if (hasRun || bridge.hasCheckpoint()) ask('Begin a new operation?', 'Your current operation will be replaced. Your archive discoveries and settings will stay with you.', () => launch(chapter));
      else launch(chapter);
      return;
    }
    if (action === 'resume') {
      hide();
      if (hasRun) bridge.resume();
      else if (bridge.restoreCheckpoint()) hasRun = true;
      else show('main', false);
      return;
    }
    if (action === 'confirm') { const proceed = confirmAction; confirmAction = null; proceed?.(); return; }
    if (action === 'fullscreen') { bridge.fullscreen().catch(() => { document.getElementById('fm-settings-status').textContent = 'Fullscreen is unavailable in this preview. Open the game in a browser window.'; }); return; }
    if (action === 'reset-settings') { Object.assign(settings, DEFAULTS); save(); renderSettings(); root.querySelector(`[data-settings-tab="${tab}"]`).focus(); return; }
    if (['chapters','settings','record','controls','credits'].includes(action)) show(action);
  }
  root.addEventListener('click', event => {
    const toggleEl = event.target.closest('button[data-setting]');
    if (toggleEl) { const name = toggleEl.dataset.setting; settings[name] = !settings[name]; toggleEl.setAttribute('aria-checked', settings[name]); toggleEl.querySelector('span').textContent = settings[name] ? 'On' : 'Off'; save(); return; }
    const tabEl = event.target.closest('[data-settings-tab]');
    if (tabEl) { tab = tabEl.dataset.settingsTab; renderSettings(); tabEl.focus(); return; }
    const chapter = event.target.closest('[data-chapter]');
    if (chapter) { const id = chapter.dataset.chapter; if (hasRun) ask('Change your orders?', 'Starting this chapter replaces the current operation with a reconstructed checkpoint. Your archive discoveries stay with you.', () => launch(id)); else launch(id); return; }
    const action = event.target.closest('[data-menu-action]')?.dataset.menuAction;
    if (action) handle(action);
  });
  root.addEventListener('input', event => {
    const name = event.target.dataset.setting; if (!name || event.target.tagName === 'BUTTON') return;
    settings[name] = event.target.type === 'range' ? Number(event.target.value) : event.target.value;
    const output = event.target.parentElement.querySelector('output');
    if (output) output.value = settings[name] + (name === 'fov' ? '°' : '%');
    save();
  });
  function onKey(event) {
    if (!active) return false;
    if (event.code === 'Escape' && !event.repeat) { event.preventDefault(); if (screen !== 'main' || stack.length) goBack(); return true; }
    if (screen === 'splash' && event.code === 'Enter' && !event.target.closest?.('button')) { event.preventDefault(); if (!event.repeat) handle('enter'); return true; }
    const forward = ['ArrowDown', 'ArrowRight'].includes(event.code);
    const arrow = forward || ['ArrowUp', 'ArrowLeft'].includes(event.code);
    if (event.target.matches?.('[role="tab"]') && (arrow || ['Home','End'].includes(event.code))) {
      const tabs = [...root.querySelectorAll('[role="tab"]')], index = tabs.indexOf(event.target);
      const next = event.code === 'Home' ? 0 : event.code === 'End' ? tabs.length - 1 : (index + (forward ? 1 : -1) + tabs.length) % tabs.length;
      tab = tabs[next].dataset.settingsTab; renderSettings(); tabs[next].focus(); event.preventDefault();
    }
    if (screen === 'main' && arrow) {
      const choices = [...root.querySelectorAll('.fm-main .fm-nav-item:not([hidden])')], index = choices.indexOf(document.activeElement);
      choices[index < 0 ? (forward ? 0 : choices.length - 1) : (index + (forward ? 1 : -1) + choices.length) % choices.length]?.focus(); event.preventDefault();
    }
    trapFocus(event, root);
    return true;
  }
  function trapFocus(event, container) {
    if (event.code !== 'Tab') return;
    const focusable = [...container.querySelectorAll('button:not(:disabled),input,select,a[href],summary')].filter(el => !el.closest('[hidden]') && el.tabIndex !== -1 && el.getClientRects().length);
    const first = focusable[0], last = focusable.at(-1);
    if (event.shiftKey && (document.activeElement === first || !container.contains(document.activeElement))) { last?.focus(); event.preventDefault(); }
    else if (!event.shiftKey && document.activeElement === last) { first?.focus(); event.preventDefault(); }
  }
  function openFromPause(next) {
    lastFocus = document.activeElement; stack = [{ screen: 'pause', focus: lastFocus }];
    bridge.hidePause(); show(next, false);
  }
  bridge.applySettings(settings);
  show('splash', false);
  document.getElementById('fleet-loading')?.remove();
  return {
    get active() { return active; }, get state() { return { screen, active, hasRun, tab }; }, settings,
    onKey, openFromPause, trapFocus,
    main() { stack = []; show('main', false); },
    restart() {
      document.getElementById('fm-confirm-title').textContent = 'Restart this chapter?';
      document.getElementById('fm-confirm-copy').textContent = 'Your progress in this chapter will return to its starting point. Your archive discoveries stay with you.';
      confirmAction = () => { hide(); bridge.restart(); };
      openFromPause('confirm');
    },
    newTitle() { hasRun = false; stack = []; show('main', false); },
    markRun() { hasRun = true; },
    closeForDebug() { hide(); },
    diagnostics() { return bridge.diagnostics(); },
    syncMute(value) { settings.muted = value; save(); }
  };
}
