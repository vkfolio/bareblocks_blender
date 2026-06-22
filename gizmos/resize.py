# BareBlocks - interactive parameter handles for "BareBlocks mode".
#
# Active only while the BareBlocks toolbar tool is selected. Entering the tool also
# turns on Blender's move/rotate/scale gizmos, so the standard transform gizmo and the
# BareBlocks face handles show together. Drag a face handle to live-edit that size:
#   - default: the opposite face stays anchored (grows from one side, like Unreal)
#   - hold Alt: grow symmetrically from the center
#   - hold Shift: snap to whole units;  Ctrl: snap to the fine increment
# A header readout shows the live measurement.

import math

import bpy
from mathutils import Vector
from mathutils.geometry import intersect_line_line
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d

from ..core.ids import GIZMO_HANDLES, ANGLE_GIZMOS, has_gizmos, TOOL_IDNAME
from ..core.sockets import socket_id, get_modifier, is_bareblocks
from ..core.props import get_prefs
from ..nodegroups.shader_blockout import get_shader_group_node

MIN_SIZE = 0.01
OUT_OFFSET = 0.12  # push handles slightly off the surface so they read clearly
AXIS_VEC = {0: Vector((1.0, 0.0, 0.0)), 1: Vector((0.0, 1.0, 0.0)), 2: Vector((0.0, 0.0, 1.0))}
AXIS_COLOR = {0: (0.95, 0.25, 0.25), 1: (0.35, 0.85, 0.35), 2: (0.3, 0.5, 1.0)}


def format_distance(value):
    a = abs(value)
    return f"{a * 100.0:.1f} cm" if a < 1.0 else f"{a:.2f} m"


def _arrow_shape():
    length, head, rad = 0.85, 0.22, 0.09
    tip = (0.0, 0.0, length)
    bz = length - head
    return [
        (0.0, 0.0, 0.0), tip,
        tip, (rad, 0.0, bz), tip, (-rad, 0.0, bz),
        tip, (0.0, rad, bz), tip, (0.0, -rad, bz),
        (rad, 0.0, bz), (0.0, rad, bz), (0.0, rad, bz), (-rad, 0.0, bz),
        (-rad, 0.0, bz), (0.0, -rad, bz), (0.0, -rad, bz), (rad, 0.0, bz),
    ]


def _value(obj, name):
    mod = get_modifier(obj)
    return mod[socket_id(mod.node_group, name)]


def _set_value(obj, name, value):
    mod = get_modifier(obj)
    mod[socket_id(mod.node_group, name)] = value
    obj.update_tag()


def _make_dial_handlers(socket_name):
    """Read/write an angle socket (stored in degrees) as a dial offset (radians)."""
    def get():
        try:
            return math.radians(_value(bpy.context.active_object, socket_name))
        except Exception:
            return 0.0

    def setv(value):
        try:
            deg = max(1.0, min(360.0, math.degrees(value)))
            _set_value(bpy.context.active_object, socket_name, deg)
            if bpy.context.area:
                bpy.context.area.header_text_set(f"{socket_name}: {deg:.0f} deg")
        except Exception:
            pass

    return get, setv


def tool_is_active(context):
    try:
        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
        return bool(tool) and tool.idname == TOOL_IDNAME
    except Exception:
        return False


class BAREBLOCKS_GT_resize_handle(bpy.types.Gizmo):
    bl_idname = "BAREBLOCKS_GT_resize_handle"
    __slots__ = (
        "socket_name", "axis", "sign", "mode", "anchored", "custom_shape", "_group",
        "_obj", "_center", "_axis_dir", "_start_size", "_start_loc", "_minor", "_major",
    )

    def _ensure_shape(self):
        if not getattr(self, "custom_shape", None):
            self.custom_shape = self.new_custom_shape("LINES", _arrow_shape())

    def draw(self, context):
        self._ensure_shape()
        self.draw_custom_shape(self.custom_shape)

    def draw_select(self, context, select_id):
        self._ensure_shape()
        self.draw_custom_shape(self.custom_shape, select_id=select_id)

    def setup(self):
        self.custom_shape = None

    def _dist(self, value):
        return value * (0.5 if self.mode == "centered" else 1.0)

    def update_matrix(self, obj):
        try:
            value = _value(obj, self.socket_name)
        except Exception:
            return
        mw = obj.matrix_world
        world_axis = (mw.to_3x3() @ AXIS_VEC[self.axis]).normalized() * self.sign
        face_local = AXIS_VEC[self.axis] * (self.sign * self._dist(value))
        pos = (mw @ face_local) + world_axis * OUT_OFFSET
        mat = world_axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
        mat.translation = pos
        self.matrix_basis = mat

    def _project(self, context, event):
        region, rv3d = context.region, context.region_data
        co = (event.mouse_region_x, event.mouse_region_y)
        ray_o = region_2d_to_origin_3d(region, rv3d, co)
        ray_d = region_2d_to_vector_3d(region, rv3d, co)
        hit = intersect_line_line(self._center, self._center + self._axis_dir,
                                  ray_o, ray_o + ray_d)
        return None if hit is None else (hit[0] - self._center).dot(self._axis_dir)

    def invoke(self, context, event):
        obj = context.active_object
        self._obj = obj
        mw = obj.matrix_world
        self._center = mw.translation.copy()
        self._axis_dir = (mw.to_3x3() @ AXIS_VEC[self.axis]).normalized()
        self._start_size = _value(obj, self.socket_name)
        self._start_loc = obj.location.copy()
        # Snap increments come from this block's grid: Shift = major spacing
        # (Grid Size x Major Every), Ctrl = minor spacing (Grid Size).
        self._minor = self._major = None
        try:
            mod = get_modifier(obj)
            mat = mod[socket_id(mod.node_group, "Material")]
            gn = get_shader_group_node(mat)
            gs = float(gn.inputs["Grid Size"].default_value)
            me = int(gn.inputs["Major Every"].default_value)
            self._minor, self._major = gs, gs * me
        except Exception:
            pass
        return {"RUNNING_MODAL"}

    def _snap(self, value, tweak):
        prefs = get_prefs(bpy.context)
        if "PRECISE" in tweak:      # Shift -> major grid lines
            step = self._major or (prefs.snap_coarse if prefs else 1.0)
        elif "SNAP" in tweak:       # Ctrl -> minor grid lines (single cell)
            step = self._minor or (prefs.snap_fine if prefs else 0.1)
        else:
            return value
        return max(MIN_SIZE, round(value / step) * step)

    def modal(self, context, event, tweak):
        t = self._project(context, event)
        if t is None:
            return {"RUNNING_MODAL"}

        symmetric = (not self.anchored) or event.alt or self.mode == "origin"
        if self.mode == "origin":
            new_size = max(MIN_SIZE, self.sign * t)
        elif symmetric:
            new_size = max(MIN_SIZE, 2.0 * self.sign * t)
        else:
            new_size = max(MIN_SIZE, self.sign * t + self._start_size * 0.5)
        new_size = self._snap(new_size, tweak)

        _set_value(self._obj, self.socket_name, new_size)
        if self.mode == "centered" and not symmetric:
            shift = self.sign * (new_size - self._start_size) * 0.5
            self._obj.location = self._start_loc + self._axis_dir * shift
        else:
            self._obj.location = self._start_loc

        # Update every arrow handle so they all track the new size/position together.
        for gz in getattr(self._group, "_handles", ()):
            gz.update_matrix(self._obj)
        if context.area:
            context.area.header_text_set(f"{self.socket_name}: {format_distance(new_size)}")
        return {"RUNNING_MODAL"}

    def exit(self, context, cancel):
        if context.area:
            context.area.header_text_set(None)
        if cancel:
            _set_value(self._obj, self.socket_name, self._start_size)
            self._obj.location = self._start_loc


