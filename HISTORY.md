# U-505: Boarding Party — project history

Dated entries of what changed and why. Read this first each session; add an entry at the end of each session.

## 2026-11-16/17 — Session 1: milestone 1 (flooding sim + gray-box hull)

**Built**

- `index.html`: the whole game in one file. Three.js 0.160 comes from jsDelivr through an import map; everything else is inline.
  - Four JSON data blocks: `data-timeline`, `data-compartments`, `data-systems`, `data-scenario`. Every record carries a `status` of real / estimated / assumed.
  - `<script id="sim">`: the flooding simulation. Plain script with no DOM or Three.js, so Node can run it. Fixed 10 Hz step.
  - Module script: gray-box hull of 8 compartments, first-person walking, hatches, the sea strainer, an in-world gauge board (keel depth and trim) in the control room, and a debug overlay.
- `tools/simcheck.mjs`: pulls the data and sim out of `index.html`, runs seven scripted scenarios and fails if the tuning targets are missed.
- `.claude/launch.json`: static server on port 8505 for previewing.

**How the sim works**

- Each compartment is a slice of a 4.4 m cylinder with a taper and permeability. Water volume gives a level; trim tilts every surface.
- Sea openings use `Q = Cd * A * sqrt(2 g h)`, where h is sea level minus the higher of the opening and the water already inside.
- Water moves aft or forward through open hatches (over a sill) and through the bilge drain lines to the control room. A full compartment takes no more.
- Reserve buoyancy = 112 t (1,232 - 1,120) minus water aboard, plus dynamic lift from headway. Trim comes from the water's moment about midships over a longitudinal GM that collapses as reserve buoyancy goes. The boat founders at zero reserve and is lost when the sea reaches the conning tower hatch.

**Tuning result** (clock starts 11:25, player below at 11:40)

- Doing nothing loses the boat at 11:55:23, about 15 minutes after going below.
- At 11:40 she has 49.5 t of reserve left, 2.7° stern-down trim, and 0.9 m of water over the deck plates in the aft torpedo room.
- Capping the strainer at 11:45 or 11:50 keeps her afloat to the 14:23 tow.
- Stopping the engines with the strainer still open loses her at 11:50, five minutes sooner than doing nothing.

**Decisions and why**

- Strainer uses the 6-inch reference case with Cd 0.5 (0.6 reduced for the sea chest and pipe run). This is the main calibration knob. With Cd 0.6 the boat is gone before a boarding party could plausibly reach the strainer.
- Dynamic lift (0.30 t per kn², scaled by trim, up to about 29 t) is the least-grounded number in the model. It is there because the boat is recorded as settling whenever she lost way. It makes "stop the diesels" a real trade-off.
- Aft depth-charge damage is modelled as 8 t already aboard plus a 20 mm seep. The flooding is recorded; the size is not.
- Scuttling valves and demolition charges are not in the sim yet. Their locations are an open question and the handoff says not to invent them.
- All seven bulkheads have the same circular hatch for now.

**Not done / not verified**

- uboatarchive.net did not resolve from this machine (fetch tool, Chrome and DNS lookup all failed), so none of the source-dependent open questions were settled and the timeline block has no page references.
- Mouse look under pointer lock was not exercised: the preview pane was in the background, so frames were driven through `__u505.tick()`. Walking, hatches, the strainer, the debug buttons and the loss banner were checked that way.
- No sound, no art, no codex, no items, no glossary. Those are milestones 2 to 5.

**Open questions** (from the handoff; none closed this session)

1. Strainer size: 6-inch stream vs 8-inch strainer vs 11-inch pipe. Using 6 inches.
2. First boarding party: eight or nine men.
3. First name of the sailor killed. A search found NHHC and others giving Gottfried Fischer; not checked against Enclosure E.
4. Locations of demolition charges and scuttling valves.
5. Time basis for the in-game clock. Using report times as written.
6. Scope of first release. The build order (Act 2 first) works for either answer.
7. Art direction. Gray box is neutral; low-poly is assumed until decided.
8. Rights for Skizzenbuch plates and MSI photography.
9. Title. Working title kept.

## 2026-11-17 — Session 2: milestone 2 (systems graph, labels, glossary)

**Built**

- **Valves** (`valves` in `data-systems`): each is an opening fraction in `sim.s.valve[]`, 1 = open. A source's or drain's flow area is its area times the smallest opening of the valves on its `valves` list. The old booleans (`doorOpen`, `sourceOpen` = strainer cover off, `drainOpen`) are unchanged, so milestone 1 behaviour and tests are untouched.
  - Hull stop valve (Außenbordventil Kühlwasser) on the cooling-water line ahead of the strainer: 8 turns at 1 turn/s. A second way to stop the jet, slower than the cover but it cuts the flow as you turn.
  - Four bilge valves (Lenzventil …) on a manifold (Lenzverteiler) in the control room, one per drain line.
  - Three vents (Entlüftung vorn / Mitte / achtern) as levers and three blow valves (Anblaseventil …) on a blowing manifold, with a compressed-air gauge (PRESSLUFT kg/cm²).
- **Main ballast tanks** in three lumped groups (25 + 62 + 25 t = the 112 t reserve), at x +24 / 0 / -24 m. An open vent lets them fill toward sea level; blowing with the vent shut drives the water out and uses air (more at depth). Ballast now counts in the trim moment as well as reserve buoyancy.
- **The boat's own bilge pump** (Lenzpumpe) in the control room, 1 m³/min from the control-room bilge, only with power. Power starts off.
- **Interaction**:
  - Hold E to turn a wheel while looking at it; it stops when you let go or look away.
  - Vent levers are one throw: a tap runs them to the end stop. A half-open vent behind a "shut" prompt would be lethal.
  - Keydown auto-repeat no longer flips hatches back and forth.
- **Glossary** (`data-glossary`, 20 terms, G to open): a term is added the first time you look at something labelled with it or enter its compartment. Prompts show the German only, until the glossary has been opened after the word was found; then the English appears in brackets. Kept in localStorage.
- **Debug panel**: valve buttons (fully open / shut), tank contents, air, power and pump toggles. Ballast tanks are drawn above the hull in the profile.
- `tools/simcheck.mjs`: six new scenarios and four new checks (ten in all, all pass). The milestone 1 numbers are unchanged.

**Results**

- Turning the hull valve shut from 11:45 saves her, the same as fitting the cover (rb 22.5 t at 14:23).
- Opening every vent at 11:46 loses her at 11:47:14.
- One forward vent opened for a minute, then shut and blown, recovers fully.
  - Air used: 87 m³ of the 250 m³.
  - Most of that bubbled out of the tank after it was already empty, because the blow valve was left open for 2 minutes. Leaving a blow open wastes air, and the player should learn that.
- The forward vent left open alone barely matters at this stern-down trim, because the forward tanks sit above the sea.
- Power plus the boat's own pump from 11:50 ends at rb 50 t.

**Decisions and why**

- Vents are a real system with real consequences, not a booby trap. But "open every vent = gone in about 70 s" is harsh. **It is a design call for the user.**
- Valve positions, turn counts, the three-group tank split, air figures, pump rate and pipe colours are all `assumed`. The pipe palette is explicitly not the Kriegsmarine colour code.
- All German terms are `estimated`. One batch of web searches found nothing to confirm them; Zentrale appears in a search snippet of the uboatarchive diving regulations, but the page could not be read because uboatarchive.net still fails DNS.
- The hull valve was moved aft of the strainer (x -5.65), because near a bulkhead the player ducks and the wheel drops out of view.
- No scuttling valves or demolition charges, and no Act 2 flow. Those wait for sources (scuttling, charges) and milestone 3 (Act 2).

