# BareBlocks - the "BareBlocks mode" toolbar tool (active WorkSpaceTool).
#
# Selecting it in the View3D toolbar enters the mode: Blender's transform gizmos are
# shown (the gizmo group's setup turns them on) and the BareBlocks corner handles
# appear on the active primitive. Click selects, drag moves, dragging a corner handle
# resizes the primitive's parameters.

import bpy

from .core.ids import TOOL_IDNAME


class BAREBLOCKS_WT_edit(bpy.types.WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"
    bl_idname = TOOL_IDNAME
    bl_label = "BareBlocks"
    bl_description = "BareBlocks mode: move/rotate/scale and drag corner handles to resize"
    bl_icon = "ops.transform.resize"
    bl_widget = "BAREBLOCKS_GGT_resize"
    bl_keymap = (
        ("view3d.select", {"type": "LEFTMOUSE", "value": "PRESS"},
         {"properties": [("deselect_all", True)]}),
        ("transform.translate", {"type": "LEFTMOUSE", "value": "CLICK_DRAG"},
         {"properties": [("release_confirm", True)]}),
    )

    def draw_settings(context, layout, tool):  # noqa: N805 (Blender signature)
        layout.label(text="Drag corner handles to resize  (Shift = 1u snap, Ctrl = fine)")


def register_tool():
    try:
        bpy.utils.register_tool(BAREBLOCKS_WT_edit, after={"builtin.transform"},
                                separator=True, group=False)
    except Exception:
        bpy.utils.register_tool(BAREBLOCKS_WT_edit, separator=True, group=False)


def unregister_tool():
    try:
        bpy.utils.unregister_tool(BAREBLOCKS_WT_edit)
    except Exception:
        pass
