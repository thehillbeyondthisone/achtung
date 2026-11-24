# Browser release

Install the pinned npm package into the local build cache, then stage the release from the current checkout.

```powershell
npm install --prefix dist/release-deps --no-save --no-package-lock --ignore-scripts three@0.160.0
node tools/stage-release.mjs
```

If the exact package is already available, pass its directory to `node tools/stage-release.mjs`. The staging script copies the runtime files into `dist/u505/`, points Three.js and Draco to copies in the release, and selects online historical citations. The original checkout keeps its development import map and local research links.

To package the staged files for handoff, run `tar -a -cf dist/u505-desktop-test-build.zip -C dist/u505 .` on Windows.

Preview the staged build at a site root.

```powershell
node tools/serve.mjs 8505 --release
```

Open [the release preview](http://127.0.0.1:8505/). For a subpath check, run `node tools/serve.mjs 8505` and open [the staged site under a subpath](http://127.0.0.1:8505/dist/u505/). Upload the contents of `dist/u505/` to a static host with JavaScript and WebAssembly MIME types. Historical report links need internet access when opened. The game and shipped models load from the host itself.

For a fallback smoke test, open the release with `?boatart=0` for the procedural exterior or `?interiorart=0` for the procedural interior.

Run `node tools/releasecheck.mjs` to check both mount paths in fresh Chromium contexts. The check blocks external requests, verifies the online notebook links and local decoder, then fails each GLB request separately to exercise the procedural fallbacks. It uses the same `MENU_PLAYWRIGHT` and `MENU_CHROME` overrides as the menu checks. Pass `--headed` for a foreground browser.

See the [release candidate handoff](RELEASE-CANDIDATE.md) for the current package, results, and open playtest gates.

## Starting baseline verification

- The static build passed at a site root and subpath. With either model request returning 404, the player could still walk to the bridge hatch, descend, and start the simulation. The throttled cold menu took 6.25 seconds at 20 Mbps and 80 ms latency in Chrome.
- A continuous open-motor-hatch run reached Bermuda. A second clean-profile run reached Bermuda after reloading at the bridge, the ladder, 12:40 salvage, the 14:23 tow, and the 7 June rescue. The 12:40 reload preserved the closed motor hatch and exact inherited water volumes. The tow replay retained the pump events.
- The foreground bridge-to-shutdown capture ran in Chrome at 1280 × 720 and device scale 1 on the RTX 4060. The below-deck p95 frame interval was 16.9 ms, matching the recorded [second-pass boarding baseline](SECOND-PASS.md). The capture included one frame interval of 133.3 ms. The captured stereo signal peaked at −4.76 dBFS.
- The simulation, evidence, menu, browser gameplay, and release checks passed.
- Independent first-time play and listening by ear remain outstanding.
