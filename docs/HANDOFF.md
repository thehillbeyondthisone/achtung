# U-505: Boarding Party — development handoff

Updated 21 November 2026.

This handoff reflects the current game, the session notes, and the November 17 accuracy review. The original external design handoff remains unavailable. See the evidence review below for source disagreements and open questions.

## Current build

The simulation, story, and rendering/input module are in `index.html`; `ui/menus.js` and `ui/menus.css` provide the menu system. The game uses Three.js 0.160.0 from jsDelivr through an import map, inline JSON data, a DOM-independent simulation (`<script id="sim">`), and a DOM-independent act controller (`<script id="act">`). Run it from the local Node preview without installing packages or building assets.

The splash screen leads to the main menu. Choose **Begin operation** for the mission briefing, then **Board U-505** or **Watch the approach**. **Select chapter** offers all four chapters at reconstructed checkpoints: approach, boarding, salvage, and the 7 June rescue. The main menu also provides a service record and field manual. Pause includes settings, chapter restart, and a return to the main menu; an active operation can be resumed while the game remains open. Audio, render quality, brightness, field of view, mouse controls, reduced motion, captions, and control hints are configurable in Settings.

| Stage | Implemented behavior |
| --- | --- |
| Act 1, 11:09–11:35, 4 June | Choose **Watch the approach** in the mission briefing, or select Chapter I, to spend about 150 seconds on Pillsbury's deck. The camera tightens as U-505 surfaces, with a layered wake, spray, and animated swell. Framing and distance are staged. The captions paraphrase the reports and display GCT. Enter skips to boarding. |
| Act 2, 11:46–12:40 | Choose **Board U-505** to start on the bridge at 11:46. Walk to the hatch and press F to descend. Chapter II and loss retries start below deck at 11:46. On-screen orders lead from the strainer cover to the diesel levers and the flood valve when enabled. Press F at the ladder to climb out, then F on deck to wait for salvage. E at the bridge hatch returns below. The notebook shows the current order and optional work. |
| Act 3, 12:40–14:23 | Carries over the water and hatch states from Act 2. Use the flood survey to choose a flooded room and locate its intake. Take a handy-billy from the foot of the ladder and connect it at that fitting. Aim at the control-room ladder and press F to climb out and see the painted waterline bands. Press F on deck to fast-forward to the tow. The debrief shows recorded water for one decision and lets you scrub the cutaway or continue to 7 June. |
| Act 4 | From the tow debrief, continue directly to the 7 June rescue or watch the tow-wire break and Gallery's 5 June inspection first. The rescue uses electric submersibles powered by Abnaki. Climb out onto the same deck and hand off after rigging at least one pump. The crew redirects idle intakes during the recovery. The portable pump count, initial water, timing, recovery target, and intake handoff are game assumptions. The story ends at Bermuda on 19 June. |
| Final screen | The run compared row by row with the historical account, plus codex completion. R restarts the story. |

The notebook (G) pauses play and contains orders, glossary, and 25 codex entries with evidence labels. Source links open downloaded reports when available. The generated assumptions list covers 60 flagged records, including mixed field statuses such as item weights and positions. Remaining source gaps are marked in the notebook.

## Run and test

Run from the project root:

```powershell
node tools/simcheck.mjs
node tools/evidencecheck.mjs
node tools/serve.mjs
```

Open `http://127.0.0.1:8505/`. The `u505` launch configuration runs the same server. The browser needs access to jsDelivr for Three.js.

The optional menu browser suite runs with `node tools/menucheck.mjs`. It requires `playwright-core` and Chrome (or Playwright Chromium); use `MENU_PLAYWRIGHT` and `MENU_CHROME` to override their locations. It starts its own local preview and checks menu navigation, working and persisted settings, pause/resume behavior, and responsive layouts. Preview, simulation, and evidence checks do not require these browser-testing dependencies.

Add `?water-demo=1` to open the interactive water demo. The scene buttons open the diesel strainer, motor-room hatch, awash deck, surfacing, tow, and turbulence basin. Use `?water-demo=hatch`, `?water-demo=deck`, `?water-demo=surfacing`, `?water-demo=tow`, or `?water-demo=turbulence` to open those scenes directly. The two exterior shots loop. Click the view or press Enter to replay either shot.

**Developer controls** exposes the simulation clock (paused through 240×), flood presets, strainer opening, motor-room hatch, and swell. The tow uses live simulated trim and draught. Surfacing uses a staged rise with adjustable swell. Presets rebuild the selected scene from model inputs, and **Reset scene** reloads the current preset. Use the motor-room hatch view and set 60× for a quick pump drawdown check. Demo notebook activity stays in the tab.

