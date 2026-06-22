# BareBlocks - convert live GN primitives to plain editable meshes.

import bpy

from ..core.sockets import is_bareblocks


class BAREBLOCKS_OT_convert_to_mesh(bpy.types.Operator):
    bl_idname = "bareblocks.convert_to_mesh"
    bl_label = "Convert to Mesh"
    bl_description = "Apply the blockout modifier and bake the selection into editable meshes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and any(is_bareblocks(o) for o in context.selected_objects)

    def execute(self, context):
        targets = [o for o in context.selected_objects if is_bareblocks(o)]
        count = 0
        for obj in targets:
            context.view_layer.objects.active = obj
            bpy.ops.object.convert(target="MESH")
            for key in ("bareblocks_type", "bareblocks_version"):
                if key in obj:
                    del obj[key]
            count += 1
        self.report({"INFO"}, f"Converted {count} blockout primitive(s) to mesh")
        return {"FINISHED"}


classes = [BAREBLOCKS_OT_convert_to_mesh]
