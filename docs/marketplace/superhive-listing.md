# BareBlocks — listing copy (free / open source)

Ready-to-paste copy for a product / extension page (GitHub release notes, the Blender
Extensions platform, or a free Superhive listing). Replace the **[bracketed]** placeholders
and the `vkfolio` GitHub handle.

---

## Product title
BareBlocks — Parametric Blockout & Greyboxing Kit

## Tagline / subtitle (≤ ~70 chars)
Block out worlds, not geometry. 42 live primitives, splines & an AI builder.

## Category
Add-ons → Modeling (secondary: Add-ons → Render / Scene)

## Price
**Free.** BareBlocks is free and open source.

## License
GPL-3.0 — free to use, study, modify and redistribute (also required for Blender add-ons
that link Blender's Python API).

## Distribution channels
1. **GitHub** (source of truth) — repo + tagged releases with the built `bareblocks.zip`.
   `https://github.com/vkfolio/bareblocks`
2. **Blender Extensions platform** (recommended for a free add-on) —
   `https://extensions.blender.org` lets users install it straight from Blender's
   Get Extensions browser. Submit the same extension.
3. **Superhive / Blender Market** (optional) — you can still list it at price **$0** for reach.

If you only do one, do GitHub releases; add Blender Extensions for one-click discovery.

## Blender compatibility
Minimum **4.2.0**; tested through **5.1**. Ships as the new extension format
(`blender_manifest.toml`).

## Tags
blockout, greybox, level design, prototyping, geometry nodes, parametric,
environment, modular, kitbash, game, architecture, procedural, ai

---

## Short description (the listing summary box)

BareBlocks is a parametric greyboxing kit for Blender. Drop in live primitives —
boxes, ramps, stairs, doorways, roads, signage, trees and props — bend roads and
walls along editable splines, and shade everything with a snapping grid material.
Every piece stays Geometry-Nodes editable, so you can re-size and re-route a whole
level right up to final art. A built-in AI assistant even plans and builds scenes
from a prompt, using your own OpenAI key.

---

## Full description (product body)

### Block out levels at the speed of thought

Greyboxing is where a level is won or lost — and it's where Blender slows you down.
BareBlocks turns the N-panel into a complete blockout pipeline: a palette of 42
parametric blocks, in-viewport resize gizmos, spline-driven roads and walls, a
reference grid material, layout tools, and an AI that assembles scenes for you.

Nothing is ever baked. Every block is live Geometry Nodes, so a doorway, a flight
of stairs or an entire road network stays editable as the design changes.

### What you get

**42 parametric blocks, 11 categories**
- Primitives — Box, Plane, Cylinder, Tube, Sphere, Cone (separate top/bottom radius)
- Structural — Wall, Floor, Pillar, Sleeve (taper + skew)
- Ramps & Corners — Ramp (run/width/rise), Corner Curved (convex or scooped inner)
- Openings — Window, Doorway, Arch
- Stairs — Stairs, Stairs Curved (follows a spline, with an angle dial)
- Path — Track (road channel), Railing
- Signage — road Sign, highway Billboard
- Trees — one procedural generator + 11 species presets (Pine, Palm, Oak, Birch,
  Willow, Cypress, Acacia, Cherry, Banyan, Baobab, Bamboo)
- Nature — Bush, Rock
- Structures — Well, Bridge, Tower
- Props — Barrier, Bench, Lamppost, Fountain

**Spline roads, walls & stairs**
Track, Railing, Wall and Curved Stairs follow an editable curve. Tab into Edit Mode
and bend the path — smooth curves or sharp corners. The grid material flows along
the path so cells stay square around bends.

**In-viewport gizmos**
A dedicated BareBlocks mode adds face handles with live cm/m readouts and grid
snapping, right alongside Blender's transform gizmos. Each block also shows handles
for its own parameters (radius, width, wall height, sweep angle…).

**A snapping grid material**
A triplanar grid + checker locked to each block, with minor and major lines for real
measurement. Per-object color, optional top-face tint, or swap in your own material.

**AI scene builder (bring your own OpenAI key)**
Describe a scene; the agent proposes an editable checklist, you approve, and it builds
with the blocks — streaming its reasoning as it works. Base rules keep everything on
the ground, at human scale and evenly spaced. Runs on Blender's bundled Python; nothing
extra to install.

**Layout tools & reusable bundles**
Illustrator-style Align & Distribute in the view plane. Save selections as `.blend`
bundles and register them as an Asset Library for drag-and-drop.

### Built to last
- One registry drives the palette, menus, gizmos and AI — extensible by design.
- Blocks persist with your file and auto-upgrade when node groups change.
- No third-party dependencies. GPL-3.0. Free updates.

---

## Requirements (listing field)
- Blender 4.2 or newer (tested on 5.1)
- For the AI assistant only: an OpenAI API key (optional; the rest works without it)
- No additional Python packages

## What's included (files)
- `bareblocks.zip` — the Blender extension (install from disk)
- Quick-start link to the online documentation

---

## FAQ (for the listing)

**Does the AI cost extra?**
No — you bring your own OpenAI API key and OpenAI bills you for usage. Everything else
works fully without a key.

**Is it destructive?**
Never, until you choose. Blocks are live Geometry Nodes; a one-click "Convert to Mesh"
bakes only when you're ready.

**Can I add my own blocks?**
Yes — the kit is registry-driven. A new type is one entry plus a node-group builder, and
it shows up automatically in the palette, gizmos and AI tools.

**Which Blender versions?**
4.2+ as the new extension format, tested through 5.1.

---

## Image / video checklist for the listing
Upload in this order (first image is the thumbnail):
1. `assets/hero.png` — the isometric greybox scene (main thumbnail)
2. `assets/blocks.png` — the 42-block palette
3. `assets/trees.png` — the 12 tree species
4. `assets/kit.png` — structures & props
5. A short screen-capture GIF/MP4 of: dragging a gizmo to resize, bending a Track
   spline, and the AI plan → build flow (record from Blender 5.1)

## Links to set on the listing
- Website / docs: **https://vkfolio.github.io/bareblocks** (e.g. https://bareblocks.app)
- Documentation: **[your URL]/docs.html**
- Support email: **[your email]**
