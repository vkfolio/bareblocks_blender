# BareBlocks - View3D sidebar panels (Add / Blockout Tools / Blockout Material).

import bpy

from ..core.ids import (LABELS, PARAM_LAYOUT, BLOCK_TYPES, CATEGORY_ORDER, CURVE_TYPES,
                        types_in_category, TOOL_IDNAME)
from ..core.sockets import socket_id, get_modifier, mod_value, is_bareblocks
from ..nodegroups.shader_blockout import get_shader_group_node
from .icons import icon_id

CATEGORY = "BareBlocks"


class VIEW3D_PT_bareblocks_add(bpy.types.Panel):
    bl_label = "Add Blockout"
    bl_idname = "VIEW3D_PT_bareblocks_add"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CATEGORY

    def draw(self, context):
        layout = self.layout

        # Enter / exit the BareBlocks toolbar tool ("mode").
        from ..gizmos.resize import tool_is_active
        mode_on = tool_is_active(context)
        row = layout.row(align=True)
        row.scale_y = 1.3
        if mode_on:
            op = row.operator("wm.tool_set_by_id", text="Exit BareBlocks Mode", icon="LOOP_BACK")
            op.name = "builtin.select_box"
        else:
            op = row.operator("wm.tool_set_by_id", text="Enter BareBlocks Mode", icon="TOOL_SETTINGS")
            op.name = TOOL_IDNAME

        # Palette: a big-thumbnail picker per category. Click the preview to open a grid of
        # large clickable icons; clicking one adds the block.
        from ..core.props import palette_prop
        settings = context.scene.bareblocks
        for category in CATEGORY_ORDER:
            if not types_in_category(category):
                continue
            layout.separator(factor=0.6)
            layout.label(text=category.upper())
            layout.template_icon_view(settings, palette_prop(category),
                                      show_labels=True, scale=7.0, scale_popup=6.0)

        layout.separator(factor=0.6)
        layout.label(text="SETTINGS")
        box = layout.box().column(align=True)
        box.prop(settings, "place_at_cursor")
        box.prop(settings, "snap_grid")


def _draw_gn_inputs(layout, obj):
    mod = get_modifier(obj)
    ng = mod.node_group
    for entry in PARAM_LAYOUT.get(obj["bareblocks_type"], []):
        if isinstance(entry, (list, tuple)):
            row = layout.row(align=True)
            for name in entry:
                sid = socket_id(ng, name)
                row.prop(mod, f'["{sid}"]', text=name.split()[-1])
        else:
            sid = socket_id(ng, entry)
            layout.prop(mod, f'["{sid}"]', text=entry)


class VIEW3D_PT_bareblocks_edit(bpy.types.Panel):
    bl_label = "Blockout Tools"
    bl_idname = "VIEW3D_PT_bareblocks_edit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CATEGORY

    @classmethod
    def poll(cls, context):
        return is_bareblocks(context.active_object)

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        box = layout.box()
        box.label(text=f"Blockout {LABELS[obj['bareblocks_type']]}", icon="MODIFIER_DATA")
        _draw_gn_inputs(box, obj)

        # Curve-based types (Track/Railing): point the user at Edit Mode to bend the path.
        if obj["bareblocks_type"] in CURVE_TYPES:
            tip = box.column(align=True)
            tip.label(text="Tab into Edit Mode to bend the path", icon="CURVE_PATH")
            tip.label(text="Add points: select all, Subdivide / Extrude", icon="DOT")

        layout.separator()
        layout.operator("bareblocks.convert_to_mesh", icon="MESH_DATA")


class VIEW3D_PT_bareblocks_material(bpy.types.Panel):
    bl_label = "Blockout Material"
    bl_idname = "VIEW3D_PT_bareblocks_material"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CATEGORY
    bl_parent_id = "VIEW3D_PT_bareblocks_edit"

    BLOCKOUT_PARAMS = [
        "Color", "Use Grid", "World Aligned", "Grid Size", "Major Every",
        "Checker Luminance", "Roughness", "Use Top Color",
    ]

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        settings = context.scene.bareblocks

        mat = mod_value(obj, "Material")
        gnode = get_shader_group_node(mat) if mat else None

        if gnode is None:
            layout.label(text="Custom material in use", icon="MATERIAL")
        else:
            col = layout.column(align=True)
            for name in self.BLOCKOUT_PARAMS:
                col.prop(gnode.inputs[name], "default_value", text=name)
            sub = col.column(align=True)
            sub.active = bool(gnode.inputs["Use Top Color"].default_value)
            sub.prop(gnode.inputs["Top Color"], "default_value", text="Top Color")

        layout.separator()
        layout.prop(settings, "custom_material", text="Custom")
        row = layout.row(align=True)
        row.operator("bareblocks.assign_custom", text="Use Custom")
        row.operator("bareblocks.reset_material", text="Reset")
        layout.operator("bareblocks.material_make_unique", icon="DUPLICATE")


