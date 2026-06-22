# BareBlocks - scene-level settings and add-on preferences.

import bpy

# Filled lazily by the bundles module so the EnumProperty callback stays import-light and
# its returned strings keep a stable reference (avoids the Blender enum-callback GC bug).
_bundle_items_cache = [("", "(no bundles)", "")]


def _bundle_items():
    return _bundle_items_cache


class BareBlocksPlanStep(bpy.types.PropertyGroup):
    """One reviewable/editable line of the AI build plan."""
    text: bpy.props.StringProperty(name="Step", default="")
    enabled: bpy.props.BoolProperty(name="", default=True,
                                    description="Include this step when building")


class BareBlocksSceneProps(bpy.types.PropertyGroup):
    place_at_cursor: bpy.props.BoolProperty(
        name="At 3D Cursor",
        description="Spawn new primitives at the 3D cursor instead of the world origin",
        default=True,
    )
    snap_grid: bpy.props.BoolProperty(
        name="Snap to Grid",
        description="Snap new / dropped primitives to whole units",
        default=False,
    )
    interactive_place: bpy.props.BoolProperty(
        name="Click to Place",
        description="After clicking a palette tile, move and click in the viewport to drop the "
                    "block (off = add instantly at the origin / 3D cursor)",
        default=True,
    )
    custom_material: bpy.props.PointerProperty(
        name="Custom Material",
        type=bpy.types.Material,
        description="Material assigned by 'Use Custom Material'",
    )
    align_to: bpy.props.EnumProperty(
        name="Align To",
        description="What the Align / Distribute buttons measure against",
        items=[
            ("SELECTION", "Selection", "The combined bounds of all selected objects"),
            ("ACTIVE", "Active (Key)", "The active object (Illustrator's 'key object')"),
        ],
        default="SELECTION",
    )
    bundle_name: bpy.props.StringProperty(
        name="Bundle Name",
        description="File name for the bundle saved from the selection",
        default="my_bundle",
    )
    bundle_enum: bpy.props.EnumProperty(
        name="Bundle",
        description="A saved bundle to import",
        items=lambda self, context: _bundle_items(),
    )
    ai_prompt: bpy.props.StringProperty(
        name="Prompt",
        description="Describe the environment to build or edit (e.g. 'a race track loop with railings')",
        default="",
    )
    ai_plan_steps: bpy.props.CollectionProperty(type=BareBlocksPlanStep)
    ai_log: bpy.props.StringProperty(
        name="AI Log",
        description="Live log of what the agent is doing",
        default="",
    )
    ai_status: bpy.props.StringProperty(
        name="AI Status",
        description="Latest AI agent status / reply",
        default="",
    )


class BareBlocksPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__.rsplit(".", 1)[0]  # the top-level add-on package

    snap_coarse: bpy.props.FloatProperty(
        name="Shift Snap (units)",
        description="Increment used while holding Shift during a gizmo drag",
        default=1.0,
        min=0.001,
    )
    snap_fine: bpy.props.FloatProperty(
        name="Ctrl Snap (units)",
        description="Fine increment used while holding Ctrl during a gizmo drag",
        default=0.1,
        min=0.001,
    )
    bundle_dir: bpy.props.StringProperty(
        name="Bundle Folder",
        description="Where Save/Import Bundle reads and writes .blend bundles "
                    "(blank = a folder in your Blender user data)",
        subtype="DIR_PATH",
        default="",
    )
    openai_api_key: bpy.props.StringProperty(
        name="OpenAI API Key",
        description="Your OpenAI API key (kept in Blender preferences, sent only to OpenAI)",
        subtype="PASSWORD",
        default="",
    )
    openai_model: bpy.props.StringProperty(
        name="Model",
        description="OpenAI model with tool-calling (e.g. gpt-4o, gpt-4.1, gpt-4o-mini)",
        default="gpt-4o",
    )
    ai_max_steps: bpy.props.IntProperty(
        name="Max Steps",
        description="Safety cap on agent tool-call rounds per run",
        default=14, min=1, max=60,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Gizmo drag snapping increments:")
        col.prop(self, "snap_coarse")
        col.prop(self, "snap_fine")
        layout.separator()
        layout.prop(self, "bundle_dir")
        layout.separator()
        box = layout.box()
        box.label(text="AI Assistant", icon="OUTLINER_OB_LIGHT")
        box.prop(self, "openai_api_key")
        row = box.row(align=True)
        row.prop(self, "openai_model")
        row.prop(self, "ai_max_steps")
        box.label(text="Key is stored in Blender prefs and sent only to api.openai.com.", icon="INFO")
        layout.separator()
        layout.label(text="Add primitives from the View3D > Sidebar > BareBlocks tab, or Shift+A.")


def get_prefs(context=None):
    context = context or bpy.context
    addon = context.preferences.addons.get(BareBlocksPrefs.bl_idname)
    return addon.preferences if addon else None


# --------------------------------------------------------------------------- #
# Palette pickers - one thumbnail-view EnumProperty per category. Clicking a big
# icon in the popup adds that block. The first ("__cover__") item is a no-op cover
# the inline preview shows; after an add we reset to it so the same type can be
# re-picked. Properties are added to the PropertyGroup annotations before register.
# --------------------------------------------------------------------------- #
_palette_cache = {}  # category -> items list (keep a ref so enum strings don't get GC'd)


def palette_prop(category):
    return "pick_" + "".join(c if c.isalnum() else "_" for c in category)


def _palette_items(category):
    def items(self, context):
        from . import ids
        from ..ui.icons import icon_id
        types = ids.types_in_category(category)
        cover = icon_id(ids.BLOCK_TYPES[types[0]]["icon"]) if types else 0
        lst = [("__cover__", category, "Pick a " + category + " block", cover, 0)]
        for i, t in enumerate(types):
            spec = ids.BLOCK_TYPES[t]
            lst.append((t, spec["label"], spec["label"], icon_id(spec["icon"]), i + 1))
        _palette_cache[category] = lst
        return lst
    return items


def _palette_update(prop):
    def update(self, context):
        val = getattr(self, prop)
        if not val or val == "__cover__":
            return
        from . import ids
        from ..operators.add_primitives import create_primitive
        if val in ids.BLOCK_TYPES:
            create_primitive(context, val)
        self[prop] = 0  # reset to the cover (raw set -> no re-trigger), so re-picking works
    return update


def _register_palette_props():
    from . import ids
    for cat in ids.CATEGORY_ORDER:
        BareBlocksSceneProps.__annotations__[palette_prop(cat)] = bpy.props.EnumProperty(
            name=cat, items=_palette_items(cat), update=_palette_update(palette_prop(cat)))


_register_palette_props()


classes = [BareBlocksPlanStep, BareBlocksSceneProps, BareBlocksPrefs]


def register_props():
    bpy.types.Scene.bareblocks = bpy.props.PointerProperty(type=BareBlocksSceneProps)


def unregister_props():
    del bpy.types.Scene.bareblocks
