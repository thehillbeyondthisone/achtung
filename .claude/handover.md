# Handover — the walkable deck matches the real boat (2026-11-17)

For the game itself, `docs/HANDOFF.md` is the current handoff. `HISTORY.md` is the dated log. Git: public repo https://github.com/thehillbeyondthisone/achtung (`main`); git lives in GitHub Desktop's bundled copy (see project-truths.md). Other sessions edit `index.html` and HISTORY.md here too.

## What changed this session
- **Cutscenes.** The detailed U-505 (`art/u505_game.glb`, 989 KB, 79k triangles, 10 meshes) shows in the Act 1 surfacing scene and the 14:23 tow (`loadBoatArt` / `setBoatArt` / `placeBoatArt` in the exterior block). The import map adds `three/addons/`.
- **Deck.**
  - The Act 3 and 7 June deck now shows the model too, and walks on its real surfaces.
  - `deckLayout` (top of the exterior block) ports the model's deck and tower geometry and replaces the old `deckY`, `bridgeY`, `stairs`, `deckProfile`, `deckFloor`, `casingWidth` and `deckHalf`.
  - There are three levels (deck, `low`, `up`), with obstacle collision; `player.deckLevel` holds the current one.
  - The platforms are joined by walk-on ladders. Deck ↔ tower climbs are E actions (`deckLayout.nearClimb`, `exterior.climbLadder`, prompt in `findTarget`) that refuse a landing under water. Ramps were tried and failed on the narrow walkway.
  - Player spawn is on the bridge beside the hatch at x −0.2, side 0.7.
  - The camera's near plane is 0.08 m on deck and 0.3 m elsewhere.
- **Model changes in `tools/blender/u505`:**
  - the hatch is at x −0.9 (`HATCH_Y`);
  - ladders join the lower and upper platforms (`LADDER_X`);
  - side ladders run from the upper platform to the deck walkway at x −2.5 (`SIDE_LADDER_Y`). This is a gameplay fitting: at the game's 21–23° stern-down trims the aft rungs land in the sea;
  - forward rungs run up the fairwater and over the bulwark at x 2.6 (`FWD_RUNG_Y`). This is also a gameplay fitting: on 7 June it keeps the route from the forward deck back to the hatch open until 42 minutes (she founders at 28 and is lost at 45);
  - the railings have gaps at all the ladders and rungs;
  - the canisters are aft of the tower.
  - All the GLBs were re-exported.
- `?boatart=0` (or a missing GLB) uses the primitives, lifted on deck. The walking is unchanged.

## What was tested
- `deckLayout` matches Blender's `deck_z` and `w` within 0.5 mm at nine stations.
- **Routes:** a breadth-first search from the spawn reaches every intended area and none of the blocked ones.
  - In the real Act 3 and 7 June poses with the wash rule, the reachable deck runs from x −3.8 (Act 3) or −3.4 (7 June) to the bow.
  - The current route proof is the prompt-driven E-climb route and the 7 June and Act 3 time series. Earlier walk-only route checks used walk-on ramps that no longer exist.
  - All 12 climb landings (6 climbs, foot and top) are walkable, and each climb leads back.
  - The real F / E / F climb-out loop works.
- **In the browser on 8507:**
  - the views from the bridge, the walkway beside the tower and the lower platform;
  - the 7 June wash (aft deck under water);
  - the fallback;
  - shader programs steady at 31.
- `simcheck` and `evidencecheck` pass.
- **E-climbs:** a scripted route through `use()` and the prompts went bridge → deck → bridge → below in the Act 3 pose. The aft rungs refuse when flooded.
- **Not tested:**
  - a hands-on keyboard and mouse walk, which is tight between the hatch and the bulwark's aft opening and beside the tower (about 0.25 m clearance);
  - a real-time playthrough.
- **Known:** the ladder stringers aren't collision obstacles, and the forward rungs stand about 0.47 m off the fairwater.

## Open issues
- **Gameplay shift.** At 12:40 (21° stern-down), the point where the sea crosses the deck moves about 3 m aft, to beside the tower's aft fairing. The aft deck is still awash on 7 June and in Act 3.
- **Stale renders.** The Cycles renders in `docs/visuals/blender/` don't show the new ladders, the moved hatch or the moved canisters. Re-shoot with `shoot()` if needed.
- **Stale preview server.** The 8505 server predates the `.glb` type and falls back silently; restart it.
- **Public preview.** It must serve `art/u505_game.glb` next to `index.html`.
- **Not committed.** Nothing from this session is committed.

## Next step
- A hands-on walk of the deck with keyboard and mouse to judge the narrow spots. Then consider widening the hatch-to-bulwark gap or the tower walkway if they feel fiddly.