**Open questions added**

10. Was there battery power to run U-505's own pumps on 4 June?
11. How harsh should mishandling the vents be? **Closed 2026-11-17: the user chose to keep it lethal.** Every vent open loses her in about 70 s. Don't soften the tank flood rate.

## 2026-11-17 — Session 2, continued: milestone 3 (Act 2 playable end to end)

**Built**

- **New data blocks:**
  - `data-items`: seven intelligence items with weight, bulk, position, and German and English names.
    - The kinds of item are real.
    - Positions are estimated (the radio room and the commander's corner at the after end of the officers' compartment).
    - Weights are assumed.
  - `data-charges`: one disabled placeholder.
  - `data-act2`: start and end times, intro text, orders, carry limits, a message heard at 12:03, and three suspicious objects (invented, flagged as such).
- **`<script id="act">`**: act logic with no DOM, which Node also runs.
  - It covers orders, picking up and passing up items, the charge steps, the end state, and the comparison with history.
- **Diesel stop levers** (Abstellhebel, port and starboard) in the engine room, built as `fuel` valves.
  - Speed now follows the share of diesels running. `enginesOn` is still the master switch.
  - A stopped diesel can't be restarted.
- **Play loop:**
  - An intro card at 11:40.
  - Orders and what you carry are in the notebook (G), above the glossary.
  - Take items with E. Carrying slows you.
  - Pass items up at the ladder with E.
  - Press E twice at the ladder with empty hands to wait on deck. The sim then runs at ×120 to 12:40, so she can still be lost on the way.
  - The 12:03 news about Pillsbury arrives as a message.
  - The act is won if she is afloat at 12:40.
  - The end screen sets your run against 4 June 1944, using only facts we can source (no counts).
- **Suspicious objects:** hold E for 4 s to check one. Nothing is ever found.
- **Placeholders** (`?placeholders=1` only):
  - A scuttling flood valve in the motor room and a demolition charge in the control room.
  - A charge is disconnected in two steps: hold E to take off the firing lead (Zündleitung), then hold F to take out the detonator (Zünder).
  - Taking the detonator out first sets the charge off. This is the game's only explosion.
- **Other changes:**
  - 16 new glossary terms, 12 used in play. The 4 charge and flood-valve words are tagged `placeholder` and are hidden (and left out of the count) unless placeholders are on.
  - Movement and E/F do nothing while the intro card is up.
  - Officers' bunks moved forward to make room for the radio desk.
  - Refused pointer locks no longer throw errors.
  - The end and intro cards sit above the debug panel.
- **`tools/simcheck.mjs`:** five Act 2 playthroughs and seven new checks (17 in all, all pass).

**Results**

- Cap at 11:45, diesels at 11:47, papers up at 12:00: won at 12:40.
- Diesels first (11:41), strainer at 11:50: lost at 11:49:43, before the strainer is reached.
- Doing nothing: lost at 11:55:23.

**Decisions and why**

- **Scuttling valves and charges ship switched off.** The handoff says to check the KTB, 2G-9C or museum staff before inventing positions, and none can be reached. The mechanism is built and tested, so turning them on only needs positions in data.
- **No lines are scripted for David or other real people.** The intro and messages are neutral.
- **No counts on the end screen.** The "ten sacks, 900 lb, two Enigmas" figures came from an unverified search snippet.
- **Sources still unread.** NHHC refused connections, the Rogers PDF returned 404, and uboatarchive.net fails DNS.

**Open question added**

12. Use placeholder positions for the scuttling valves and charges until sources arrive, or keep them out? **Closed 2026-11-17: the user chose placeholders.**

## 2026-11-17 — Session 2, continued: placeholders in, retune to the record