**Turbulence** is a separate surface-wave test basin. Choose a continuous jet, moving wake, or pulse only. Click the water to place a pulse or use **Pulse at center** for a repeatable input. Adjust strength and damping, switch between shaded water and the motion heatmap, and read peak displacement and RMS vertical speed. P or **Pause basin** freezes the test. **Reset basin** clears the water and foam while keeping the settings and run state. The campaign still uses its own fixed-step flooding model.

Click the canvas for mouse look and audio. If pointer lock is refused, hold the left mouse button and drag to look. Move with WASD and hold left Shift to run. E interacts and F performs the alternate action where shown. G opens the notebook, M mutes, and P pauses. Resume with P, Enter, or the Resume button. R retries or restarts from the loss and final screens. The debug panel starts hidden and opens with backquote, F3, or `?debug=1` on load.

Saved notebook progress uses localStorage keys `u505.glossary` and `u505.codex`. Settings use `u505.settings.v1`. The active operation resumes exactly while the tab is open. After reload, `u505.operation.v1` holds the latest campaign checkpoint on that origin. Chapter selection and debug jumps use reconstructed starts. To reproduce first-time unlocks, use a fresh browser profile.

The debug panel has two Act 3 jumps, **water aft** and **diesel pocket**. Both replay Act 2 from 11:46 through the normal handoff. The diesel-pocket route shuts the motor-room hatch before capping the strainer. The **awash** jump opens 7 June. Press E to handle pumps below. Press F at the ladder to climb out. On deck, walk with WASD and press F to start or stop fast-forward. On 7 June, the first successful F on deck hands off to the crew. Press E near the hatch to return below. Enter or click skips the tow scene.

### Verification status

**21 November interior pass.** Blender re-imported nine assemblies with 67,712 triangles. Focused Chrome at 1440 × 900 on an RTX 4060 reached the motor room on the same boarding walk in both builds. The 95th-percentile frame interval was about 18 ms in each. Both salvage checkpoints and the 7 June pump handoff passed with the new art. Captured full-volume browser audio stayed below clipping.

**18 November jam browser pass:** opened the actual build on a fresh local origin in a new foreground Chrome window. A native click captured the mouse; Escape released it and opened Pause. An embedded pass deliberately refused capture and verified drag look, release, and movement. A browser-delivered R retried a real loss screen. The detailed GLB loaded as 10 meshes / 79,434 triangles with two textured meshes, rendered in surfacing, tow and on the playable deck, and E returned below. The explicit `?boatart=0` fallback also rendered. No model-loading or shader blocker was observed.

Fixed missing campaign approach/tow sea ambience and interior audio leaking behind restart/interstitial cards. The approach now updates the audio mixer every frame; exterior shots select sea ambience, and cards silence both sea and interior channels. WebAudio output was measured in the browser: nonzero, unclipped boarding and exterior samples; mute, Pause and notebook output settled to silence and resumed correctly. This verifies the signal path, not listening quality through the user's speakers.

Open `tools/jamcheck.html` through `tools/serve.mjs` and click **Run browser checks** for the repeatable 19-check suite. It loads the shipped game and models and uses debug hooks for scenario setup. It covers embedded input, water and machinery cues, both Blender models, UV and normal checks, the deck hatch loop, Act 2/3/7 June loss and retry, checkpoint water and hatches, the tow, and a silent restart title. `__u505.audio.output()` supplies a lazy analyser tap for QA and never starts or unmutes audio. A continuous campaign playthrough and subjective listening remain open.

All 32 flooding checks, two turbulence checks, and the evidence checker pass. The evidence checker covers the 25 codex entries, 60 assumptions, and local links. The simulation checks exercise extracted logic and include the two Act 3 routes with and without placeholders.

Representative current results:

- Act 3 after the paced Act 2: hatches and pumps reach the tow with 41.0 t reserve; doing nothing reaches it with 8.1 t. Idling does not sink her: the aft room reaches the outside waterline and the seep stops.
- With the default placeholders, pumping the stern and motor rooms yields 42.8 t reserve versus 17.3 t when the first pump is aimed at the dry diesel room. With the isolated diesel pocket, pumping that intake and the stern leaves 1.8 t in the diesel room versus 25.3 t when both pumps draw from farther aft.
- The 7 June scene starts with 4.9 t reserve. With no pumps it is lost after 0.6 simulated hours. Pumps rigged at +8, +16, and +24 simulated minutes win after 4.8 hours.
- Rigging in a dry compartment is refused, and the pump stays in hand. The 27-check suite now covers all six placements across the three aft rooms with their hatches open, including the route that dries the last room before its pump arrives. Deck support also recovers with one pump and is unavailable before any pump is rigged.
- Chrome deck checks covered climbing out and back, blocking movement into flooded sections, walking during fast-forward, pausing the clock with the notebook, and reaching the tow. The 7 June check reached Bermuda after rigging one pump and handing off from the deck.

