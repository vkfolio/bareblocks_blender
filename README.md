# BareBlocks

Parametric **blockout / greyboxing** primitives for Blender — a native recreation of the
Unreal Engine *Blockout Tools* plugin. Each primitive is driven by **Geometry Nodes**, so its
dimensions stay live and editable, and they all share a procedural **triplanar grid + checker
material**. Interactive viewport gizmos let you drag faces to resize, with snapping and a
measurement readout.

Built for **Blender 4.2+** (developed and tested on Blender 5.1).

## Block types

Declared once each in a central **registry** (`core/ids.py` ▸ `BLOCK_TYPES`); the Add palette,
Shift-A menu, edit panel and gizmos are all generated from it, so a new type is a registry entry plus
one Geometry-Nodes builder. The palette groups them by category with custom rendered thumbnails.

| Category | Types | Parameters |
|----------|-------|------------|
| **Primitives** | Box · Plane · Cylinder · Tube · Sphere · Cone | sizes / Radius / Height / Sides / Wall Thickness / Quality / Is Hemisphere; **Cone** = Bottom Radius + Top Radius (frustum) |
| **Structural** | Wall · Floor · Pillar · Sleeve | **Wall** = a slab swept along an editable spline — **curved** (smooth handles) or **angled** (sharp corners via Vector/Poly handles); Floor/Pillar = Box presets; **Sleeve** = Length / Start / End Size (taper) + **Skew Y / Skew Z** (sheared beam) |
| **Ramps & Corners** | Ramp · Corner Curved | Ramp = X(run)/Y(width)/Z(rise); Corner Curved = Radius / Height / Quality / Is Inner |
| **Openings** | Window · Doorway · Arch | Size X/Y/Z + Top / Bottom / Side Thickness. Doorway = floor-to-top rectangular opening; **Arch** = floor-to-crown opening with a semicircular top |
| **Signage** | Sign · Billboard | **Sign** = post + board (road sign); **Billboard** = two legs + a big board (highway hoarding) |
| **Trees** | Tree + Pine · Palm · Oak · Birch · Willow · Cypress · Acacia · Cherry · Banyan · Baobab · Bamboo | one procedural generator — tapered trunk (+ multi-trunk ring), a **Canopy Shape** (Sphere / Cone / Column / Umbrella / Fronds / None), Width / Height / Droop. Species are presets of it |
| **Nature** | Bush · Rock | Bush = squashed dome; Rock = noise-displaced boulder |
| **Structures** | Well · Bridge · Tower | Well = hollow ring; Bridge = deck + piers + side rails; Tower = column + cap |
| **Props** | Barrier · Bench · Lamppost · Fountain | road barrier (tapered), park bench, street lamp, tiered fountain |
| **Stairs** | Stairs · Stairs Curved | Straight: Steps / Width / Step Height / Step Depth. **Stairs Curved follows an editable spline** (default arc — Tab in to bend the path), Step Width / Step Height. Both: **Fill Bottom** (solid vs floating treads), **Side Rails** (Rail Height / Thickness / **Post Spacing**) |
| **Path** (curve) | Track · Railing | follow an **editable spline** — Tab into Edit Mode to bend the path. Track has optional **Side Rails** (posts + rail along both walls, Post Spacing) |

- **Path types** (Track, Railing) *are* curve objects: their spline is the path. **Tab** into Edit Mode
  and drag / add / extrude points; the profile sweeps along live. **Track** = a channel (floor + side
  walls); **Railing** = posts + top/bottom rails.
- **Corner Curved** is a solid rounded corner: convex quarter-cylinder by default, concave (scooped) with
  *Is Inner*. **Window/Doorway** leave a connected frame. **Wall/Floor/Pillar** reuse the Box group with
  preset sizes.

Shared **Blockout Material**: Color, Use Grid, World Aligned, Grid Size, Checker Luminance,
Roughness, Use Top Color, Top Color (+ per-object Custom material / Make Unique).

## AI Assistant (OpenAI)

A built-in agent that builds and edits the scene from a natural-language prompt — *"a race
track loop with railings and a billboard"*, then *"make the walls taller"*.

- **Setup:** paste your **OpenAI API key** in *Preferences ▸ Add-ons ▸ BareBlocks* (also set the
  model, default `gpt-4o`). The key is stored in Blender preferences and sent only to
  `api.openai.com`.
- **Use:** Sidebar ▸ **BareBlocks ▸ AI Assistant**. Type a prompt and:
  1. **Plan** → the agent returns an editable **checklist**. Tweak any step's text, **uncheck**
     steps to skip them, add/remove steps.
  2. **Approve & Build** → it executes only the enabled steps, streaming a live **Activity** log
     ("[v] added BB_Track…"). **Re-plan** regenerates from the prompt; **Build directly** skips
     planning for quick edits.
- The build is a **ReAct loop** over the model's tool-calling: `add_block`, `edit_block`,
  `move_block`, `set_color`, `shape_path` (bend Track/Wall/Railing/Stairs Curved through points),
  `delete_block`, `list_blocks`. The tools and the type catalogue are **auto-generated from the
  block registry**, so every block type (and any you add later) is available automatically.
