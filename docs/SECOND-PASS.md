# U-505 second-pass review

## Baseline and route

The baseline started from a fresh Chrome profile and reached Bermuda before any game or art edits. Both campaign runs use the full approach, the 5 June inspection, the shipped chapter clocks, and the crew's built-in waits. The input driver used the game's mouse-look and keyboard handlers and read the campaign state for logs. The focused tests below used reconstructable checkpoints.

The approach took about two and a half minutes at its authored pace. During boarding, the player capped the strainer, operated both diesel stops, crossed the wet aisle to the open motor hatch, shut and reopened it, and returned to the ladder. The campaign continued through the aft flood valve and Enigma delivery, two separate salvage intakes, the 14:23 tow, Gallery's inspection, and the 7 June crew handoff. The baseline recorded depth, signed flow, trim, camera pose, frame intervals, and live stereo around those actions.

Both runs showed **U-505 reached Bermuda** with 95 t of modeled reserve. Tow reserve was 57.265 t on the baseline and 57.266 t on the second run. Neither full run logged a browser error.

## Findings and revisions

| Area | Baseline finding | First revision | Second revision after combined review |
|---|---|---|---|
| Rooms | The ceiling runs looked repetitive. Several diesel fittings and forward shelves appeared unsupported. A diagonal pipe interrupted the silhouette of the diesel stops. The salvage survey faced a bright ceiling patch and its prompt covered part of the board. | Added individually routed overhead pipes, hangers, junction boxes, machinery fittings, berth structure and bedding in Blender. Mounted the diesel fittings, moved the pipe clear of the controls, and gave the forward shelves and salvage survey visible supports. Moved the survey prompt below the board. | The ladder's bright rungs were visible while the side rails blended into the structure. Added muted tread wear and rail fittings, polished the walk down the center of the grating, and detailed the motor-hatch mounting ring and smaller backed compartment plates. |
| Water | The partly submerged motor hatch looked like a flat sheet at boarding flow. The deep rescue intake had little visible response. | Used the direction and strength of the simulated transfer to shape the sheet, runout, and submerged churn. Anchored both salvage and rescue effects at the ends of the suction lines. | Added narrow moving highlights on the receiving side and inward surface ripples over the intake. The surface effect fades as the intake draws air and follows crew redirection to the next wet compartment. |
| Light | The strainer and hatch were hard to read against the dark floor, while the survey crown had a broad hotspot. | Shaped the four existing practicals onto task hardware, retained some spill through the open hatch, and restored soft ambient separation over the survey. | Re-aimed the existing lights to pick out both sides of the sill and frame the ladder in the approach and retreat. Checked hints off at 65%, 100%, and 140% in both the Blender and fallback interiors. |
| Sound | Both diesels and the strainer competed for space in the mix. The water and pump were difficult to place by their sound in the wet aisle. | Balanced diesel and water, added short filtered stereo reflections to the compartments, and used a brief water-band dip during successful control cues. | Put the pump motor at the casing and the wet suction at the hose end. The deep wet-foot transient stays audible over the moving water during steep-trim wading. |

The art uses the archived interior and damage-survey photos and the same Blender builder and GLB round trip as the first interior pass. These are documented reconstructions of reference features and playable hardware. [Interior references and build workflow](INTERIOR.md)

The simulation, source rates, chamber volumes, interaction targets, and chapter clocks are unchanged. In the final boarding take, the fixed aft-diesel and motor landmarks started at 0.57 m and 0.74 m above the deck plates. At the motor hatch the player was standing in 0.52 m of water and the hatch was carrying about 70 L/s from diesel toward motor. Stern-down trim increased from 3.6° at boarding to 4.6° at the ladder. The 7 June pump was set in 1.21 m of water at 24.1° stern down.

| Final-run event | Aft diesel at −14.20 m | Motor room at −17.37 m | Stern-down trim |
|---|---:|---:|---:|
| Boarding starts | 0.570 m | 0.737 m | 3.63° |
| Motor hatch open | 0.563 m | 0.745 m | 4.02° |
| Return to the ladder | 0.567 m | 0.735 m | 4.61° |
| Salvage starts | 0.468 m | 0.959 m | 8.81° |
| 7 June pump connected | 2.853 m | 0.958 m | 24.12° |

The focused water check swept approximately 2, 69, 190, and 550 L/s in both directions, tried a half-covered and fully submerged sill, watched the transfer equalize, and closed the hatch. The focused rescue test pumped below the air threshold and followed a crew redirect into the aft torpedo room.

## Focused regression checks