class VIEW3D_PT_bareblocks_align(bpy.types.Panel):
    bl_label = "Align & Distribute"
    bl_idname = "VIEW3D_PT_bareblocks_align"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CATEGORY

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and len(context.selected_objects) >= 2

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bareblocks
        layout.prop(settings, "align_to", text="")

        layout.label(text="Align (view plane)")
        col = layout.column(align=True)
        row = col.row(align=True)
        for mode, icon in (("LEFT", "ANCHOR_LEFT"), ("HCENTER", "ANCHOR_CENTER"),
                           ("RIGHT", "ANCHOR_RIGHT")):
            row.operator("bareblocks.align", text="", icon=icon).mode = mode
        row = col.row(align=True)
        for mode, icon in (("TOP", "ANCHOR_TOP"), ("VCENTER", "ANCHOR_CENTER"),
                           ("BOTTOM", "ANCHOR_BOTTOM")):
            row.operator("bareblocks.align", text="", icon=icon).mode = mode

        layout.label(text="Distribute centers")
        row = layout.row(align=True)
        row.operator("bareblocks.distribute", text="Horizontal",
                     icon="ARROW_LEFTRIGHT").mode = "HORIZONTAL"
        d = row.operator("bareblocks.distribute", text="Vertical", icon="EMPTY_SINGLE_ARROW")
        d.mode = "VERTICAL"


class VIEW3D_PT_bareblocks_bundles(bpy.types.Panel):
    bl_label = "Bundles"
    bl_idname = "VIEW3D_PT_bareblocks_bundles"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CATEGORY
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bareblocks

        save = layout.box()
        save.label(text="Save selection as bundle", icon="EXPORT")
        save.prop(settings, "bundle_name", text="")
        save.operator("bareblocks.save_bundle", icon="FILE_TICK")

        imp = layout.box()
        imp.label(text="Import bundle", icon="IMPORT")
        row = imp.row(align=True)
        row.prop(settings, "bundle_enum", text="")
        row.operator("bareblocks.refresh_bundles", text="", icon="FILE_REFRESH")
        imp.operator("bareblocks.import_bundle", icon="APPEND_BLEND")

        col = layout.column(align=True)
        col.operator("bareblocks.register_asset_library", icon="ASSET_MANAGER")
        col.operator("bareblocks.open_bundle_dir", icon="FILE_FOLDER")


class VIEW3D_PT_bareblocks_ai(bpy.types.Panel):
    bl_label = "AI Assistant"
    bl_idname = "VIEW3D_PT_bareblocks_ai"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = CATEGORY

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bareblocks
        from ..core.props import get_prefs
        prefs = get_prefs(context)

        if not prefs or not prefs.openai_api_key.strip():
            layout.label(text="Set OpenAI key in Preferences", icon="ERROR")
            layout.operator("screen.userpref_show", text="Open Preferences", icon="PREFERENCES")

        layout.label(text="Describe the scene to build / edit:")
        layout.prop(settings, "ai_prompt", text="")

        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator("bareblocks.ai_run", text="Plan", icon="OUTLINER_OB_LIGHT").mode = "PLAN"
        b = row.operator("bareblocks.ai_run", text="Build directly", icon="PLAY")
        b.mode = "BUILD"

        # Editable, checkable plan: uncheck to skip, edit text inline, add / remove steps.
        steps = settings.ai_plan_steps
        if len(steps):
            box = layout.box()
            box.label(text="Plan - edit / uncheck, then approve:", icon="TEXT")
            col = box.column(align=True)
            for i, step in enumerate(steps):
                r = col.row(align=True)
                r.prop(step, "enabled", text="")
                r.prop(step, "text", text="")
                r.operator("bareblocks.ai_step_remove", text="", icon="X", emboss=False).index = i
            box.operator("bareblocks.ai_step_add", text="Add Step", icon="ADD")
            arow = box.row(align=True)
            arow.scale_y = 1.4
            arow.operator("bareblocks.ai_run", text="Approve & Build", icon="CHECKMARK").mode = "BUILD"
            sub = box.row(align=True)
            sub.operator("bareblocks.ai_run", text="Re-plan", icon="FILE_REFRESH").mode = "PLAN"
            sub.operator("bareblocks.ai_clear", text="Clear", icon="TRASH")

        if settings.ai_log:
            lbox = layout.box()
            lbox.label(text="Activity:", icon="CONSOLE")
            lcol = lbox.column(align=True)
            lcol.scale_y = 0.6
            for line in settings.ai_log.splitlines()[-8:]:
                lcol.label(text=line)

        if settings.ai_status:
            sbox = layout.box()
            sbox.scale_y = 0.8
            for line in _wrap(settings.ai_status, 40):
                sbox.label(text=line)


def _wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines[:8] or [""]


classes = [
    VIEW3D_PT_bareblocks_add,
    VIEW3D_PT_bareblocks_edit,
    VIEW3D_PT_bareblocks_material,
    VIEW3D_PT_bareblocks_align,
    VIEW3D_PT_bareblocks_bundles,
    VIEW3D_PT_bareblocks_ai,
]