- The model's **reasoning streams** into the Activity log as it works. The system prompt carries
  **base rules** (ground = z 0, per-type anchoring so pieces sit on the floor, human scale, even
  spacing, no overlaps) so plans and builds are sensible.
- **No packages to install** — it uses Blender's bundled Python (`urllib`) and runs the HTTP
  call on a background thread, so Blender doesn't freeze. Press **Esc** to cancel a run; a step
  cap (Preferences) bounds each run.

## Bundles (save / load / asset library)

The **Bundles** panel turns a selection into a reusable prefab:
- **Save Bundle** — writes the selected objects to a `.blend` in the bundle folder (and marks them as
  assets). Name it in the field first.
- **Import Bundle** — pick a saved bundle from the dropdown and append it into the scene.
- **Register Asset Library** — adds the bundle folder to Blender's Asset Libraries so bundles appear in
  the **Asset Browser** for drag-drop.
- The bundle folder defaults to your Blender user data; change it in the add-on Preferences.

## Install

1. Zip the `bareblocks` folder (the one containing `blender_manifest.toml`).
2. Blender → **Edit ▸ Preferences ▸ Get Extensions ▸ Install from Disk…** → pick the zip.
3. Enable **BareBlocks** if it isn't already.

(During development you can also point Blender at the folder directly via
*Preferences ▸ File Paths ▸ Script Directories* and enable it as a legacy add-on.)

## Usage

- **Add:** View3D **Sidebar (N) ▸ BareBlocks** tab — click a primitive. Also under **Shift+A ▸ BareBlocks**.
- **Edit dimensions:** select a primitive → the **Blockout Tools** panel (or the Modifier panel)
  exposes its live parameters.
- **Material:** the **Blockout Material** sub-panel edits the shared grid material (affects all
  primitives). *Make Material Unique* detaches an editable copy for the active object; *Use Custom*
  assigns the chosen material to the selection.
- **BareBlocks mode:** click **Enter BareBlocks Mode** at the top of the N-panel (or pick the
  **BareBlocks** tool from the left toolbar, press **T**). In the mode:
  - Blender's **move / rotate / scale** gizmos stay on (the full transform gizmo) **and** BareBlocks
    **face handles** appear on the active primitive — both together, like Unreal.
  - Drag a face handle to live-edit that size. By default the **opposite face stays anchored** (grows
    from one side); hold **Alt** to grow **symmetrically** from the center.
  - Hold **Shift** → snap to the **major** grid lines (Grid Size × Major Every); **Ctrl** → snap to the
    **minor** grid lines (one cell). A header readout shows the live size (`Size X: 1.10 m` / `40.0 cm`).
  - **Per-type special handles:** each type shows handles for *its* parameters — Cylinder/Sphere/Corner
    **Radius**, Track **Width / Wall Height**, Railing **Height**, Stairs **Width**, Curved Stairs
    **Inner Radius**, etc. Curved Stairs also shows an **angle dial** for **Sweep Angle** (drag to spin
    the staircase; the header shows the degrees).
- **Convert to Mesh:** bakes the selected primitives into plain editable meshes (Blockout Tools panel).
- **Align & Distribute:** with 2+ objects selected, the **Align & Distribute** panel (Sidebar ▸ BareBlocks)
  works like Illustrator — in the **view plane**. Align Left / Center / Right and Top / Center / Bottom
  use the current view's screen axes, so in an **orthographic** view (Front / Top / Right — numpad 1/7/3)
  they behave as a true 2D layout tool. *Distribute* evenly spaces the selected objects' centers
  horizontally or vertically (the two outermost stay put). *Align To* chooses the reference: the whole
  **Selection** bounds, or the **Active** object (Illustrator's "key object"). Works on any objects, using
  each one's live evaluated bounds.

### Grid material

The grid is a **fixed reference grid locked to each block** (it doesn't swim when you move or rotate a
block; resizing just reveals more/fewer cells). It has **minor lines** every cell and brighter
**major lines** every *Major Every* cells, to help snapping — switch *World Aligned* on if you prefer a
single world-space grid shared across all blocks.

## Pie menu (optional)

A pie menu `VIEW3D_MT_bareblocks_pie` is registered but bound to no key by default. Assign one via
*Preferences ▸ Keymap* (call menu: `wm.call_menu_pie`, name `VIEW3D_MT_bareblocks_pie`).

## Tests

Headless checks (from the repo root, the folder *above* `bareblocks`):

```
blender --background --factory-startup --python tests/smoke.py          # builders + eval
blender --background --factory-startup --python tests/ops_test.py       # operators + convert
blender --background --factory-startup --python tests/render_preview.py # writes tests/preview.png
```

## Notes / limitations

- **Track / Corner Curved** are built by sweeping a solid profile along a curve (Curve to Mesh with
  *Fill Caps*); on a Track, smaller **Segment Length** = smoother bends.
- Roadmap primitives (not in v1): Cylinder, Doorway, Railing, Shadow, Stairs Curved, Tube.