In Chrome, Enter advanced the opening cards, a held W crossed a hatch, and the drag-to-look fallback moved the camera when pointer lock was refused. Pause and notebook reading froze the clock at 11:46. The notebook opened the local communications log from the Node preview. Earlier console-driven traversal reached the final comparison and restarted. Audio gain and small-preview performance measurements are recorded in `HISTORY.md`.

The visual pass was checked in Chrome at 1538 × 881. The deck sequence showed the plumes, surfaced hull, wake, and timed caption. The boarding transition, control room, flooded diesel space, and 7 June aft room were also inspected. The interior uses room-specific lamp colours, illuminated hatch landmarks, and a water surface that follows the hull at steep trim.

The control room, diesel room, electric-motor room, and aft torpedo passage load the new Blender interior. Their live controls and collision use the existing game layout. Signed hatch flow, strainer spray and wading disturbances drive the water effects. Caged practicals and hatch daylight drive both surface lighting and water reflections. The audio mix separates machine, water, and interaction sounds. [Interior sources and rebuild instructions](INTERIOR.md)

Chrome checks at 1837 × 881 covered the boarding view, the steep-trim 7 June view, looking and walking in the aisle, and using the port diesel stop lever through normal input. The new debug **Review room looking aft** and **Measure room render cost** controls expose the existing review/benchmark hooks. Sampled diesel views used 141–147 draws and about 21,000 triangles. Thirty synchronous renders with a readback measured 7.25–8.82 ms/render; this is a rough render-cost measure, not foreground gameplay FPS. Programs stayed at 21 through control-room/diesel-room revisits. The four-light pool is unchanged; no shadow-map passes were added. The browser also logged a messaging-connection error, with no shader compilation errors observed. Continuous foreground pacing and audio listening remain open.

An earlier browser run reached Bermuda using drag-to-look and keyboard controls, with the opening skipped. The Act 3 prototype was checked in a 1538 × 881 Chrome viewport using both handoffs. Browser checks covered survey text, pump pickup and connection, dry-intake refusal, recovery, hatch traversal, retry, deck wait, the two tow compositions, pause, reduced motion, skip, and the transition into Act 4. A first-time playtest, native pointer lock, full-size frame timings, and sound judged by ear remain open.

## Code map and invariants

