# Project truths (verified)

## What this is
- U-505: Boarding Party. A single-file Three.js web game about the 4 June 1944 capture of U-505, played from the boarding party's side. `HISTORY.md` is the running log. `docs/HANDOFF.md` is a reconstructed handoff; the original design spec is not in the repo.
- `docs/SOURCES.md` indexes the local TG 22.3 report/enclosures and Report 2G-9C (retrieved 17 Nov 2026), with completeness limits and manifests. Use these local copies for accuracy work.

## Layout
- `index.html`: everything. JSON data blocks (timeline, compartments, systems, scenario, items, charges, act1–3, epilogue, codex, glossary), then `<script id="sim">` (plain script, no DOM), then `<script id="act">`, then the Three.js module.
- Systems graph: `sim.s.valve[]` holds opening fractions (0..1); a source's or drain's `valves` list gates its area. The booleans `doorOpen` / `sourceOpen` (strainer cover off) / `drainOpen` stay separate: tests and debug buttons rely on them.
- `<script id="act">`: Act 2 (phase 2) and Act 3 (phase 3, `act.beginAct3()`): orders, items, pumps, charges, end state. `U505Act.create(sim, data, opts)`; `U505Act.awash(sim, data)` runs 7 June via `sim.startFrom()`.
- Story flow lives in the module (`story.act` 1–5, `showCard`, `restartStage`, `jump`). Act 1 renders a separate exterior scene with its own lights.
- `sim.reset()` restores the clock to `sim_start`; the epilogue moves it with `sim.setClockBase()`, so never cache `sim.t0` across a reset.
- Codex entries: `flag` real / simplified / invented; `evidencecheck` requires a `locator` on real ones and known source keys. Only URLs actually seen are allowed; others carry "link pending". Never construct a URL.
- localStorage keys `u505.glossary` and `u505.codex`: clear both when testing first-time prompts and unlocks.
- Placeholders (`"placeholder": true`: the flood valve, two charges) ship by default (user decision 2026-11-17). `Sim.create(data, { placeholders: false })` or `?placeholders=0` removes them. simcheck physics uses the base boat; the Act 2 checks the shipped boat.
- Tuning targets come from the record: she survived dead in the water from about noon to the 14:23 tow. Keep the "real day" check passing whenever lift, Cd or sources change.
- Strainer opening (verified 2026-11-23 by a Node sweep of the shipped sim, placeholders off, cover as the only action, engines running): inflow depends only on Cd × area. Shipped = 69.3 cm² (6 in, Cd 0.38). 8 in at Cd 0.2138 and 11 in at Cd 0.1131 reproduce the shipped results exactly (lost 12:00:29 if idle, last saving cover 11:56:52, 28.7 t at tow with the cover on at 11:46). A cover at 11:46 survives up to about 106 cm² effective; at 11:50, about 89 cm². A literal six-inch stream (≈ 177 cm²) is lost at 11:40:04 even with nobody waiting, so the shipped Cd 0.38 absorbs a gap between the reported stream and the lift model.
- Debug hooks: `__u505.tick(dt)` runs one frame including the sim; `__u505.aim(x, z, side)` points the camera at sim coordinates; `__u505.dismissIntro()`; `__u505.view(id)` renders a fixed look aft in a compartment; `__u505.stats()` gives calls/programs; `__u505.bench(id)` a rough GPU ms per frame; `__u505.lastKnock`, `__u505.flotsam`, `__u505.lights.hand / toggleHand() / handActive`.
- Git repo since 2026-11-17, remote `origin` = https://github.com/thehillbeyondthisone/achtung (public), branch `main`. `.gitattributes` forces LF (system `core.autocrlf=true` would rewrite to CRLF).
- `git` is not on PATH: use `$env:LOCALAPPDATA\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe` (the version folder changes when Desktop updates).

## Menu system
- Theme is CSS-only via `--fm-*` custom properties on `:root` in `ui/menus.css`. All markup lives in `ui/menus.js`. Restyle by changing CSS; menucheck keys on the markup selectors, not on colours or fonts.
- System font stack: Bahnschrift (Windows 10+), DIN Alternate (Mac), fallbacks. No CDN fonts (releasecheck blocks external requests).