- Open motor-hatch inheritance reached the 14:23 tow with **43.872 t** reserve after rigging the aft torpedo and motor intakes. The shut-hatch inheritance reached tow with **36.395 t** after rigging aft torpedo and diesel, with the motor hatch still shut. Ordinary controls and crew waits after each seed produced both results.
- A separate boarding run triggered a loss through normal play. R returned the player to the 11:46 briefing with the boat afloat.
- The 7 June chapter was also left to flood at its normal clock with no pumps. It foundered at 11:11:56, and R restored the 10:35 checkpoint at 4.922 t reserve and 22.61° stern-down trim. The retry rigged the electric pump, handed off to the crew, and reached Bermuda with 95 t reserve.
- The browser cue tests verified separate diesel rundowns, mute, pause, notebook, restart, wet and air pumping, pump pan reversal, and attenuation through a shut hatch. The pump target gain through the closed hatch was about 35% of the open-hatch gain in the measured pose. At 22.6° down by the stern, the measured wet-step target was 0.574 versus 0.124 for steady slosh.
- The final lighting review covered 24 angle and brightness combinations across the control, diesel, motor, and aft torpedo rooms with hints off. The task views also passed with the procedural fallback.
- Existing simulation checks passed **34/34**, gameplay checks passed **21/21**, menu checks passed **19/19**, and the evidence check passed. The browser tests used the shipped Three.js r160 files, served from the local cache.

## Frame times and recording

Both boarding takes ran in focused Chrome windows at 1280 × 720, device scale 1, using D3D11 on the same RTX 4060. The comparison uses foreground animation frame intervals while recording.

| Segment | Baseline p95 | Second-pass p95 |
|---|---:|---:|
| Walk from diesels to motor hatch | 16.9 ms | 16.8 ms |
| Retreat to the ladder | 16.9 ms | 16.9 ms |
| Entire boarding take | 16.9 ms | 16.9 ms |

The p95 meets the 20% budget. Whole-take p99 improved from 18.3 ms to 17.0 ms. The final take did have one 83.3 ms frame 0.12 seconds after the recording started, before the first movement. Repeated compartment crossings held at 30 shader programs. Blender re-imported all nine assemblies and 98,288 triangles, and the browser UV and normal checks passed.

The continuous clip is 37.95 seconds at 1280 × 720, 30 fps, with the live master unadjusted in 48 kHz stereo. The game clock advanced 38.0 seconds during the 37.94-second take. Audio started 22 ms after picture and the tracks differ by 2 ms in duration. I inspected frames around both animated lever stops and the motor-hatch closure and checked the corresponding audio drops. The clip reaches the ladder near 00:36. [New gameplay clip](visuals/interior/u505-diesel-shutdown-and-retreat-second-pass.mp4) · [Previous clip](visuals/interior/u505-diesel-shutdown-and-retreat.mp4)

The native clip peaks at −4.6 dBTP. Its left and right channels measure −22.8 and −23.2 dBFS RMS, with a 0.73 correlation over the clip. Each pair in the comparison uses a single gain per excerpt so the change within the excerpt is preserved. Paired loudness after encoding agrees within 0.1 LU, with the baseline first each time. The audio was checked by waveform, level, and in-game cue measurements. [Stereo comparisons](visuals/interior/u505-second-pass-stereo-comparisons.m4a) · [Matched camera views](visuals/interior/u505-second-pass-visual-comparison.jpg)

| Cue | Baseline | Second pass |
|---|---:|---:|
| Strainer cap | 0:00.0 | 0:04.3 |
| Both diesel stops | 0:08.6 | 0:19.1 |
| Motor hatch open to shut | 0:29.5 | 0:34.8 |
| Retreat to ladder | 0:40.1 | 0:46.2 |
| Stern salvage intake | 0:52.2 | 0:56.4 |
| Motor salvage intake | 1:00.6 | 1:04.6 |
| High-trim rescue pump | 1:08.6 | 1:13.1 |

The local review folder, `trailer/work/second-pass`, holds the original takes, matched screenshots, fixed-location depths, engine and hatch state, campaign clocks, and test data.

## Elapsed work

About **42 minutes of elapsed time** on 21 November, with the four workstreams running in parallel. The baseline reached Bermuda at 1:12 p.m. Central, the first combined review ran at 1:17 p.m., and the second revision and Blender build finished at about 1:25 p.m. The final full campaign reached Bermuda at 1:33 p.m. The normal-clock 7 June loss and recovery finished at about 1:41 p.m. The schedule set aside eight hours.
