# BareBlocks - material assignment operators (shared / custom / unique).

import bpy

from ..core.sockets import set_mod, is_bareblocks
from ..nodegroups.shader_blockout import ensure_material, get_shader_group_node


def _selected_primitives(context):
    return [o for o in context.selected_objects if is_bareblocks(o)]


class BAREBLOCKS_OT_assign_custom(bpy.types.Operator):
    bl_idname = "bareblocks.assign_custom"
    bl_label = "Use Custom Material"
    bl_description = "Assign the chosen Custom Material to the selected blockout primitives"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.bareblocks.custom_material is not None and _selected_primitives(context)

    def execute(self, context):
        mat = context.scene.bareblocks.custom_material
        for obj in _selected_primitives(context):
            set_mod(obj, "Material", mat)
        return {"FINISHED"}


class BAREBLOCKS_OT_reset_material(bpy.types.Operator):
    bl_idname = "bareblocks.reset_material"
    bl_label = "Reset to Blockout Material"
    bl_description = "Reassign the shared Blockout material to the selected primitives"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return bool(_selected_primitives(context))

    def execute(self, context):
        for obj in _selected_primitives(context):
            mat = ensure_material().copy()
            mat.name = "BB_Blockout"
            set_mod(obj, "Material", mat)
        return {"FINISHED"}


class BAREBLOCKS_OT_material_make_unique(bpy.types.Operator):
    bl_idname = "bareblocks.material_make_unique"
    bl_label = "Make Material Unique"
    bl_description = "Give the active primitive its own editable copy of the Blockout material"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return is_bareblocks(context.active_object)

    def execute(self, context):
        mat = ensure_material().copy()
        gnode = get_shader_group_node(mat)
        if gnode is not None and gnode.node_tree is not None:
            gnode.node_tree = gnode.node_tree.copy()
        set_mod(context.active_object, "Material", mat)
        return {"FINISHED"}


classes = [
    BAREBLOCKS_OT_assign_custom,
    BAREBLOCKS_OT_reset_material,
    BAREBLOCKS_OT_material_make_unique,
]