class BAREBLOCKS_GGT_resize(bpy.types.GizmoGroup):
    bl_idname = "BAREBLOCKS_GGT_resize"
    bl_label = "BareBlocks Resize"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "SHOW_MODAL_ALL"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (
            is_bareblocks(obj)
            and obj.mode == "OBJECT"
            and has_gizmos(obj["bareblocks_type"])
            and tool_is_active(context)
        )

    def _enable_transform_gizmos(self, context):
        sd = context.space_data
        if sd and sd.type == "VIEW_3D":
            sd.show_gizmo = True
            sd.show_gizmo_object_translate = True
            sd.show_gizmo_object_rotate = True
            sd.show_gizmo_object_scale = True

    def _build(self, context):
        self.gizmos.clear()
        obj = context.active_object
        bb_type = self._built_type = obj["bareblocks_type"]

        # Arrow handles for size/length params.
        self._handles = []
        for socket_name, axis, sign, mode, anchored in GIZMO_HANDLES.get(bb_type, ()):
            gz = self.gizmos.new(BAREBLOCKS_GT_resize_handle.bl_idname)
            gz.socket_name = socket_name
            gz.axis = axis
            gz.sign = sign
            gz.mode = mode
            gz.anchored = anchored
            gz._group = self
            gz.color = AXIS_COLOR[axis]
            gz.alpha = 0.9
            gz.color_highlight = tuple(min(1.0, c + 0.25) for c in AXIS_COLOR[axis])
            gz.alpha_highlight = 1.0
            gz.line_width = 3.0
            gz.use_draw_modal = True
            self._handles.append(gz)

        # Dial gizmos for angle params (Blender's built-in dial, bound to the socket).
        self._dials = []
        for socket_name, axis in ANGLE_GIZMOS.get(bb_type, ()):
            try:
                gz = self.gizmos.new("GIZMO_GT_dial_3d")
                gz.draw_options = {"ANGLE_VALUE"}
                gz.color = (1.0, 0.75, 0.15)
                gz.alpha = 0.7
                gz.color_highlight = (1.0, 0.9, 0.4)
                gz.alpha_highlight = 1.0
                gz.line_width = 3.0
                gz.use_draw_modal = True
                get, setv = _make_dial_handlers(socket_name)
                gz.target_set_handler("offset", get=get, set=setv)
                self._dials.append((gz, axis))
            except Exception:
                pass

    def _update_dial(self, gz, axis, obj):
        mw = obj.matrix_world
        loc, rot, _scale = mw.decompose()
        spin = (rot.to_matrix() @ AXIS_VEC[axis]).normalized()
        basis = spin.to_track_quat("Z", "Y").to_matrix().to_4x4()
        basis.translation = loc
        gz.matrix_basis = basis
        try:
            radius = _value(obj, "Inner Radius") + _value(obj, "Step Width")
        except Exception:
            radius = 2.0
        gz.scale_basis = max(0.6, radius)

    def setup(self, context):
        self._enable_transform_gizmos(context)
        self._built_type = None
        self._build(context)

    def refresh(self, context):
        obj = context.active_object
        if not is_bareblocks(obj):
            return
        if getattr(self, "_built_type", None) != obj["bareblocks_type"]:
            self._build(context)
        for gz in self._handles:
            gz.update_matrix(obj)
        for gz, axis in self._dials:
            self._update_dial(gz, axis, obj)


classes = [BAREBLOCKS_GT_resize_handle, BAREBLOCKS_GGT_resize]
