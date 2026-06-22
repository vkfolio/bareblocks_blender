# BareBlocks - Shift+A submenu (grouped by category) and optional pie menu.

import bpy

from ..core.ids import BLOCK_TYPES, CATEGORY_ORDER, types_in_category
from .icons import icon_id


def _op(layout, bb_type):
    spec = BLOCK_TYPES[bb_type]
    iid = icon_id(spec["icon"])
    if iid:
        op = layout.operator("bareblocks.add", text=spec["label"], icon_value=iid)
    else:
        op = layout.operator("bareblocks.add", text=spec["label"], icon=spec["stock"])
    op.bb_type = bb_type


class VIEW3D_MT_bareblocks_add(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_bareblocks_add"
    bl_label = "BareBlocks"

    def draw(self, context):
        layout = self.layout
        first = True
        for category in CATEGORY_ORDER:
            types = types_in_category(category)
            if not types:
                continue
            if not first:
                layout.separator()
            first = False
            layout.label(text=category)
            for bb_type in types:
                _op(layout, bb_type)


class VIEW3D_MT_bareblocks_pie(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_bareblocks_pie"
    bl_label = "BareBlocks"

    def draw(self, context):
        pie = self.layout.menu_pie()
        # Pie has 8 slots: surface the first type of each category as a quick-add.
        for category in CATEGORY_ORDER:
            types = types_in_category(category)
            if types:
                _op(pie, types[0])


def menu_add(self, context):
    self.layout.menu("VIEW3D_MT_bareblocks_add", icon="MESH_CUBE")


classes = [VIEW3D_MT_bareblocks_add, VIEW3D_MT_bareblocks_pie]
