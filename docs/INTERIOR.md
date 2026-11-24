# U-505 interior art and flooding

The Blender asset covers the control room, diesel room, electric-motor room, and aft torpedo passage. It includes the diesel-room hull and the structure and hardware on both sides of its two hatches. The game supplies the other hull sections, the forward rooms, signs, lamps, pumps, collision, and interaction targets. The Blender asset and the procedural rooms use the same deck heights, walk widths, and hatch centers.

## Sources and parts

| Space | What the photographs informed | What is reconstructed |
| --- | --- | --- |
| Control room | Banks of handwheels, bent pipes, tall scale, and a crowded deckhead. [Wartime G437](https://www.uboatarchive.net/U-505A/U-505EnclG437.htm), [wartime G435](https://www.uboatarchive.net/U-505A/U-505EnclG435.htm), [museum-era ladder view](https://uboat.net/gallery/U505C/photo/9) | Valve and instrument placement around the game's existing ladder and gauge stations. |
| Diesel room | Twin engine banks, narrow raised grating, rounded cylinder covers, low valves, and a vessel overhead. [Wartime G516](https://www.uboatarchive.net/U-505A/U-505EnclG516.htm), [U.S. Navy 80-G-324368](https://www.history.navy.mil/our-collections/photography/numerical-list-of-images/nara-series/80-g/80-g-320000/80-G-324368.html) | Engine envelopes, stop-lever mounts, strainer installation, pipe routes, and edge wear. Nine repeated assemblies per bank follow the engine description in the existing design references. |
| Electric-motor room | Long switchboards with dark dials, curved housings, and handrails along the walkway. [Wartime G523](https://www.uboatarchive.net/U-505A/U-505EnclG523.htm) | Motor and switchboard envelopes and the round aperture in the game's bulkhead. |
| Aft torpedo passage | Bunks, patterned bedding, hanging chains, and overhead cable runs. [Wartime G522](https://www.uboatarchive.net/U-505A/U-505EnclG522.htm) | Berth spacing, lower machinery, cable routes, and tube closure placement. |

The photographs establish shapes and visible wear. Paint colors, lamp fixtures, lighting conditions, and the water level at any given moment are game reconstructions. The strainer cover follows the preserved artifact's overall dimensions, curved handle, and four pairs of prongs. The cover, diesel stops, cooling valve wheel, and hatch leaves use separate meshes so the game can move them from its own state. [Griffin MSI cover catalog](https://collections.griffinmsi.org/collections/11131)

## Build and review

Use Blender 5.2 from the repository root. The script reads the existing compartment and system data from `index.html`. The Blender axes are X starboard, Y toward the bow, and Z up from the pressure-hull axis. The GLB exporter converts these to the game's Three.js axes.

```powershell
blender -b --factory-startup --python-exit-code 1 --python tools/blender/u505/build_interior.py -- --review
```

The build writes `art/u505_interior.blend` and `art/u505_interior.glb`. It checks the engineering walkways against the modeled equipment and caps the export at 125,000 triangles. `--verify` checks the re-imported GLB. `--review` also captures four Blender reference views. `--graybox` builds a diesel fit asset, which can be loaded with `?interiorart=graybox` during modeling. Use `?interiorart=0` to review the procedural fallback.

## In-game review

The flood model supplies the mean water surface and signed hatch transfer. Surface ripples, wakes, foam, and reflections are presentation effects. Spatial audio uses the same source and hatch positions. A rigged pump's suction sound and water disturbance follow the hose end, while its motor stays at the pump casing. The four existing practical lights illuminate the task hardware and spill through open hatches.

In the diesel room, the forward practical throws warm light across the strainer and stops. Cooler light marks the aft sill and water beneath it. Each face of the two bulkheads takes its wetness from the adjoining compartment, so a closed hatch can retain a dry side when the other side floods.

Matched player-eye views show the strainer, both stops, and the motor hatch in dry and flooded conditions, including both sides of a sealed hatch. [Diesel-room before and after](visuals/interior/diesel-cinematic-comparison.jpg)

The matched route held 16.9 ms p95 before and after in foreground Chrome at 1280 × 720, device scale 1, on the RTX 4060. The longest frame was 100.2 ms before and 116.8 ms after. The new GLB is 9.95 MB and re-imports as 16 assemblies with 124,716 triangles.

Open `?water-demo=hatch` and use Developer controls to compare a dry room, an open source, reversed flow, and a submerged hatch. The browser regression suite is at `tools/jamcheck.html`. Matched player-eye screenshots show the [dry](visuals/interior/diesel-dry.jpg), [rising](visuals/interior/diesel-rising.jpg), and [flooded](visuals/interior/diesel-flooded.jpg) diesel room.

For the normal-clock campaign comparison, see the [second-pass review](SECOND-PASS.md).