- Inline data blocks: timeline, compartments, systems, scenario, items, charges, act1, act2, act3, epilogue, codex, glossary. Search their `data-*` IDs.
- `U505Sim.create(data, opts)` supplies the flooding model and plain-JSON `sim.s` state. Fixed step: 10 Hz. `sim.startFrom()` supports the 7 June setup; `sim.setClockBase()` changes clock origin. `reset()` restores the original clock, so do not cache `sim.t0` across resets.
- `U505Act.create(sim, data, opts)` controls Act 2/3. Key methods include `beginAct3()`, `takePump()`, and `rigPump()`. `U505Act.awash(sim, data)` controls 7 June.
- Story orchestration is in the module through `story.act` 1–5, `showCard()`, `restartStage()`, and `jump()`. Act 1, the playable U-505 deck, and the tow scene share the exterior renderer. The playable deck follows the Blender model: `deckLayout` in the exterior block ports its deck sheer, width and camber, tower plan and platform heights. There are three levels: weather deck, lower Wintergarten and bridge with the upper platform. The two platforms are joined by walk-on ladders. Between the deck and the tower, the player presses E at a ladder's foot or top ("[E] Climb up the ladder"). It refuses if the landing is under water. Collision covers the tower, guns, periscope standards, hatches and bitts. The player climbs out onto the bridge beside the hatch. Two accesses are gameplay fittings, not from the photographs. The first is the side ladders from the upper platform down to the deck walkway at x −2.5. The second is the rungs up the fairwater and over the bulwark at x 2.6. At the game's 21–23° stern-down trims the aft rungs land in the sea; these keep the dry forward deck reachable, and the forward rungs keep the route back to the hatch open as she settles on 7 June. Exterior trim and waterline follow the simulation.
- Debug console: `__u505.jump('act1'|'surfacing'|'act2'|'act3'|'gallery'|'awash'|'bermuda'|'final')`, `tick(dt)`, `aim(x,z,side)`, `dismissIntro()`, `view(compartmentId)`, `stats()`, `bench(compartmentId)`, and `audio.levels()`. The debug panel's `surfacing` button opens a view of the boat just after it clears the water.
- Simulation coordinates use positive x toward the bow and z above the pressure hull's inside bottom. Three.js X is starboard, Y up, and Z aft. Positive trim is stern down and positive heel is starboard down.
- Keep valve fractions (`sim.s.valve`) separate from the existing `doorOpen`, `sourceOpen`, and `drainOpen` booleans. A line's valve list gates its area by the smallest opening.
- Cap incoming flow by compartment room; clamping water after the fact loses mass and can prevent sinking. Keep `sim.s` JSON-cloneable for forecasts.
- Preserve the hypothetical calibration check when changing lift, strainer discharge, or sources. Strainer Cd 0.38 and lift-max factor 1.0 are model choices. The early propulsion-stop check covers survival with positive reserve on that route. A separate test covers the increased hazard of stopping propulsion with the inflow still open.
- Keep the fixed `lampPool`; changing light counts as compartments show/hide recompiles shaders. Shared cached materials must not be mutated for a single prop; create a separate material for changing effects.
- The `lambert()` helper now returns cached Phong surface materials. Shared generated colour/normal tiles cover paint, steel, brass, wood, cloth, rubber and water. `metricUV()` supplies physical texture scale and instance UV axes. `applyRoomSurface()` creates cached compartment variants for the wet-plane shader, including rebuilt pump meshes. Preserve Basic materials and their original UVs for labels, gauges, lamps and effects. `prepareBoatSurfaces()` runs once before the first scene. Polished round fittings use smooth geometric normals; painted structure stays faceted.
- A background preview throttles animation frames. Console stepping is useful for debugging, but a foreground browser is required for the outstanding playtest.

## Decisions already made

- Full day plus epilogue is the first-release scope.
- Low-poly interiors with strong light and impressionistic detail.
- Scuttling valve and two charge placeholders are on by default. They are labeled as invented and `?placeholders=0` removes them. Sim physics checks use the base boat, while act checks use the shipped placeholders.
- Mishandling the ballast vents stays lethal. The check that opening every vent loses the boat within three minutes guards this user decision.
- The capture and people are historical. The player's role, route, and some timing are adapted for play. Use sourced attribution for any future dialogue.
- Keep U-505 unmarked and portray the crew as sailors following orders. The killed sailor is mentioned in the account. The searchable suspicious objects are invented and harmless.
- State belongs on in-world gauges, with a separate debug overlay. Act 3 uses reserve buoyancy and avoids an invented threat.

## Accuracy review and sources

The first review compared all 25 codex entries and the game data with the downloaded TG 22.3 report, its enclosures, and Report 2G-9C. Museum sources supplement later history. [Offline source index](SOURCES.md)

- The game uses GCT on 4 June. Pillsbury and Escort Division Four place first boarding at 11:46, with 11:43 in the chronology. The player's immediate descent is compressed. Pillsbury logs the later engineering-space damage at 13:10 and reports power cut at about 13:18. The 11:50 repair and noon propulsion stop remain a hypothetical calibration sequence. [Timeline audit](accuracy/TIMELINE-AUDIT.md)
- The tow ran from Guadalcanal's stern to U-505's bow. Gallery inspected the boat later on 5 June after the dawn retow. The 7 June model portrays pumping. The documented recovery also used ballast blows, weight removal, and headway.
- Report 2G-9C supports broad layout, pump and valve systems, and the nine-cylinder diesel count. Much baseline data describes IXC40 boats. The game's flooding geometry, door and drain behavior, pump rates, reserve and lift are models. The observed six-inch stream provides a basis for the modeled opening. The actual bore and discharge coefficient remain unresolved. [Technical audit](accuracy/TECHNICAL-AUDIT.md)
- The strainer details, initial state of the boat's own pump power, exact charge positions and count, pump counts, German labels, and the Skizzenbuch plates need further evidence. The game labels or discloses these limits. [Codex audit](accuracy/CODEX-AUDIT.md)

## Release preparation

### Whole-boat surface pass, UVs and normals

