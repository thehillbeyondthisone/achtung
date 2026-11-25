# U-505: Boarding Party

A browser game about boarding, securing, and salvaging U-505 in June 1944. Explore the submarine, stop the flooding, and keep her afloat through the journey home.

Run the local preview with Node.js:

```powershell
node tools/serve.mjs
```

Open [the game](https://thehillbeyondthisone.github.io/achtung/). The browser needs access to jsDelivr for Three.js; no build step is required.

The engineering rooms use a Blender reconstruction based on photographs of U-505. The [interior notes](docs/INTERIOR.md) cover the sources, rebuild command, and flood demo.

The cinematic naval menu system includes a splash screen, main menu, mission briefing, four chapter checkpoints, service record, field manual, and pause and debrief screens. Audio, display, mouse controls, captions, hints, and reduced motion are configurable in Settings. Press P to pause and G to open the notebook during play.

**Board U-505** starts on the bridge. Walk to the hatch and press F to climb down. Below, F at the ladder returns you to daylight. F on deck waits for the next party, and E at the hatch goes below again. The notebook shows the current order and the flood survey during salvage.

Archive discoveries and settings are saved in this browser. **Resume operation** returns to your live position in the same tab. After reload it restores your latest campaign checkpoint, including inherited flooding and the 4 June replay. Chapter selection offers reconstructed starting points.

Run the simulation and historical-evidence checks with Node.js:

```powershell
node tools/simcheck.mjs
node tools/evidencecheck.mjs
```

The optional browser suite checks menu navigation, settings, pause behavior, and responsive layouts:

```powershell
node tools/menucheck.mjs
```

Browser checks require `playwright-core` and Chrome (or Playwright Chromium). Set `MENU_PLAYWRIGHT` to the package path and `MENU_CHROME` to the browser executable when they are not found automatically. See [the development handoff](docs/HANDOFF.md) for gameplay, diagnostics, and additional checks.

See [Browser release](docs/RELEASE.md) to stage and test the static build with local Three.js and Draco dependencies.