**Placeholders on by default** (user's decision). Records carry `"placeholder": true` and `status: "placeholder"`; `?placeholders=0` removes them, and so does `Sim.create(data, { placeholders: false })`.
- One opened flood valve (Flutventil): 25 mm, motor room, aft of the motors, open since the start.
- Two demolition charges: control room, and bow torpedo room. The second charge was my addition, so the "charges" order is plural and sends the player forward.
- All positions and sizes are invented. The end screen says the real positions are not yet sourced.

**Retune.** Making the act playable exposed a contradiction. With the old lift, capping the strainer at about 11:50 and then stopping the diesels about noon sank her. On 4 June she lay dead in the water from about noon until the 14:23 tow and stayed up.
- `lift_max_factor` 2.0 → 1.0 (peak lift about 29 t → about 15 t). The coefficient is unchanged.
- Strainer `cd` 0.5 → 0.38. It is still the main calibration knob; the 6-inch diameter is kept.

| | Before | After |
|---|---|---|
| Do nothing | lost 11:55:23 | lost 12:00:29 |
| Reserve at boarding (11:40) | 49.5 t | 63.0 t |
| Strainer flow at boarding | 4.70 t/min | 3.41 t/min |
| Every vent open (11:46) | lost 11:47:14 | lost 11:47:27 |
| Act 2, diesels first (11:41), strainer 11:50 | lost 11:49:43 | won, 6.8 t of reserve (with the flood valve shut at 11:56) |

- Stopping the engines with the strainer open is still worse than doing nothing (lost 11:56:41).
- Do nothing with the placeholders in: lost 11:59.

**Correction to the milestone 3 entry.** Stopping the diesels before capping the strainer no longer loses the boat. It now costs margin: 6.8 t of reserve at 12:40, against 8.1 t the other way round. This fits the record, since the party stopped the diesels and she survived, so it is not retuned back. The base-boat check still holds: stopping the engines with the strainer open is worse than doing nothing.

**Act rule change.** If she has no reserve buoyancy left at 12:40, the act is lost ("too late"), not won. The "too late" end card has been rendered once in the preview.

**simcheck**: the physics checks now run on the base boat (no placeholders); the Act 2 checks run the boat as shipped. New checks, 20 in all, all pass:
- **The real day:** cap 11:50, engines 12:00, hatches 12:40, pump 12:45. Afloat at 14:23 with 20.5 t of reserve.
- **A realistic pace:** cap 11:50, flood valve 11:56, diesels 12:00, charges 12:05, papers 12:20. Won with at least 5 t of reserve.
- **The flood valve left open:** with the diesels stopped, lost at 12:40 (foundering).

**Tuning tool**: grid searches were run from a scratch script, not kept in the repo; `tools/simcheck.mjs` holds the targets.

## 2026-11-17 — Session 2, continued: milestone 4 (art pass: low-poly, strong light)

The user chose **low-poly with strong light**. The interiors are impressionistic, built from the handoff's facts, not from the Skizzenbuch plates or MSI photos (those are reference-only or rights-pending). No flags, eagles, insignia, posters, crew figures or bodies were added.

**Lighting**
- ACES tone mapping and a near-black fog.
- Very low ambient light, so the room is warm pools under caged deckhead lamps with darkness between.
- A cold spotlight comes down the conning-tower hatch.
- **Fixed light pool:** four point lights are moved each frame to the lamps nearest the player, plus the daylight.
  - Before this, the light count changed as compartments showed and hid, which recompiled shaders at hatches: the program count grew 14 → 24 while walking.
  - It now stays at 12 everywhere.
- Plates, gauges and lamp bulbs are left out of tone mapping, so they stay readable.

**Materials**
- One shared, flat-shaded material per colour.
- The hull is an 18-sided shell with a vertex-colour gradient: pale at the deckhead, dark at the bilge.

**Dressing**
- Frames every 0.6 m and deck seams, both instanced.
- Four deckhead pipe runs in the placeholder pipe palette, plus cable trays.
- Caged lamps about every 3 m.
- Hatch coamings with dogs and a handwheel.

**Props**
- Bow room: four tube breeches with doors, reload torpedoes stowed low along both sides, bunks above them, and an overhead loading rail.
- Petty officers' and officers' quarters: two tiers of bunks with lockers, and a curtain at the commander's corner.
- Galley: range, sink and a shelf of tins.
- Control room:
  - two periscope tubes;
  - the planesmen's handwheels under the depth gauges;
  - a rudder-angle dial (Ruderlage) pinned hard to starboard. The jammed rudder is real, and the dial has a new glossary term.
- Diesel room: two engines with a row of cylinder heads, valve gear and exhaust mains. The nine-cylinder count is my estimate.
- Motor room: two motors and switchboards with dials.
- Aft room: two tube breeches, a reload and bunks.

**Water**
- Faceted, flat-shaded Phong on a 12×6 grid, with a small zero-mean chop. It is visual only, and the mean level still comes from the sim.
- Spray particles fly off the top of the strainer jet.

**Sound** (procedural WebAudio; no audio files)
- **Diesels:** a rumble heard through the whole hull. It spins down when both stop levers are pulled.
- **Strainer:** a roar scaled by its flow.
- **Placeholder flood valve:** a gurgle.
- **Wading:** a slosh when moving through water.
- **Lamps:** a faint hum.
- **Hull:** creaks that come more often as reserve buoyancy runs out.
- Sources are panned by bearing, and each closed hatch muffles them.
- Audio starts on the intro click. M mutes.

**Verified**
- simcheck: 20 of 20 pass, sim untouched.
- Browser playthrough with the new art: strainer, hull valve, both levers, flood valve, both charges, all seven items to the ladder, then wait. Won at 12:40, no console errors.
- Audio levels, read through `__u505.audio.levels()`:
  - strainer: 0.69 beside it, 0.01 in the bow room;
  - diesel: 0.38 in the engine room, 0.08 in the bow;
  - diesel after both stop levers: 0.00.
- Draw calls peak at about 228, in the control room and officers' quarters.
- Shader programs settle at 13: 12, plus 1 for the spray.
- Muffling: shutting the control-room/diesel hatch cuts the strainer roar heard in the control room from 0.544 to 0.136.
- Panning: beside the strainer, it pans +0.9 facing forward and −0.9 facing aft.
- Rough GPU frame time (`__u505.bench`): about 2.4 ms in the control room, 1.9 ms in the officers' quarters and 1.6 ms in the diesel room. Measured in the 610×608 background pane at DPR 1; a big window will cost more.
- Fixes after review:
  - The bow placeholder charge moved to x 26.6, clear of the reload torpedo, and was checked from the walkway.
  - The hydroplane handwheels moved out of the walkway.

**Not verified**
- Real-time frame rate in a full-size window.
- Mouse look.
- The sound by ear.

**Open question closed:** 7. Art direction. The user chose low-poly with strong light (2026-11-17).

## 2026-11-17 — Session 2, continued: milestone 5 (the full day, epilogue, codex, comparison)

The user chose the full day plus the epilogue for the first release (open question 6 closed). The game now runs Act 1 → Act 2 → Act 3 → Act 4 → final comparison. R on a lost screen retries the current stage; R on the final screen starts again from the top.

**Act 1** (`data-act1`, non-interactive, about 2.5 minutes)
- **Scene:** a separate exterior scene with its own lights. A low-poly sea with swell, Pillsbury's deck rail, Chatelain as a grey silhouette, and a U-boat with no flag, eagle or number.
- **Timeline:** events from 11:09 to 11:35 run as captions. She surfaces at 11:22:30 and circles. Depth-charge columns rise at 11:21, and gunfire splashes fall from 11:22:30 to 11:27.
- **No radio lines.** Enclosure D, the radio log, is unread; the codex says so ("What the radio said").
- **Controls:** Enter, Space or a click skips to the boarding.

**Act 3** (`data-act3`)
- **Continuity:** Act 3 carries on from the same boat at 12:40. Act 2's win is a card with the comparison table, and nothing is reset.
- **Orders:**
  - shut the hatches abaft the control room (door_5, door_6, door_7);
  - rig the handy-billies;
  - check the charges.
- **Pumps:** two handy-billies, a number that is assumed. Take one at the foot of the ladder, carry it (25 kg, hands full), and press E with nothing targeted to rig it where you stand.
- **Ending:** wait on deck (×240) for the 14:23 tow. A checkpoint is taken at 12:40.
- **"Prepare the tow"** is not invented as a procedure; it is the wait.
- **Measured, not assumed:** doing nothing in Act 3 does not sink her. The after room floods to the outside waterline and the seep stops, so she holds at about 8 t of reserve. The act's stakes are margin and mistakes. simcheck: hatches and pumps reach the tow with 41 t, against 8 t for doing nothing.

**Act 4** (`data-epilogue`)
- **Midnight, 4–5 June:** a card. The tow wire parts.
- **Dawn, 5 June:** a card, then the control room. The rudder dial swings from hard starboard to amidships. The discovery is Gallery's: he isn't scripted, the player doesn't solve it, and the fuse box isn't placed.
- **7 June, playable:** `sim.startFrom()` loads water aft, with the engines off and the hatches aft shut. She starts at 4.9 t of reserve, nearly awash but not lost.
  - Three pumps (assumed) are carried aft at ×6.
  - Once all three are going, time runs at ×900.
  - The goal is 95 t of reserve, full surfaced trim.
  - simcheck: with no pumps she founders after 0.6 h; with three she is back after 4.6 h. The real recovery took until the evening of 8 June; the scene compresses it.
- **Bermuda, 19 June:**
  - Secrecy, and the 58 prisoners held at Camp Ruston and declared dead until 1947.
  - The dead sailor is named only as Fischer.
  - David's Medal of Honor, and the museum.

**Codex** (`data-codex`, 25 entries, in the notebook on G)
- **Unlocks:** entries unlock as you look at things (`touchKeys`) and as the story moves on. They are kept in localStorage `u505.codex`.
- **Flags:** each entry is flagged real, simplified or invented.
- **Links:** only to URLs seen in this session (NHHC, the MSI collection and the MSI capture page). All other sources are named with "link pending".
- **"What this game assumes"** is generated from every data record with status assumed or placeholder.
- **Covers the handoff's required entries:**
  - an invented player;
  - compressed tasks;
  - the invented glossary mechanic;
  - booby traps (real fear, none found);
  - no swastikas;
  - Zschech in one line;
  - placeholder positions;
  - the sim's simplifications and the retune.

**Final screen:** the Act 2, Act 3 and 7 June rows, each set beside what really happened (sourced facts, no counts), plus the codex count.

**Also**
- `sim.setClockBase()` and `sim.startFrom()`. `reset()` restores the clock.
- `act.beginAct3()`, `takePump()` and `rigPump()`.
- `U505Act.awash()`.
- Debug jump buttons: act1, act2, act3 (via a fast paced Act 2), gallery, awash, bermuda, final. The same jumps are hooked to `__u505.jump()`.

**Fixes after review**
- **Pumps:** a pump can't be rigged in a compartment holding under 1 t of water. The prompt says "nothing to pump", and the pump stays in hand.
- **7 June pacing:**
  - It no longer fast-forwards automatically once three pumps are rigged; the player climbs the ladder to wait.
  - A walking-pace run (rigs at +8, +16 and +24 sim-minutes) still wins, in 4.8 h.
- **Card wording:** the Gallery and Abnaki cards were trimmed to the handoff's own words.

**Verified**
- simcheck: 27 of 27 pass.
- Browser, end to end through the hooks, with no console errors:
  - Act 1 captions and surfacing;
  - Act 2 → card → Act 3 (pumps carried and rigged, hatches shut, wait), reaching 14:23 with 45 t of reserve;
  - the epilogue cards and the rudder animation;
  - 7 June with three pumps, back at trim;
  - Bermuda, the final table, and R back to Act 1.
- Shader programs stay at 14 across passes and after returning from Act 1.

**Not verified**
- Mouse look, real-time pacing and the sound by ear.
- Act 1 on a wide screen. The U-boat is small at about 330 m.

**Open questions:** 6 (scope) is closed. Still open:
- power for the boat's own pump (10);
- title (9);
- rights (8);
- the source questions (1–5).

## 2026-11-17 — Source retrieval and development handoff

**Delivered**

- `docs/sources/tg-22-3/`: the hosted TG 22.3 capture report and all 16 enclosure pages linked by U-boat Archive, including the chronology, radio log, boarding lists, prisoner list, track charts, unit reports, photographs, Plan of the Day, and cruise report. Linked chart and image files are preserved for offline reference. The report lists an H(1) night-intentions signal, but the index supplies only H(2); H(1) remains a documented gap.
- `docs/sources/report-2g-9c/`: Portsmouth Naval Shipyard's 1946 Type IXC design study, complete as hosted in its large HTML transcription, plus all 18 referenced images. Much baseline data concerns IXC40 boats, so it must not automatically be applied to U-505.
- `docs/SOURCES.md`: reading links, enclosure map, provenance, completeness limits, and acquisition method. Both report packages include original URLs, byte lengths, and SHA-256 manifests.
- `docs/HANDOFF.md`: a current-state development handoff reconstructed from code, history, session notes, and the user's status. The original externally supplied design document was not present and has not been recovered.
- `tools/fetch-tg22-3.mjs`: bounded, reproducible retrieval of the indexed TG report/enclosures and linked figures.

**Access and limits**

- Normal local DNS lookup still failed, including an ordinary escalated archive fetch. A public DNS-over-HTTPS lookup returned `65.254.227.224`; `curl --resolve` then retrieved the reports with normal HTTPS certificate verification. No hosts-file change was made.
- These are the archive's hosted transcriptions with linked images, not scans of every page in an authenticated original archival packet. No original PDF was located.
- Installed-pump design data does not establish power actually available during capture. Pump power, Skizzenbuch retrieval and rights, MSI photography rights, and the title remain open.
- No game code, tuning, codex claims, or browser saved progress changed. The accuracy review itself is still to do.

**Verification**

- Fresh `node tools/simcheck.mjs` run: all 27 checks pass (exit 0).
- Mouse look, continuous keyboard play, real-time pacing, full-size performance, and sound by ear remain untested.
- The `python` command in the existing preview configuration resolved to an inaccessible Windows app alias in this task; Node was available for the checks.

## 2026-11-17 — Accuracy review and first-run controls

The review checked all 25 codex entries and the game data against the downloaded TG 22.3 report, its enclosures, and Report 2G-9C. The notebook now links to local reports and identifies specific passages. Its generated assumptions list covers 60 records, including geometry, drainage, and item weights. Museum and Navy references support later history and spelling where available. [Codex audit](docs/accuracy/CODEX-AUDIT.md) · [Timeline audit](docs/accuracy/TIMELINE-AUDIT.md) · [Technical audit](docs/accuracy/TECHNICAL-AUDIT.md)

- Act 2 starts at 11:46 GCT, the first-boarding time supported by Pillsbury and Escort Division Four. The chronology gives 11:43. Immediate descent is compressed. The engineering-space damage message uses Pillsbury's 13:10 entry during Act 3.
- The 14:23 tow now runs from Guadalcanal's stern to U-505's bow. Gallery's inspection follows the dawn retow later on 5 June. The 7 June scene uses electric submersibles powered by Abnaki. It retains a modeled pumping objective. The historical salvage parties also blew ballast tanks and removed weight.
- The modeled strainer opening uses the reported six-inch stream. Its discharge coefficient was tuned for play. Actual bore, shipboard pump power, pump counts and rates, and detailed compartment dimensions remain uncertain. The two representative charge placements and separate scuttling valve stay flagged as invented. The Skizzenbuch, title, and image rights remain open.
- The old “real day” check is now a hypothetical calibration scenario. Its noon propulsion stop is earlier than Pillsbury's logged 13:18. With the later playable start, the propulsion-first route can finish with more reserve than the tested alternative. The revised check verifies positive reserve and a win. A separate check still verifies that stopping propulsion with the strainer open can hasten loss.
- The Node preview replaces Python in the launch configuration. Debug starts hidden. P pauses and resumes play, the notebook freezes time, and movement and hold inputs clear on focus loss. Drag-to-look is available when the browser refuses pointer lock.

All 27 simulation checks and the evidence checker passed. In Chrome via the Node preview, keyboard controls advanced the cards, held W crossed a hatch, dragging moved the camera, pause and notebook reading froze the clock, and the notebook opened the local radio log. The complete mouse-and-keyboard route, pointer lock, real-time pacing, and sound by ear remain to be verified.

## 2026-11-17 — Visual presentation and atmosphere

The deck sequence stages a closer view of U-505 as she surfaces and turns. Pillsbury's rail and deck seams establish the foreground. Swell, wake, and spray animate beneath the GCT captions. Distances and camera framing are artistic choices.

Warm accommodation lamps, cooler machinery lighting, and hatch and passage highlights make the interior easier to read. The water mesh follows the hull at high trim and the underwater tint leaves more contrast near the center of the view. The four-light interior pool remains fixed.

Added a surfacing checkpoint to the debug panel and limited the buoyancy forecast to interior play with debug visible. Checked the deck and surfacing captions, boarding transition, control room, flooded machinery space, and 7 June aft room in a 1538 × 881 Chrome viewport. All 27 simulation checks and the evidence checker passed. The complete hands-on route and audio by ear remain open.

## 2026-11-17 — 7 June pump recovery

With the aft hatches open, pumping aft first could dry the final placement room and leave water trapped below the hatch sills. In the reproduced route, reserve buoyancy stabilized at about 92.9 t, below the 95 t target. Players now need to rig at least one pump before waiting on deck. During that wait, the salvage crew redirects idle pump intakes toward standing water. This modeled handoff preserves the installed pump rate and the refusal to place a pump in a dry room.

The strainer's loose cover can now be selected directly from the diesel aisle. A player standing against a closed hatch can open it. Closing still requires stepping clear, with a prompt if the player is too close.

All 27 simulation checks and the evidence checker passed. The 7 June check now covers all six aft-room placement orders with the hatches open. It also covers a one-pump recovery, dry placement retaining the carried pump, and deck support staying unavailable until a pump is rigged.

In Chrome, the normal-input run reached the Bermuda card and final comparison. It began on Pillsbury and used the built-in Enter skip for the rest of the opening. The player selected the loose cover, ran both Act 3 pumps, opened the closed diesel hatch from its sill on 7 June, rigged one electric pump, and handed off at the ladder with two pumps unused. The final table reported 26 t reserve at 12:40, 47 t at 14:23, and 12.6 modeled hours to the 7 June target. This run used mouse drag and keyboard controls throughout the playable acts. Native pointer lock, listening, and normal foreground pacing remain open.

## 2026-11-17 — Act 3 salvage prototype and tow scene

Act 2's motor-room hatch choice now sets up two salvage problems through the existing flooding model. Leaving it open lets the diesel room drain aft. Shutting it early traps about 25 t in the diesel room. The control-room survey and the notebook show room water, trends, and hatch states. The player can connect and recover the two handy-billies at three labeled intakes staged clear of the deepest water. The modeled hose connections are disclosed in the codex. Retry restores the original handoff.

Act 3 uses amber and blue-green lighting, wet hatch highlights, and ripples at working intakes. At 14:23, an eight-second camera move reveals Guadalcanal taking the tow. U-505's profile reflects the run's trim and draught. The debrief displays remaining diesel-room water beside reserve buoyancy.

All 31 simulation checks and the evidence checker passed. Chrome checks covered both handoffs, pump interactions, retry, strong and close tow framings, and the cutscene controls through the Act 4 transition. First-time player testing remains open.

## 2026-11-17 — Playable U-505 deck

The control-room ladder now leads to a shared playable bridge and weather deck in Act 3 and on 7 June. The hull, stairs, rails, and waterline move with the simulated trim and draught. Water can wash over the aft section and cut off the walk down, with the submerged casing still visible through the sea.

F climbs out at the ladder. On deck it starts or stops fast-forward, and E near the hatch returns below. On 7 June the first successful F on deck hands off to the salvage crew after the player rigs an electric pump. Abnaki is visible off starboard. The crew continues to redirect idle intakes after handoff.

Chrome checks reached the Act 3 tow and Bermuda on 7 June. They covered movement during the wait, the wet stern boundary, return through the hatch, notebook pause, and the one-pump handoff requirement. The 31 simulation checks and evidence check passed.

## 2026-11-17 — First-release priorities and Astra ideas

The [development handoff](docs/HANDOFF.md) orders the remaining work around a first-time salvage test, a full foreground playthrough, and release preparation. Its initial Astra stretch list records five proposed additions, led by a replay of the player's flooding history in cutaway.

## 2026-11-17 — Astra features and public preview preparation

Added a cutaway of the player's boarding-to-tow record, with hatch and pump events and access from both debriefs. Hatch audio changes with the opening and water beyond it. Portable pumps gain wet and dry audio and visual feedback. The interior now shows peak flood marks, a vertical plumb cord by the ladder, and wrapped hoses for the modeled Act 3 intake connections. Aft deck paint bands reveal the boat's rising stern. On 7 June the modeled swell modulates the daylight pool beneath the hatch.

Kept U-505: Boarding Party as the release title and added online-only notebook source links for a single-file public preview. The Lenzpumpe prompt identifies its lack of power as the scene's assumption. First-time playtesting was skipped by request.

All 31 simulation checks and the evidence checker passed. Automated Chrome checks exercised both cutaway entry points, actual hatch and pump events, both wrapped hoses, wet marks and the ladder shadow, submerged and exposed stern bands, and the change in daylight as the boat rises. The public preview notebook used external source links. The browser check measured audio channel levels and used drag-to-look for the mouse check. Listening by ear and a continuous foreground run remain open.

## 2026-11-17 — Diesel-room visual benchmark

Replaced the two plain engine blocks with stepped crankcases, nine cylinder assemblies per engine, gasket seams, rocker covers, inspection doors and bolts, bent fuel lines, exhaust branches and flanges, front timing housings, and rubber service loops. Added grated aisle treads, machined edge strips, restrained oil streaks, and soft contact shade beneath the engine beds. The machinery remains an impressionistic interpretation rather than a verified installation reconstruction.

Painted steel, machined steel, iron, brass, and rubber now have separate flat-shaded Phong responses in this room. A shared shader treatment follows the simulated flood plane in boat coordinates, darkening submerged surfaces and leaving a narrow damp fringe. The diesel water material has a sharper specular response, broken lamp glints follow the reflected light positions, and expanding rings mark the strainer's water impact. Physics, controls, collision widths, data records, and the four-light pool are unchanged. Repeated fittings are instanced; no shadow-map passes or external assets were introduced.

Added debug controls for the existing aft-facing review viewpoint and 30-render benchmark, with draw, triangle, program, resolution, and timing readouts. In Chrome at 1837 × 881, sampled diesel views used 141–147 draws and approximately 21,000 triangles. Synchronous render/readback measurements ranged from 7.25 to 8.82 ms/render; these are not gameplay frame-rate measurements. Shader count stayed at 21 across control/diesel revisits. Checked the boarding and steep-trim 7 June views, drag-to-look and aisle movement, and the port diesel stop lever through normal keyboard input. No shader compilation errors were observed; the browser logged a messaging-connection error during the session. [Saved benchmark view](docs/visuals/diesel-room.jpg).

All 31 simulation checks and the evidence checker pass. Full foreground pacing, sound by ear, and the remaining rooms' material/detail passes are still open.

## 2026-11-17 — Whole-boat surfaces, fittings, UVs and normals

Extended the diesel-room treatment to the other seven compartments, shared hatch hardware and the exposed deck. Added batched locker faces and handles, berth frames and straps, galley range and sink details, periscope collars, diving-wheel spokes, ladder feet and rung edges, motor cooling ribs and end bells, instrument faces, reload supports and bands, and breech/hatch fasteners. Added contact shade beneath major furniture and machinery, pipe couplings and deck edging. The weather deck gains casing slots, plank fasteners, seams and rail feet. These are impressionistic fittings, not newly verified historical installation details. Physics, interaction volumes, narrative data and the fixed light pool are unchanged.

The shared `lambert()` helper now supplies Phong materials with separate paint, metal, brass, wood, cloth and rubber responses. Small seamless colour and tangent-space normal tiles are generated in the file. Native primitive UVs were present before; this pass adds metric UV projection, including instance-scale correction. Polished round fittings use smooth normals while painted structure remains faceted. The normal tiles are procedural surface detail, not a high-poly bake, and no authored UV atlas has been created. Readable labels, gauges and lamp faces retain their Basic materials and original UVs.

Wet darkening now follows each compartment's simulated flood plane, including pumps rebuilt during salvage. Reflected lamp glints cover all rooms. Interior water now has explicit UVs, upward triangle winding, updated geometric normals and fallback normals at collapsed boundary rows. The ocean updates its normals with the swell. Initial browser inspection prompted a subtler cloth/paint normal strength and corrected motor-gauge surrounds.

Added a debug UV/normal audit. The boarding scene passed with 729 unique geometries and 773 normal-mapped meshes. Rebuilt Act 3 pumps passed with 735 / 779; steep-trim 7 June passed with 738 / 782. No missing/mismatched attributes, nonfinite UVs or invalid unit normals were found. This is an attribute/normal check, not proof of an authored distortion-free unwrap.

Chrome review at 1837 × 881 covered every compartment, both salvage starts and rebuilt pumps, 7 June flooding, deck materials, and returning through the hatch. Room render/readback samples ranged from 2.16 to 11.19 ms; these are not sustained gameplay FPS. The control-room sample reached 275 draws and about 35,000 triangles. Shader programs settled at 24 after the exterior was drawn and stayed at 24 on motor/control revisits. No shader errors were observed; the browser again logged its messaging-connection error. [Saved views](docs/visuals/quarters.jpg): quarters, galley, control room, motor room and deck are in `docs/visuals/`.

All 31 simulation checks, the evidence checker and module syntax check pass. Continuous foreground pacing and listening by ear remain open.

## 2026-11-17 — Engineering floodwater, Gerstner ocean, and deck wash

The diesel and motor rooms now shade floodwater by depth and reflect the room lamps through animated ripples. The strainer jet follows inflow and disturbs the pool around it. Opening the motor-room hatch sends a sheet toward the receiving compartment when there is modeled head across the sill. Each hydraulic step records its signed hatch transfer as visual telemetry. The fixed-step flooding calculations still govern water levels, wading, trim, and the story outcomes.

The shared exterior uses six directional Gerstner waves evaluated on the GPU, with a matching CPU surface sample for boat motion, foam, and hatch daylight. The water reflects the procedural sky. On the playable deck the crests leave foam and a receding film on the weather deck and stair treads. Deck access uses the existing clearance threshold against the simulated mean waterline.

The `?water-demo=1` preview opens the diesel strainer, with switches for the motor-room hatch and awash deck.

## 2026-11-17 — Blender hero model of the exterior

Built a detailed, fully procedural Blender model of U-505's exterior as a standalone art asset. The game, sim and data are untouched. Source of truth is the script set in `tools/blender/u505/`, one module per part; each rebuilds its own collection. The saved file is `art/u505_exterior.blend` (Blender 5.2, about 75k faces in the boat). Renders are in `docs/visuals/blender/`.

- **Dimensions.** From Report 2G-9C: LOA 76.76 m, beam 6.86 m, pressure hull 4.45 m, rudders 975 mm off the centreline and 225 mm inboard of the screws (3.111 m² each), bow planes 1.5 m above the pressure-hull bottom, hatch clear openings 600/660 mm, a starboard hawse with a stockless anchor, bow and stern plane guards. These are IXC/40 figures; U-505 was an IXC, so treat them as approximate.
- **Shape and fittings.** Section shapes, the tower, platform layout, weathering and deck pattern were reconstructed from the TG 22.3 capture photographs (Encl G 470, 499, 505, 506, 517), not from lines plans. No 105 mm deck gun (none in Encl G 499/517). Two twin 20 mm mounts and one 37 mm are a typical 1944 fit, and the counts are estimated. No snorkel, radar or DF loop, because none can be confirmed in the photographs. Propeller size and blade count, tank extents, slot rows and hatch positions are estimated.
- **What it includes.**
  - Lofted outer hull with beavertail stern and V deadwood; saddle tanks; ballast keel.
  - Fairwater with flared ledge, spray-lipped bulwark and compass hood.
  - Two Wintergarten platforms with railings and chain-link netting.
  - Bridge gear: periscope standards with the sky periscope raised, UZO post, binnacle, voice pipe, open upper hatch and rod antenna.
  - Twin bronze 3-blade screws on A-brackets; balanced spade rudders, stern planes and prop guards.
  - Bow planes with horns, tube-shutter outlines and stem bar.
  - Slatted timber deck with staggered drain slots, four dogged hatches, bitts, two capstans, guard rails and canisters.
  - Jumping wires with insulators, casing and tank flood slots, tank vents and weld seams.
- **Materials.** Procedural Cycles shaders, no image textures and no photo projection:
  - light grey topsides with ragged peeling to a dark undercoat, rust cores and runs, and grime streaks;
  - edge wear, salt bloom, waterline growth and a dark grey bottom;
  - raised weld lines and weathered silver-grey timber with per-plank variation.
- **Project rules.** No flags, ensign, emblems, hull numbers, the post-capture "CAN DO JUNIOR" paint, or crew. The boat sits at normal surfaced trim (estimated waterline 4.30 m above the pressure-hull bottom), not the damaged attitude in the photos.
- **Sets and renders.** An Atlantic set (Ocean modifier sea, far-sea skirt, physical sky, sun) and a studio set (keel blocks, shores, cyclorama, area lights). Nine cameras; `shoot()` renders any of them. On the RTX 4060 with OptiX, 1920×1080 at 192 samples takes about 20 s per shot.
- **Orientation.** Bow +Y, starboard +X, up +Z. Origin at the pressure-hull midpoint and the outside bottom of the pressure hull. After a glTF export the bow points along three.js −Z, which matches the game. No export has been tested.
- **Fixes from review.**
  - The hull's normals came out inward, because its degenerate end fans fooled `recalc_face_normals`. The shrinkwrapped casing slots were sinking out of sight as a result. `build_main_hull` now checks a side face and flips the mesh.
  - Tube shutters gained raised rims that follow the hull surface.
  - The studio fill light was moved so its plane no longer cuts the floor.
  - All nine shots were re-rendered and reviewed.
- **Not verified.** The model is unchecked against the Skizzenbuch or MSI photographs, which are rights-pending. No glTF export has been tried. The hatch uses a staged difference in water level, with an optional pump at 60× simulation speed for visible drawdown. The simulation checks now verify that the signed hatch rate matches the transferred volume and clears on closure.

## 2026-11-17 — Surfacing and tow water effects

Surfacing gets a short waterline boil, a bow fan with falling spray, and a curved wake that persists behind the turn. During the tow, Guadalcanal leaves a wider propeller wash and U-505 trails a narrower wake. Foam follows the Gerstner surface and builds near the hull where the crests meet it.

The water demo now loops both exterior shots. Developer controls set the flood clock, initial flood conditions, strainer opening, motor-room hatch, and swell. The tow preview reads the current simulation pose. The campaign tow takes its pose from the actual salvage result at the handoff. The surfacing preview uses a staged rise and a closer camera. All 32 simulation checks and the evidence check passed.

## 2026-11-17 — Turbulence test basin

Added a sixth water demo scene for testing a continuous jet, a moving wake, and repeatable pulses. The basin runs a damped 2D surface field at a fixed step, with waves reflecting from the walls and foam lingering where the water is disturbed. Strength and damping controls, a motion heatmap, and peak displacement and RMS vertical speed readings support side-by-side tests. Campaign hydraulics run separately.

Chrome checks covered clicking the water and the area outside it, pause and reset, the shaded and heatmap views, and a 390 px viewport. Two new numerical checks cover propagation, settling, and repeatability after reset. All 34 simulation checks and the evidence check passed.

## 2026-11-17 — Blender model glTF export test

Exported the Blender exterior to glTF as a test of the pipeline. Nothing in the game changed.

- **Export script.** `tools/blender/u505/export_gltf.py` exports temporary copies of the 34 boat meshes, so the saved model is never touched. Modifiers are applied, so the decals stay on the hull.
  - Flat web materials replace the procedural Cycles shaders, with constant PBR factors.
  - Painted faces below the boot-top get the dark bottom colour, which keeps the two-tone without textures.
  - The netting is left out, because its alpha panels sort badly in three.js.
  - Fixed a bug found while testing: clearing a mesh's materials resets every face to slot 0, so the face slots are read first.
- **Output.**

  | File | Size |
  |---|---|
  | `art/u505_exterior.glb` (plain) | 3.87 MB |
  | `art/u505_exterior_draco.glb` (Draco) | 357 KB |

  168,472 triangles, 41 primitives, 10 materials, no textures.
- **Viewer.** `tools/glbview.html` loads either file with three.js 0.160 from jsDelivr, the game's version, plus `GLTFLoader`, `DRACOLoader` and `OrbitControls` from the same CDN. It has ACES tone mapping, a sun and a hemisphere light, and a translucent waterline at 4.30 m. Stats go to `window.__glb`.
  - Serve it with the new `u505-glb` launch config (`node tools/serve.mjs 8507`), then open `/tools/glbview.html?file=art/u505_exterior_draco.glb&view=bow|stern|side|top|tower`.
  - `serve.mjs` now serves `.glb` as `model/gltf-binary`.
- **Measured in the browser pane.**
  - Bounding box 6.92 × 13.92 × 76.84 m.
  - The bow planes sit at z −33.9 and the propellers at +34.7, so the bow points along −Z, matching the game.
  - 42 draw calls, two shader programs, and no loader warnings. Draco decoded from the CDN.
  - The bow, tower and stern views drew correctly, with crisp deck-edge normals.
- **Before it could go in the game.**
  - The model is about 5× the triangles of the game's busiest interior view (about 35k). It would need a decimated level of detail and meshes merged by material.
  - Draco adds a new CDN dependency (its decoder files).
  - A separate GLB breaks the single-file public preview unless it is embedded.
  - The model's origin is the outside bottom of the pressure hull; the sim's z starts at the inside bottom. The playable deck's walk heights come from the game's own deck profile, so the two decks won't line up automatically.
  - The weathering is lost without a texture bake.

## 2026-11-17 — Baked textures for the Blender GLB

Baked the model's procedural weathering into textures, so the GLB keeps it. Nothing in the game changed.

- **Bake script.** `tools/blender/u505/bake_textures.py`, with `bake_all(out_dir)`, runs after `build()`. It produces two lighting-free base-colour textures (a Cycles DIFFUSE/COLOR bake, saved with `Image.save` so the AgX view transform isn't applied):

  | Texture | Contents |
  |---|---|
  | `art/textures/u505_paint_basecolor.jpg` (4096², 1.6 MB) | The 16 hull-paint objects, Smart-UV-unwrapped together into one atlas (0.43 UV coverage, about 1.6 cm per texel). It carries the boot-top two-tone, peeling, rust and grime runs, salt and waterline growth. |
  | `art/textures/u505_deck_basecolor.jpg` (4096×512, 0.3 MB) | `Deck_Planks`, projected from above along the deck. It carries the grain, plank variation and dirt. |

  - `Casing_Seams` keeps a flat colour.
  - Bump-only detail (weld beads, fine paint texture) is not baked, and there are no normal or roughness maps.
  - The bake takes about 2 minutes on the RTX 4060.
- **Export.** `export_glb(path, draco, textured=True)` puts the baked images on the objects that have the `BakeUV` layer. Other objects keep the flat web colours.

  | File | Size |
  |---|---|
  | `art/u505_exterior_textured.glb` | 6.9 MB |
  | `art/u505_exterior_textured_draco.glb` | 2.4 MB |

  Both embed JPEG textures at quality 88.
- **Checked in `tools/glbview.html`.**
  - 168,472 triangles, three shader programs and no warnings.
  - 36 primitives against 41 for the flat file, since the textured paint no longer splits off a dark-bottom material.
  - Draw calls depend on the opening view, because off-screen meshes are culled, so they aren't comparable between runs.
  - Same bounds, with the bow along −Z.
  - Bow, stern, tower and a new close `casing` view: the weathering matches the Cycles renders, and no UV seams are visible on the casing at about 7 m.
  - A new `far` view (about 340 m, the Act 1 distance), magnified 5× from the canvas, shows no dark mipmap bleed at the atlas island edges. Neither does the 95 m side view.
- **Note.** A rebuild regenerates the meshes and drops `BakeUV`, so run `bake_all` again before a textured export.

## 2026-11-17 — Detailed U-505 in the surfacing and tow scenes

The Blender model now replaces the primitive U-boat in the Act 1 surfacing scene and the 14:23 tow. The walkable deck (Act 3 and 7 June) still uses the simple boat. Its walk heights don't match the real geometry; see "Not done" below.

- **Game model.** `art/u505_game.glb`, 990 KB with Draco, built by `export_game_glb()` in `tools/blender/u505/export_gltf.py` (run `bake_all` first).
  - **Triangles:** 79k, against 168k for the full model. The weld beads and netting are dropped, and the hull, tanks, tower shells and dense fittings are decimated.
  - **Draw calls:** 10 meshes, one per material.
  - **Textures:** the paint atlas at 2048², the deck strip at 4096×512.
  - **Metalness:** capped at 0.3, because the exterior scene has no environment map and fully metallic surfaces would render nearly black.
- **Loading in `index.html`.**
  - The import map adds `three/addons/` (three 0.160.0, jsDelivr). `loadBoatArt()` imports `GLTFLoader` and `DRACOLoader` dynamically, loads the GLB in the background, adds it to the `uboat` group and compiles its shaders once.
  - Any failure (offline, `file://`, or the single-file public preview without `art/`) logs a warning and keeps the primitives. `?boatart=0` turns the model off.
  - `setBoatArt()` decides what shows: the model in Act 1 and the tow, the primitives on the walkable deck (`openDeck` and `closeDeck`).
  - `placeBoatArt(waterY)` puts the model's waterline (4.30 m above its origin) at the scene's sea level in the group frame: −0.8 in Act 1, −1.55 in the tow, where extra draught still lowers the whole group.
  - The tow wire now ends at the model's stem fitting.
- **Verified in the browser** (port 8507; the 8505 server predates the `.glb` MIME type and needs a restart).
  - **Surfacing:** the model loads; the waterline sits at sea level ±0.3 m with the swell, the keel is under water and the deck about 1.7 m above the sea. The orbit shot shows the tower, Wintergarten, guns and wires.
  - **Tow** (`?water-demo=tow`): the wire is on the stem and she trims stern-down at the run's draught.
  - **Walkable deck** (`?water-demo=deck`): the model is hidden, the simple boat is shown, and walking works.
  - **`?boatart=0`:** the GLB isn't requested and the primitives run the tow.
  - **Cost:** shader programs go from 24 to 32 (the model's materials, compiled at load). The exterior frame showed 27 draws and about 80k triangles.
  - The only console error is a favicon 404, which also happens with the model off.
  - `simcheck` and `evidencecheck` pass.
- **Not done: the walkable deck.**
  - The model's deck is 1.1 m higher and its bridge floor 1 m lower than the game's `deckY` (2.57) and `bridgeY` (6.85), measured from the hull axis.
  - The game's stairs run up the centreline through the real tower.
  - Matching the model would raise the freeboard from about 0.6 m to 1.6 m (so waves cross the deck less often on 7 June) and reroute the walk around the tower. That's a gameplay decision for the user.

## 2026-11-17 — The walkable deck matches the real boat

The user chose to make the walkable deck match the model. The Act 3 and 7 June deck now shows the detailed model and walks on its real surfaces.

- **Model changes** (`tools/blender/u505`):
  - The bridge hatch moves to x −0.9, matching the game's `hull.hatch.x_m`.
  - Steep ladders join the lower and upper Wintergarten platforms at side ±0.78.
  - The railings have gaps at those ladders and at the deck-to-platform rungs (x −5.6).
  - The deck canisters move aft of the tower (x −7.75), matching the Encl G 507 caption "Flask as in rack aft of conning tower".
  - Then a rebuild, re-bake and re-export of all the GLBs.
  - The Cycles renders in `docs/visuals/blender/` predate these four changes.
- **Walk layout** (`deckLayout` in the exterior block of `index.html`) ports the model's own geometry:
  - `T_W` and `T_B`, the sheer, the deck camber and plank thickness, and the tower plan outlines.
  - It matched Blender to within 0.5 mm at nine stations from stern to bow.
- **Three walking levels**, heights above the hull axis:

  | Level | Height |
  |---|---|
  | Weather deck | about 3.78 m midships, following the sheer |
  | Lower Wintergarten | 4.905 m |
  | Bridge and upper platform | 5.905 m |

  - Side rungs join the deck and the lower platform; ladders join the lower and upper platforms.
  - Collision covers the fairwater, the aft fairing, the compass hood, the bulwark (open aft), both platform edges, the periscope standards, the bridge fittings, the 20 mm mounts and lockers, the 37 mm pedestal, the hatches, the capstans, the bitts and the canisters. Player clearance is 0.15 m.
  - The old stairs, planks, rails and bollards are gone. The hatch label, the 7 June power lead and the tide-band fitting stay, set on the new surfaces.
  - The deck wash film follows the deck's sheer and camber and both platforms.
  - Casing foam forms at the waterline beam, against the old 2.57 m reference.
  - The exterior camera's near plane drops to 0.08 m on deck.
  - Climbing out puts the player on the bridge beside the hatch. The wash view starts on the lower platform.
- **Without the model** (`?boatart=0`, offline), the primitive casing and tower are lifted to the new deck height on deck. Walking works; the look is rough.
- **Added side ladders (a gameplay fitting, not from the photographs).** At the game's real trims (21.1° stern-down in Act 3 at 12:40, 22.6° at the 7 June start), the deck end of the aft rungs is 1.0–1.2 m under water. That cut the player off from the weather deck in both scenes. A ladder now hangs off each side of the upper platform at x −2.5 (`SIDE_LADDER_Y` in tower.py) down to the dry walkway beside the fairwater. The wash-view spawn moved forward to the dry lower platform (x −4.9).
- **Added forward rungs (also a gameplay fitting).** These run up each side of the fairwater at x 2.6 and over the bridge bulwark, with a handhold arch and an inside step (`FWD_RUNG_Y`). Their foot sits about 2 m higher than the side ladder's at these trims.
  - In a 7 June time series with no pumps, the route from the forward deck back to the hatch now holds until 42 minutes. She founders at 28 and is lost at 45. With only the side ladder, it was lost at about 30–32 minutes.
  - In Act 3 the route stays open from 12:40 to 14:23. The trim holds at 21.1° when idle.
- **Deck-side ladders are E actions,** like the hatch. They are the aft rungs, the side ladders and the forward rungs.
  - Standing within 0.6 m of a ladder's foot or top shows "[E] Climb up the ladder" or "[E] Climb down the ladder to the deck". E moves the player to the landing at the other end (`deckLayout.nearClimb`, `exterior.climbLadder`).
  - It refuses with "Water is washing over the foot of that ladder." when the landing is under water.
  - Walk-on ramp ladders were tried first, but walking along the narrow walkway beside the tower either lifted the player or, once that was suppressed, never started a climb. Only the two ladders between the platforms are walk-on.
  - The deck hint now reads "E at a ladder to climb".
- **Verified.**
  - **Routes, level pose:** a breadth-first search from the bridge spawn reaches the forward bridge, the upper platform, every ladder, the lower platform, the tide bands, the stern and the bow (past the tower). It cannot reach inside the tower or onto the gun mounts or periscope standards.
  - **Routes, real poses with the wash rule:** the reachable deck runs from x −3.8 (Act 3) or −3.4 (7 June) to the bow; the flooded aft deck stays blocked.
  - **Walking:** walking aft along the walkway in the Act 3 pose stops at x −3.4, where the wash rule takes over. Earlier walk-only route checks used the walk-on ramp version of the deck-side ladders, which has since been replaced by E-climbs. The current proof is the prompt-driven route and the time series below.
  - **Climb-out loop:** the real F / E / F loop at the control-room ladder works: out onto the bridge beside the hatch, back below, out again.
  - **Prompts:** in the Act 3 pose, a search over walk steps and climbs, followed through the game's own `use()` and prompts, went bridge → "[E] Climb down the ladder to the deck" → forward deck → "[E] Climb up the ladder" → bridge → "[E] Climb down through the hatch" → below. The 7 June and Act 3 time series above were rerun with the E-climbs and give the same results.
  - **Not checked by hand:** the ladder stringers aren't collision obstacles, and the forward rungs stand about 0.47 m off the fairwater.
  - **Shader programs:** stay at 31 across deck → tow → surfacing → deck.
  - **Checks:** `simcheck` and `evidencecheck` pass.
- **Gameplay change (measured, not retuned).** Act 3 at 12:40 sits 21° stern-down; 7 June starts at 22.6°.
  - The aft deck is still deep under water at x −14, −25 and −32 in both: foot height −3.9 m to −11.3 m, against −5.1 m to −12.4 m on the old deck.
  - The point where the sea crosses the deck has moved about 3 m aft, from about midships to beside the tower's aft fairing. Wash-over still blocks the aft deck.
  - The tow has no walking, so its pose wasn't sampled.

## 2026-11-18 — Jam build browser checks and campaign sound fixes

- Tested the shipped `index.html` plus `art/u505_game.glb` on a fresh local origin in a new foreground Chrome window. Native button input captured the mouse; Escape released it and paused. An iframe deliberately refused capture: real drag input changed the deck camera, and E returned below. A browser-delivered R on a loss screen returned to the 11:46 boarding card.
- Fixed campaign sound: Act 1 previously never updated the mixer outside the water demo, and sea ambience was gated to demo shots. Approach and tow now play the sea channel and silence interior channels. Also silenced channels behind title/interstitial cards, including the restart title, which previously retained boarding sounds.
- Added the lazy `__u505.audio.output()` analyser probe and `tools/jamcheck.html`. The harness loads the actual build unchanged, uses existing debug hooks for setup, and passes 15 browser checks: live unclipped audio output, drag/release/movement, mute, pause/resume, notebook sound, approach sound, textured model, deck/hatch loop, Act 2/3/7 June loss/retry, checkpoint restoration, normal tow handoff, final restart and title silence.
- Visually checked the detailed surfacing boat and playable bridge, plus the explicit primitive fallback. The GLB has 10 meshes, 79,434 triangles and two meshes with loaded texture maps. No shader/model loading blocker was observed.
- `node tools/simcheck.mjs` and `node tools/evidencecheck.mjs` pass. Audio was verified from live WebAudio waveform samples and the browser's audio-playing indicator; subjective speaker/headphone listening, a full real-time playthrough and continuous foreground frame timing were not performed.
