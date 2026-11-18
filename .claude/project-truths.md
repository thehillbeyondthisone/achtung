# Project truths (verified)

## What this is
- U-505: Boarding Party. A single-file Three.js web game about the 4 June 1944 capture of U-505, played from the boarding party's side. The design spec is the user's handoff doc (not in the repo); `HISTORY.md` at the repo root is the running log.
- `docs/HANDOFF.md` is a reconstructed development handoff, not the missing original design spec. `docs/SOURCES.md` indexes the local TG 22.3 report/enclosures and Report 2G-9C retrieved on 17 November 2026, with completeness limits and manifests. Use these local copies for the pending accuracy review.

## Layout
- `index.html`: everything. JSON data blocks (`data-timeline`, `data-compartments`, `data-systems`, `data-scenario`, `data-glossary`), then `<script id="sim">` (plain script, no DOM), then the Three.js module.
- Systems graph: `sim.s.valve[]` holds opening fractions (0..1); a source's or drain's `valves` list gates its area (times the smallest opening). The booleans `doorOpen` / `sourceOpen` (strainer cover off) / `drainOpen` are kept separately; don't merge them, because the tests and debug buttons rely on them.
- `tools/simcheck.mjs`: runs the sim and the act logic under Node by extracting them from `index.html`.
- `<script id="act">` (after the sim): the boarding party's work across Act 2 (phase 2) and Act 3 (phase 3, `act.beginAct3()`); orders, items, pumps, charges, end state, comparison with history. `U505Act.create(sim, data, opts)`. `U505Act.awash(sim, data)` runs the 7 June scene, using `sim.startFrom()`.
- Story flow lives in the module (`story.act` 1–5, `showCard`, `restartStage`, `jump`). Act 1 renders a separate exterior scene with its own lights.
- Data blocks: timeline, compartments, systems, scenario, items, charges, act1, act2, act3, epilogue, codex, glossary.
- `sim.reset()` restores the clock to `sim_start`. The epilogue moves it with `sim.setClockBase()`, so never cache `sim.t0` across a reset.
- Codex links: only URLs actually seen are allowed. Others carry a name with "link pending". Never construct a URL.
- localStorage keys: `u505.glossary` and `u505.codex`. Clear both when testing first-time prompts and unlocks.
- Records with `"placeholder": true` are unsourced stand-ins (the flood valve, two charges). They are in the game by default (user's decision, 2026-11-17). `Sim.create(data, { placeholders: false })` or the page URL `?placeholders=0` leaves them out. simcheck's physics checks use the base boat; the Act 2 checks use the shipped boat.
- Tuning targets come from the record: she survived dead in the water from about noon to the 14:23 tow. Keep the "real day" check passing whenever lift, Cd or sources change.
- Debug hooks: `__u505.tick(dt)` runs one frame including the sim; `__u505.aim(x, z, side)` points the camera at sim coordinates; `__u505.dismissIntro()`.
- Git repo since 2026-11-17, remote `origin` = https://github.com/thehillbeyondthisone/achtung (public), branch `main`. `.gitattributes` forces LF in the working copy (system `core.autocrlf=true` would otherwise rewrite files to CRLF).
- `git` is not on PATH. Use GitHub Desktop's bundled copy: `$env:LOCALAPPDATA\GitHubDesktop\app-3.6.7\resources\app\git\cmd\git.exe` (version folder changes when Desktop updates). Its system config sets `credential.helper=manager`.

## Commands that work
- `node tools/simcheck.mjs` : scenario table plus pass/fail tuning checks. Exit 1 on failure.
- Preview: launch config `u505` (`node tools/serve.mjs` on 8505), then http://127.0.0.1:8505/.
- Blender exterior model (`art/u505_exterior.blend`): rebuild from `tools/blender/u505/`, not by hand. In Blender: `D=r"<repo>\tools\blender\u505\\"; G={'__name__':'u505','D':D}; exec(open(D+'build.py').read(),G); G['build']()` (or `G['build'](['tower'])` for one part).
  - Rendering: `G['load_all']()`, then `G['use_set']('sea'|'studio')` and `G['shoot']('Cam_Hero', path)`.
  - Axes: bow +Y, starboard +X, up +Z, origin at the pressure-hull midpoint and its outside bottom. Surfaced waterline z = 4.30 (estimated).
  - GLB: `exec(open(D+'export_gltf.py').read(),G); G['export_glb'](path, draco=True)`. Verified bow along three.js −Z.
    - For the textured version, first run `exec(open(D+'bake_textures.py').read(),G); G['bake_all'](r'<repo>\art\textures')` after every `build()` (about 2 min), then export with `textured=True`.
    - Save bakes with `Image.save`: `save_render` applies the AgX view transform.
  - Viewer: launch config `u505-glb` (port 8507), then `/tools/glbview.html?file=art/u505_exterior_draco.glb`.
  - In-game model: `G['export_game_glb'](r'<repo>\art\u505_game.glb')` (after `bake_all`).
    - `index.html` loads it in the `exterior` IIFE (`loadBoatArt`) for Act 1, the tow and the walkable deck. `?boatart=0` disables it.
    - Placement: model y = scene waterline in the `uboat` frame − 4.30 (−0.8 in Act 1, −1.55 in the tow); on deck y = −`MODEL_AXIS` (−2.225), fixed to the hull frame.
    - The walkable deck is `deckLayout`, a port of the model's geometry. If you change the model's deck, tower, hatch, ladders or canisters, update `deckLayout` to match. The obstacle list and ladder positions there are copied from tower.py and deck.py.
    - Deck ↔ tower ladders are E actions (`climbs` and `nearClimb`). Walk-on ramps beside the tower don't work on the narrow walkway: they either lift the player or never catch.
    - Test the deck in the real poses: Act 3 is 21.1° stern-down and 7 June starts at 22.6°, so the aft deck is flooded. A level pose hides reachability problems.
    - With the model loaded, shader programs settle at 31.
  - Gotcha: `mesh.materials.clear()` resets every face to slot 0, so read the face slots first.

## Conventions
- Sim coordinates: x along the hull, 0 at the pressure hull midpoint, positive toward the bow. z is height above the inside bottom of the pressure hull. Three.js: X starboard, Y up, Z aft (so three z = -x).
- Trim > 0 is stern down. Heel > 0 is starboard down.
- Every data record has `status`: real, estimated or assumed. Keep that honest; the codex will be built from it.
- Sim state is plain JSON (`sim.s`) so `forecast()` can clone it. Keep it that way.

## Rules from the handoff that bind every session
- The boat, clock and outcome are real; the player and their route are invented, and the codex says so.
- No swastikas anywhere, including the ensign.
- German crew are sailors following orders, not villains. No gore; no gameplay around the dead sailor.
- No booby traps explode. Only a mishandled real demolition charge can.
- State is shown on in-world gauges, not HUD bars (the debug overlay is the exception).
- Real people (David, Lukosius, Trosino, Gallery) are never the player.
- User decision (2026-11-17): mishandling the vents stays lethal (every vent open loses her in about 70 s). The simcheck check "opening every vent loses her within 3 minutes" guards it.

## Gotchas
- A background preview pane throttles requestAnimationFrame. Drive frames with `__u505.tick(dt)` and advance the sim with `__u505.sim.advance(seconds)` when testing from the console.
- Flows into a compartment must be capped by the room left in it (`room()`), or water silently vanishes at the capacity clamp and the boat never sinks.
- uboatarchive.net fails ordinary DNS from this machine. Retrieval works with a public-DNS-verified address and `curl --resolve`, with normal TLS verification. The reports are already in `docs/sources/`. Skizzenbuch plates and rights are still pending.
- The `advisor` tool is available in this environment (session 2 onward); use it per the global rule.
- The player ducks within 0.75 m of a bulkhead, which drops the view. Don't put interactables that close to a hatch.
- Keydown auto-repeat: guard one-shot actions with `!e.repeat`. Hold actions (valves) read `keys.has('KeyE')` per frame, and `__u505.tick()` runs them too.
- Lights: never add lights per compartment. Lights inside groups that show and hide change the light count and recompile every shader at hatches. Use the fixed `lampPool` (moved by `placeLamps()`) and add lamp positions to `lampSpots`. Check with `__u505.stats().programs`. As of milestone 5 it settles at 14: the boat's 13, including the strainer spray once drawn, plus the Act 1 exterior. It should not grow on a second pass. Peak draw calls are about 228.
- Materials: use `lambert(color)`, which is cached and flat-shaded. Canvas plates and gauges need `toneMapped: false`, or ACES dims them. Never mutate a cached material (`.material.color`, `.opacity` and so on): every mesh of that colour shares it. Give anything that changes at runtime its own inline material, as the pump lamp has.
- `__u505.bench(compartmentId)` gives a rough GPU ms per frame. On 2026-11-17 it measured about 2.4 ms in the control room, at 610×608 and DPR 1 in the background pane.
- Audio is procedural (no files) and only starts after a user click (`audio.start()` on the intro and canvas clicks). `__u505.audio.levels()` reads the channel gains for tests.
- Blender via MCP (5.2.2, addon protocol 13; Cycles with OptiX on the RTX 4060):
  - `look` targeted at an empty object gives clipped outline-only images. Aim a camera and use `mode: "camera"`.
  - Decal meshes need Shrinkwrap onto a target whose normals face outward. Check the normals: `recalc_face_normals` can fail on a mesh with degenerate fans.
- Review viewpoints: `__u505.view(compartmentId)` renders a fixed look aft from near the forward end of a compartment and returns draw stats.
