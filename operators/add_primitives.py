# BareBlocks - one registry-driven "Add" operator for every block type.
#
# A single operator (bareblocks.add) takes a bb_type and builds the object from the
# registry in core.ids: it picks mesh vs curve, assigns the type's GN group, applies any
# preset default sockets, and gives the object its own material copy. New types need no
# new operator - just a registry entry + a builder in nodegroups/builders.py.

import bpy
from mathutils import Vector
from mathutils.geometry import intersect_line_plane
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d

from ..core.ids import MOD_NAME, GN_VERSION, BLOCK_TYPES, CURVE_TYPES, LABELS, _defaults
from ..core.collections import link_object
from ..core.sockets import set_mod
from ..nodegroups.shader_blockout import ensure_material
from ..nodegroups.builders import ensure_group_for


def _new_path_curve(name, length=4.0):
    """A straight 2-point bezier spline centred on the origin, ready to bend in Edit Mode."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 16
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(1)
    sp.bezier_points[0].co = (-length / 2.0, 0.0, 0.0)
    sp.bezier_points[1].co = (length / 2.0, 0.0, 0.0)
    for bp in sp.bezier_points:
        bp.handle_left_type = bp.handle_right_type = "AUTO"
    return cu


def _new_arc_curve(name, radius=3.0):
    """A 90-degree bezier arc, so curved-path types (Stairs Curved) spiral by default."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.resolution_u = 16
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(1)
    k = radius * 0.5523  # cubic handle length for a quarter circle
    p0, p1 = sp.bezier_points
    p0.co = (radius, 0.0, 0.0)
    p0.handle_right = (radius, k, 0.0)
    p0.handle_left = (radius, -k, 0.0)
    p1.co = (0.0, radius, 0.0)
    p1.handle_left = (k, radius, 0.0)
    p1.handle_right = (-k, radius, 0.0)
    for bp in (p0, p1):
        bp.handle_left_type = bp.handle_right_type = "FREE"
    return cu


def create_primitive(context, bb_type):
    spec = BLOCK_TYPES[bb_type]
    ng = ensure_group_for(bb_type)
    name = spec.get("obj", spec["group"])

    if bb_type in CURVE_TYPES:
        if spec.get("curve_default") == "arc":
            data = _new_arc_curve(name)
        else:
            data = _new_path_curve(name)
    else:
        data = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, data)
    obj["bareblocks_type"] = bb_type
    obj["bareblocks_version"] = GN_VERSION

    mod = obj.modifiers.new(MOD_NAME, "NODES")
    mod.node_group = ng

    # Each primitive gets its own material instance (sharing the heavy shader node
    # group) so editing its color/params is per-object, not global.
    mat = ensure_material().copy()
    mat.name = "BB_Blockout"
    set_mod(obj, "Material", mat, tag=False)

    # Preset default sockets (e.g. Wall / Floor / Pillar reuse the Box group with sizes).
    for socket, value in _defaults(bb_type).items():
        set_mod(obj, socket, value, tag=False)

    link_object(obj)

    settings = context.scene.bareblocks
    loc = context.scene.cursor.location.copy() if settings.place_at_cursor else Vector((0.0, 0.0, 0.0))
    if settings.snap_grid:
        loc = Vector((round(loc.x), round(loc.y), round(loc.z)))
    obj.location = loc

    for o in context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    return obj


class BAREBLOCKS_OT_add(bpy.types.Operator):
    bl_idname = "bareblocks.add"
    bl_label = "Add Blockout"
    bl_description = "Add a parametric blockout primitive"
    bl_options = {"REGISTER", "UNDO"}

    bb_type: bpy.props.StringProperty(default="BOX", options={"HIDDEN"})
    interactive: bpy.props.BoolProperty(default=False, options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    @classmethod
    def description(cls, context, properties):
        spec = BLOCK_TYPES.get(properties.bb_type)
        return f"Add a parametric blockout {spec['label']}" if spec else cls.bl_description

    def execute(self, context):
        if self.bb_type not in BLOCK_TYPES:
            self.report({"ERROR"}, f"Unknown block type: {self.bb_type}")
            return {"CANCELLED"}
        create_primitive(context, self.bb_type)
        self.report({"INFO"}, f"Added {LABELS[self.bb_type]}")
        return {"FINISHED"}

    # --- interactive "drop" placement: follow the cursor on the ground, click to drop ---
    def invoke(self, context, event):
        if self.bb_type not in BLOCK_TYPES:
            self.report({"ERROR"}, f"Unknown block type: {self.bb_type}")
            return {"CANCELLED"}
        if not self.interactive:
            return self.execute(context)
        region, rv3d = self._find_view3d(context)
        if region is None:
            return self.execute(context)
        self._region, self._rv3d = region, rv3d
        self._obj = create_primitive(context, self.bb_type)
        self._z = self._obj.location.z
        if context.area:
            context.area.header_text_set(f"Place {LABELS[self.bb_type]}: move + click to drop, "
                                         "Esc/right-click to cancel")
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    @staticmethod
    def _find_view3d(context):
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                rv3d = area.spaces.active.region_3d
                for region in area.regions:
                    if region.type == "WINDOW":
                        return region, rv3d
        return None, None

    def _drop_point(self, context, event):
        region, rv3d = self._region, self._rv3d
        co = (event.mouse_x - region.x, event.mouse_y - region.y)
        origin = region_2d_to_origin_3d(region, rv3d, co)
        direction = region_2d_to_vector_3d(region, rv3d, co)
        hit = intersect_line_plane(origin, origin + direction,
                                   Vector((0.0, 0.0, self._z)), Vector((0.0, 0.0, 1.0)))
        return hit

    def modal(self, context, event):
        if event.type in {"MIDDLEMOUSE", "WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            return {"PASS_THROUGH"}
        if event.type == "MOUSEMOVE":
            p = self._drop_point(context, event)
            if p is not None:
                if context.scene.bareblocks.snap_grid:
                    p = Vector((round(p.x), round(p.y), p.z))
                self._obj.location = Vector((p.x, p.y, self._z))
                self._region.tag_redraw()
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            if context.area:
                context.area.header_text_set(None)
            return {"FINISHED"}
        if event.type in {"RIGHTMOUSE", "ESC"}:
            bpy.data.objects.remove(self._obj, do_unlink=True)
            if context.area:
                context.area.header_text_set(None)
            return {"CANCELLED"}
        return {"RUNNING_MODAL"}


classes = [BAREBLOCKS_OT_add]
