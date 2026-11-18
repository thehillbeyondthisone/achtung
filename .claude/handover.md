# Handover — first git commit and push (2026-11-17)

For the game itself (acts, sim, tests, open questions), `docs/HANDOFF.md` is the current handoff. `HISTORY.md` is the dated log. The previous session's work (Blender exterior model, GLB exports, texture bake, `tools/glbview.html`) is described in HISTORY.md and project-truths.md.

## What changed this session
- The folder is now a git repo tracking https://github.com/thehillbeyondthisone/achtung (public), branch `main`.
  - Built on top of the remote's existing "Initial commit" (a stub README.md: "achtungmanager / manager"), not force-pushed. The README is still that stub.
- Added `.gitignore`: `*.blend1`/`*.blend2`, `node_modules/`, `.claude/settings.local.json`, OS clutter, and `docs/sources/`.
  - `docs/sources/` (uboatarchive.net mirror, ~10 MB) stays local by user decision, because the repo is public. `docs/SOURCES.md` and `tools/fetch-tg22-3.mjs` are pushed so it can be re-fetched.
- Added `.gitattributes` (`* text=auto eol=lf`, binaries marked) so the system `core.autocrlf=true` doesn't rewrite files to CRLF.
- project-truths.md: replaced "not a git repository" with the remote and where git lives (GitHub Desktop's bundled copy; git is not on PATH).

## What was tested
- `node tools/simcheck.mjs` passed (exit 0) on the committed snapshot.
- The repo was confirmed publicly readable (`ls-remote` with no credentials).
- No personal email or local user paths found in the committed text files.

## Open issues
- README.md is a stub; worth replacing with a short project description.
- Largest tracked files are the GLBs/.blend (up to 6.9 MB each). Fine for GitHub, but repeated re-exports will grow history; consider Git LFS for `art/` if they change often.
- Other sessions edit `index.html` and HISTORY.md in this folder; commit their work separately.

## Next step
- Decide on the textured GLB (lower-poly game version, normal/roughness bakes, or stop) — see HISTORY.md.
