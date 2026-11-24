# U-505 desktop release candidate

**In testing.** The first-time-player, listening, and tester-laptop checks require independent participants and equipment. The automated runs below exercise the build and its checkpoints.

## Build and captures

- The starting static build is preserved in `dist/u505-baseline/`. Its staged `index.html` has SHA-256 `e109e2c1dcae73e1503449effa3ccd3e0c11fee2f723e5ac9cf82091db072011`. [Baseline build](../dist/u505-baseline/) · [Baseline 4 June capture](../dist/rc-verification/u505-baseline/june-4-diesel-100.jpg) · [Baseline 7 June capture](../dist/rc-verification/u505-baseline/june-7-diesel-100.jpg)
- The [static ZIP](../dist/u505-desktop-test-build.zip) contains the files from `dist/u505/`. Its SHA-256 is `e055b457cf888fb78cfc51cd496a834b29281634c98b890f0f0c2cf12e54f7a1`. Its staged `index.html` has SHA-256 `85037c2f0a1e70f4681d7375cc773c8ff939d443bea44f1a6d39b5ab6ffdb684`. The build vendors Three.js and Draco, ships both boat models, and uses online links for historical sources. [Static staging instructions](RELEASE.md)
- The matched diesel-room captures use the same position, heading, and pitch at both chapter starts. At a fixed point on the aft grating, the water rises from 0.49 m to 2.10 m. The initial trim goes from 3.63° to 22.61° stern down. Captures use 1280 × 720, 1× render scale, and muted audio. [Matched room views](../dist/rc-verification/diesel-room-comparison.jpg) · [Capture settings and measurements](../dist/rc-verification/u505/matched-views.json)
- The notebook identifies the staged handoff gestures as reconstructions. The painted waterline staff is a gameplay fitting attached to the simulated hull. The ending follows the salvage report and the museum’s account of the German crew. [Task Group 22.3 salvage report](https://uboatarchive.net/U-505A/U-505TG22.3Report.htm) · [Griffin Museum capture account](https://www.griffinmsi.org/exhibits/u-505-submarine/capturing-the-u-505)

## Verification

| Check | Result |
| --- | --- |
| Simulation and evidence | 37 simulation checks passed, including the two salvage starts, dry intake, loss, one-pump rescue, and replay event selection. The evidence check passed with 26 notebook entries and 60 assumption records. |
| Menus and gameplay | 22 menu checks and 24 gameplay checks passed. Focused browser checks covered live orders, the alternate cooling-water valve, the optional Enigma handoff with other material, and the June 7 hose and boot cues. |
| Campaign | Both final-build runs reached Bermuda with 95 t of modeled reserve after handing off one electric pump. The open motor-hatch route connected the aft torpedo and motor-room intakes and followed the 5 June inspection. The shut motor-hatch route connected the aft torpedo and diesel-room intakes and went directly to 7 June. [Open-hatch log](../dist/rc-verification/final-campaign/telemetry.json) · [Shut-hatch log](../dist/rc-verification/final-reload/telemetry.json) |
| Checkpoint reloads | Resumed at the bridge, ladder, salvage, tow, and rescue in the shut-hatch run. Inherited water and hatches matched the saved salvage state. Version 1 saves without the new event identifiers retained their bookmarks and scrub controls. A save with only timestamps and text also retained sequential bookmarks. |
| Loss and dry intake | With the rescue clock accelerated for testing, leaving the pumps idle caused foundering at 11:11:56. R restored the exact initial water and reserve at 10:35. In a dry diesel-intake fixture, E gave a readable message and left the pump in hand. [Edge-case log](../dist/rc-verification/final-edge-cases/telemetry.json) |
| Static release | All four checks passed in Chrome 157. The build worked at a site root and subpath with external requests blocked. Independently forcing each model request to return 404 still allowed boarding and starting the flood clock. |
| Tow decisions and accessibility | With the motor-room hatch left shut at tow the debrief featured the closure. With the hatch left open it featured the aft-torpedo pump connection and showed 75.7 t at the action and 63.2 t at tow. Tab reached the action with visible focus, Enter jumped to it, and End on the slider returned to tow. |
| Brightness and motion | Compared the two chapter starts at 65% and 100% brightness with both interior versions. Tested look control from the first salvage climb and Enigma delivery with reduced motion, muted audio, and pause. |
| Boarding frame intervals | 16.8 ms p95 and 33.3 ms maximum across 1,435 foreground frames on the RTX 4060 using Chrome, D3D11, 1280 × 720, and 1× render scale. The test used drag-to-look from the ladder through the diesel stops, past the motor hatch, and back to daylight. Baseline 16.9 ms p95, budget 20.28 ms. [Frame timing data](../dist/rc-verification/boarding-drag-perf/boarding-frame-times.json) |
| Cold menu | 2.44 s at 20 Mbps and 80 ms latency. Baseline 6.25 s, budget 7.50 s. |

The final open-hatch run entered the optional approach and used Enter to skip to the bridge. A separate integration run watched the natural approach and reached Bermuda. [Natural approach run](../dist/rc-verification/release-campaign/telemetry.json)

The boarding recording peaked at −4.89 dBFS. Audio checks measured the individual diesel rundowns, water and pump changes, and the crew cues. Headphone and laptop-speaker listening is pending. [Reference boarding recording](../dist/rc-verification/boarding-drag-perf/bridge-to-diesel-shutdown.webm)

## Playtest record

Both rounds are pending. Use a fresh browser profile for each participant. In each round start three first-time players from the main menu with ordinary controls. In round two use three new participants. Let them choose the approach, explore, use the notebook, and retry. Record elapsed playtime as an observation.

| Participant | Stage and location | Action attempted | Cue used | What happened and how to reproduce it | Needed coaching | Fix and retest |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

At the first pump choice, ask what aboard led the player to choose that room. On deck, ask what tells them whether the boat is recovering. After the run, record whether they boarded and stopped the principal leak independently, reached Bermuda, and could explain a valid pump choice.

The first-time-play gate requires all three round-two players to stop the principal leak without coaching and at least two to reach Bermuda and explain a valid pump choice. Listen to the game on headphones and laptop speakers, including the separate diesel rundowns, the case contact, wet and air suction, and the crew handoff. Record the tester laptop’s GPU, browser, display and render settings, and frame intervals separately from the reference RTX 4060 measurements.