## Commands that work
- `node tools/simcheck.mjs` (sim and act tuning checks), `node tools/evidencecheck.mjs` (codex/assumptions), `node tools/menucheck.mjs` (22 browser menu checks), `node tools/releasecheck.mjs` (load with and without models). All exit 1 on failure; all passed 2026-11-24.
- Preview: launch config `u505` (`node tools/serve.mjs` on 8505), then http://localhost:8505/. GLB viewer: config `u505-glb` (8507), `/tools/glbview.html?file=art/u505_exterior_draco.glb`.
- Blender exterior (`art/u505_exterior.blend`): rebuild from `tools/blender/u505/`, never by hand. `D=r"<repo>\tools\blender\u505\\"; G={'__name__':'u505','D':D}; exec(open(D+'build.py').read(),G); G['build']()` (or `G['build'](['tower'])`). Render: `G['load_all']()`, `G['use_set']('sea'|'studio')`, `G['shoot']('Cam_Hero', path)`.
  - Axes: bow +Y, starboard +X, up +Z, origin at pressure-hull midpoint, outside bottom. Surfaced waterline z = 4.30 (estimated).
  - Textures: `exec(open(D+'bake_textures.py').read(),G); G['bake_all'](r'<repo>\art\textures')` after every `build()` (~2 min); save bakes with `Image.save` (`save_render` applies AgX). GLB: `export_gltf.py`, `G['export_glb'](path, draco=True, textured=True)`; in-game `G['export_game_glb'](r'<repo>\art\u505_game.glb')`. Bow exports along three.js −Z.
  - In game: the `exterior` IIFE (`loadBoatArt`) shows it in Act 1, the tow and on deck; `?boatart=0` disables. Placement: model y = scene waterline in the `uboat` frame − 4.30 (−0.8 in Act 1, −1.55 in the tow); on deck y = −`MODEL_AXIS` (−2.225). The walkable deck is `deckLayout`, a port of tower.py/deck.py: change the model's deck, tower, hatch, ladders or canisters and you must update `deckLayout`. Deck ↔ tower ladders are E actions (`climbs`, `nearClimb`); walk-on ramps failed on the narrow walkway.
  - Test the deck in the real poses: Act 3 is 21.1° stern-down and 7 June starts at 22.6°, so the aft deck is flooded.

## Conventions
- Sim coordinates: x along the hull, 0 at the pressure hull midpoint, positive toward the bow; z is height above the inside bottom of the pressure hull. Three.js (boat frame): X starboard, Y up, Z aft, so `toV(x, z, side)` = (side, z − R, −x). Doors: `d.a` is the forward room; `doorQ > 0` flows a → b (aft).
- Trim > 0 is stern down. Heel > 0 is starboard down.
- Every data record has `status`: real, estimated or assumed. Keep that honest; the codex is built from it.
- Sim state is plain JSON (`sim.s`) so `forecast()` can clone it. Visual effects (spills, ripples, flotsam) read it and never write it.
- Sounds described in words (the hatch knock) show only when the sound did not play, and never as a number. `captions` defaults on, so don't gate listening mechanics on it.

## Rules from the handoff that bind every session
- The boat, clock and outcome are real; the player and their route are invented, and the codex says so.
- No swastikas anywhere, including the ensign. German crew are sailors following orders, not villains. No gore; no gameplay around the dead sailor.
- No booby traps explode. Only a mishandled real demolition charge can.
- State is shown on in-world gauges, not HUD bars (the debug overlay is the exception).
- Real people (David, Lukosius, Trosino, Gallery) are never the player.
- User decision (2026-11-17): mishandling the vents stays lethal (every vent open loses her in about 70 s); simcheck guards it.

## Gotchas
- A background preview pane throttles requestAnimationFrame: drive frames with `__u505.tick(dt)` and the sim with `__u505.sim.advance(seconds)`. The game pauses itself when focus or pointer lock goes; keys are ignored while paused (`__u505.resumePlay()`).
- Flows into a compartment must be capped by the room left in it (`room()`), or water vanishes at the capacity clamp.
- uboatarchive.net fails ordinary DNS here; `curl --resolve` with a public-DNS address works. The reports are already in `docs/sources/`. Skizzenbuch plates and rights are pending.
- The player ducks within 0.75 m of a bulkhead. Don't put interactables that close to a hatch.
- Keydown auto-repeat: guard one-shot actions with `!e.repeat`. Hold actions (valves) read `keys.has('KeyE')` per frame.
- Lights: never add, remove or hide lights (the count recompiles every shader). The fixed 4-light `lampPool` is moved by `placeLamps()` from `lampSpots`; with the hand lamp on, fixtures get `slots = 3` and `placeHandLamp()` fills the last slot. Below deck with both GLBs, programs settle at 38 and peak draw calls ~346 on a bow-to-stern walk, unchanged with the lamp on or off (2026-11-24).
- `boat.localToWorld(v)` / `worldToLocal(v)` mutate `v` in place: copy first if you still need the local vector.
- Bare-metal deck plates in the interior GLB barely respond to spot lights; machinery, racks and the deckhead do.
- Materials: `lambert(color)` is cached; never mutate a cached material. Canvas plates and gauges need `toneMapped: false`. Anything that changes at runtime gets its own material.
- Audio is procedural and starts only after a user click. `__u505.audio.levels()` / `.cues()` read gains and cue counts for tests.
- Blender via MCP (5.2.2, Cycles/OptiX on the RTX 4060): aim a camera and `look` with `mode: "camera"`; decal Shrinkwrap targets need outward normals; `mesh.materials.clear()` resets face slots to 0.
