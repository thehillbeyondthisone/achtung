# Handover

## 2026-11-24 — Menu redesign ("Deep Water")
For the game overall, `docs/HANDOFF.md` is the current handoff and `HISTORY.md` the dated log. Other sessions also edit `index.html` here, and the tree already had other uncommitted work before this session.

### What changed (`ui/menus.css`; nothing committed)
- **Complete CSS rewrite** of the menu system from a light "plotting desk" dossier look to a dark atmospheric theme. `ui/menus.js` was not touched — the redesign is CSS-only, preserving every selector, ID, data attribute and class name.
- **Palette:** dark blue-grays (`--fm-paper: #0c1419`, `--fm-sheet: #131d24`), warm off-white text (`--fm-ink: #e0dbd0`), red accent `--fm-red: #c43c2d`.
- **Typography:** Bahnschrift (Windows) / DIN Alternate (Mac) system font stack. No CDN fonts.
- **Splash:** full-bleed hero image with dark gradients, transparent card.
- **Main menu:** radial gradient background, broadside image fades into the dark.
- **Panels:** dark backgrounds, subtle borders, 3px radius. No box shadows.
- **Pause:** `backdrop-filter: blur(6px)`.
- **Glossary flags:** brightened for dark backgrounds.
- **All responsive breakpoints preserved.**

### What was tested
- menucheck 22/22, releasecheck 4/4 pass.
- Visual checks at desktop, mobile (375×812) and landscape phone (844×390): splash, main menu, settings (all 4 tabs including Accessibility), chapters, briefing, credits all verified.
- Pause overlay verified over live 3D scene — `backdrop-filter: blur(6px)` reads well on deck.
- No `--fm-` variable consumers outside `ui/menus.css`; no Impact/Georgia font references in `index.html`.
- No overflow, no truncation, no external resource requests.

### Not tested / open
- `#intro`, `#banner`, `#glossary` and `#replay` overlays were styled in CSS but not visually verified during gameplay.
- In landscape (844×390), the Accessibility tab label clips behind the footer — functional (clickable) but cosmetically tight; likely pre-existing layout.
- Oil sheen (on the vision page) is not built. The chalk survey was not part of this request.
- The hand lamp does little on bare-metal deck plates (they barely respond to spot lights); fine on machinery, racks and deckhead.
- Nothing committed.
- Older open items still stand: the 12:40 sea-crossing shift on deck, stale Cycles renders in `docs/visuals/blender/`, hands-on play-through for knock/lamp tuning.

### Next step
- Commit the menu redesign (and possibly the earlier hand lamp / knock / flotsam work). A hands-on play-through remains the main gameplay gap.