All eight compartments now share the diesel benchmark's surface treatment. Accommodation gains locker panels, handles, berth framing and bedding straps; the galley gains an oven face, controls, sink rim and faucet; the control room gains periscope collars, wheel spokes and ladder hardware. Motors gain cooling ribs, end bells, terminal boxes and framed instrument faces. Torpedo spaces gain reload bands, supports, breech clamps and hinges. Deck edging, pipe couplings, contact shade, hatch fasteners and the moving water treatment are shared across the interior. The playable exterior uses the same surface tiles, plus casing slots, deck fasteners, seams and rail feet. Exact fitting placements and the decorative motor instrument faces remain artistic dressing.

Before this pass, primitives had native generated UVs/normals and the water relied on flat-shader face normals; there was no dedicated UV/normal-map pass. There are now generated metric UVs with instance-scale correction and seamless procedural tangent-space normal maps. These are not an authored atlas or a high-poly normal bake. Interior water winding now faces upward and its UVs and geometric normals update with the flood mesh, including valid fallback normals at pinched hull intersections. Ocean normals update with the swell. Normal maps add small surface detail without smoothing away the hull's low-poly shape.

The debug **Audit UVs and normals** button validates UV/normal attribute counts, finite UVs and unit normals across the live interior and exterior. Boarding: 729 unique geometries / 773 normal-mapped meshes / zero issues. Act 3 with rebuilt pumps: 735 / 779 / zero issues. The steep-trim 7 June scene: 738 / 782 / zero issues. These checks do not prove a distortion-free authored unwrap; inspect the saved views as well. [Quarters](visuals/quarters.jpg) · [Galley](visuals/galley.jpg) · [Control room](visuals/control-room.jpg) · [Motor room](visuals/motor-room.jpg) · [Deck](visuals/deck.jpg)

Chrome review covered all eight rooms, rebuilt pumps in both salvage setups, 7 June's high trim, the playable deck, and returning below. Sampled 1837 × 881 room render/readback timings ranged from 2.16–11.19 ms, with the control-room sample reaching 275 draws and about 35,000 triangles. After the first exterior visit, programs settled at 24 and remained at 24 on motor/control revisits. No shader errors were observed; the existing browser messaging-connection error appeared again. These are synchronous render measurements, not continuous foreground FPS. All 31 simulation checks and the evidence checker pass.

- Stage the static browser release with `node tools/stage-release.mjs`. The staged build includes local renderer dependencies, both game models, and online notebook citations. Development uses the downloaded research archive when available. [Release instructions](RELEASE.md)
- The fixed pump prompt distinguishes the scene's power assumption from the record. Lange describes an electrical blackout during the attack. Pillsbury reports David stopping the boat, and the Navy's ship history places use of the boat's own pumps after recharging under tow. The evidence leaves the fixed pump's serviceability at first boarding open. [Lange statement](sources/tg-22-3/U-505LangeStatement.htm) · [Pillsbury report](sources/tg-22-3/U-505Pillsbury%20Report.htm) · [USS Guadalcanal ship history](https://www.history.navy.mil/research/histories/ship-histories/danfs/g/guadalcanal-i.html)
- The first-time player test was skipped by request. Full foreground pacing, listening by ear, and frame timing remain open.

## Astra features

| Feature | Where to see it |
| --- | --- |
| **Cutaway replay** | Opens automatically at the tow. Scrub water aboard, reserve buoyancy, and trim. Jump straight to the leak repair, the first handy-billy connection, or the tow. The final screen also offers **Review your run in cutaway**. |
| **Hatch and pump audio** | Approach a hatch with standing water beyond it. Opening it raises the volume and restores high frequencies. A pump drawing air sounds different and shows an amber flag. |
| **Stern tide mark** | Look aft on deck for the four gold bands on the casing fitting. The sea reveals the bands as the stern rises. |
| **Peak flood marks** | Look beside the bulkhead openings after pumping. The wet band records the peak from the current scene, including the boarding state carried into Act 3. |
| **Plumb cord** | Look up beside the control-room ladder. The cord hangs vertically as the boat pitches, and a shadow crosses the ladder rungs. |
| **Traceable pump hoses** | Follow single or double wraps from the control-room suction junction to the connected aft rooms in Act 3. The hose routing depicts the modeled intake connections. |
| **Daylight wash** | Look down from the foot of the ladder on 7 June. Swell and the boat's trim and draught modulate the daylight at the stylized interior hatch opening. |

See [HISTORY.md](../HISTORY.md) for the dated implementation log. The older `.claude` notes preserve earlier session context.
