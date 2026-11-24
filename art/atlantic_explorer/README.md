# Atlantic Explorer VR asset

This directory contains a VR-prepared version of JosephWPugsley's Atlantic Explorer research submersible. See [ATTRIBUTION.md](ATTRIBUTION.md) before redistribution.

## Outputs

- `atlantic_explorer_vr.glb` — decoder-free GLB for development and broad compatibility.
- `atlantic_explorer_vr_draco.glb` — smaller production GLB; configure a Draco decoder in Three.js.
- `atlantic_explorer_collision.glb` — seven low-cost exterior/interior collision proxies.
- `atlantic_explorer_vr.blend` — editable working scene with hidden collision collection.
- `atlantic_explorer_vr_preview.png` — conversion review render.
- `vr_manifest.json` — dimensions, mesh/anchor names, texture limits, and build notes.

The asset is 8.113 m long, 3.239 m wide, and 3.276 m tall. Blender uses Z-up with the pilot looking toward +Y. glTF is exported Y-up with the pilot looking toward -Z. The render asset has 120,380 triangles in 20 meshes. Its largest texture dimension is 2048 px.

The two viewports, three light groups, and eight thrusters are separately named for damage state. Empty nodes beginning with `XR_` provide seated headset/hand starting points. Nodes beginning with `ANCHOR_` locate pressure, leak, audio, battery, life-support, and viewport effects. These are authored starting points, not final headset comfort calibration.

## Rebuild and verify

From the repository root with Blender 5.2 installed:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' --factory-startup --background --python tools\blender\atlantic_explorer\prepare_vr.py
node tools\check-atlantic-explorer.mjs
```

Use `node tools/serve.mjs`, then open `/tools/atlantic-vr.html` for the WebXR inspection scene. A secure context is required for immersive VR; `localhost` qualifies on the development machine.

## Runtime guidance

Use the plain GLB until the interaction and failure systems are stable. Switch to the Draco GLB for delivery after configuring `DRACOLoader`. Load the collision GLB separately and keep its meshes invisible. They are broad-phase proxies and should not be rendered.

Do not move the XR camera directly every frame. Place a rig/root at `XR_HEAD_PILOT`, parent the WebXR camera and controllers to that rig, and let headset tracking supply the local head offset. Recalibrate the stored anchor after an in-headset seated comfort pass.
