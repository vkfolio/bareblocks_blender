# BareBlocks - Illustrator-style Align & Distribute for the current view plane.
#
# Alignment is measured in SCREEN axes (the view's right / up), so in an orthographic
# view - Front, Top, Right, etc. - "left/right" and "top/bottom" behave exactly like a 2D
# layout tool. Works on any selected objects (uses their evaluated bounds, so it's correct
# for the live Geometry-Nodes blockout primitives whose base mesh is empty).

import bpy
from mathutils import Vector


def _view_axes(context):
    """World-space unit vectors for screen-right and screen-up, or None outside a 3D view."""
    sd = context.space_data
    if not sd or sd.type != "VIEW_3D" or sd.region_3d is None:
        return None
    rot = sd.region_3d.view_rotation
    right = (rot @ Vector((1.0, 0.0, 0.0))).normalized()
    up = (rot @ Vector((0.0, 1.0, 0.0))).normalized()
    return right, up


def _world_points(obj, depsgraph):
    """Evaluated world-space vertices (falls back to the object bound box)."""
    mw = obj.matrix_world
    ev = obj.evaluated_get(depsgraph)
    try:
        me = ev.to_mesh()
    except Exception:
        me = None
    if me is not None and len(me.vertices):
        pts = [mw @ v.co for v in me.vertices]
        ev.to_mesh_clear()
        return pts
    return [mw @ Vector(c) for c in obj.bound_box]


def _span(points, axis):
    ds = [p.dot(axis) for p in points]
    return min(ds), max(ds)


def _gather(context):
    """For each selected object: its (min,max) along right and up. Returns (list, axes)."""
    axes = _view_axes(context)
    if axes is None:
        return None, None
    right, up = axes
    deps = context.evaluated_depsgraph_get()
    rows = []
    for obj in context.selected_objects:
        pts = _world_points(obj, deps)
        rmin, rmax = _span(pts, right)
        umin, umax = _span(pts, up)
        rows.append({"obj": obj, "rmin": rmin, "rmax": rmax, "umin": umin, "umax": umax})
    return rows, axes


def _reference(rows, context):
    """The bounds to align against: the active 'key' object, or the whole selection."""
    settings = context.scene.bareblocks
    if settings.align_to == "ACTIVE" and context.active_object is not None:
        for r in rows:
            if r["obj"] is context.active_object:
                return r
    return {
        "rmin": min(r["rmin"] for r in rows), "rmax": max(r["rmax"] for r in rows),
        "umin": min(r["umin"] for r in rows), "umax": max(r["umax"] for r in rows),
    }


class BAREBLOCKS_OT_align(bpy.types.Operator):
    bl_idname = "bareblocks.align"
    bl_label = "Align"
    bl_description = "Align selected objects in the current view plane (screen axes)"
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(
        items=[(m, m.title(), "") for m in
               ("LEFT", "HCENTER", "RIGHT", "TOP", "VCENTER", "BOTTOM")],
        name="Mode", default="LEFT",
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and len(context.selected_objects) >= 2

    def execute(self, context):
        rows, axes = _gather(context)
        if rows is None:
            self.report({"WARNING"}, "Hover the 3D viewport to align (needs a 3D view)")
            return {"CANCELLED"}
        right, up = axes
        ref = _reference(rows, context)
        rc = (ref["rmin"] + ref["rmax"]) * 0.5
        uc = (ref["umin"] + ref["umax"]) * 0.5

        for r in rows:
            if self.mode == "LEFT":
                delta, ax = ref["rmin"] - r["rmin"], right
            elif self.mode == "RIGHT":
                delta, ax = ref["rmax"] - r["rmax"], right
            elif self.mode == "HCENTER":
                delta, ax = rc - (r["rmin"] + r["rmax"]) * 0.5, right
            elif self.mode == "TOP":
                delta, ax = ref["umax"] - r["umax"], up
            elif self.mode == "BOTTOM":
                delta, ax = ref["umin"] - r["umin"], up
            else:  # VCENTER
                delta, ax = uc - (r["umin"] + r["umax"]) * 0.5, up
            r["obj"].location = r["obj"].location + ax * delta
        return {"FINISHED"}


class BAREBLOCKS_OT_distribute(bpy.types.Operator):
    bl_idname = "bareblocks.distribute"
    bl_label = "Distribute"
    bl_description = "Evenly space the centers of selected objects in the view plane"
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(
        items=[("HORIZONTAL", "Horizontal", ""), ("VERTICAL", "Vertical", "")],
        name="Mode", default="HORIZONTAL",
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and len(context.selected_objects) >= 3

    def execute(self, context):
        rows, axes = _gather(context)
        if rows is None:
            self.report({"WARNING"}, "Hover the 3D viewport to distribute (needs a 3D view)")
            return {"CANCELLED"}
        right, up = axes
        if self.mode == "HORIZONTAL":
            ax = right
            for r in rows:
                r["c"] = (r["rmin"] + r["rmax"]) * 0.5
        else:
            ax = up
            for r in rows:
                r["c"] = (r["umin"] + r["umax"]) * 0.5

        rows.sort(key=lambda r: r["c"])
        lo, hi = rows[0]["c"], rows[-1]["c"]
        n = len(rows)
        step = (hi - lo) / (n - 1)
        for i, r in enumerate(rows):
            target = lo + step * i
            r["obj"].location = r["obj"].location + ax * (target - r["c"])
        return {"FINISHED"}


classes = [BAREBLOCKS_OT_align, BAREBLOCKS_OT_distribute]
