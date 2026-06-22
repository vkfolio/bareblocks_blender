# BareBlocks - Wall primitive: a vertical slab swept along an editable spline.
#
# The object is a CURVE (like the Track): straight by default, bend it in Edit Mode and the
# wall follows. Height + Thickness are live; Segment Length controls bend smoothness. The
# grid flows along the wall (arc-length frame), like the Track.

from .common import (ensure_group, node, link, new_input, new_output, fmath, sweep_rect_along,
                     bake_spine_frame, store_flow_grid, shade_smooth_by_angle)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_WALL, GN_VERSION


def build_wall(ng):
    new_input(ng, "Geometry", "NodeSocketGeometry")
    h = new_input(ng, "Height", "NodeSocketFloat", default_value=3.0, min_value=0.01)
    h.subtype = "DISTANCE"
    t = new_input(ng, "Thickness", "NodeSocketFloat", default_value=0.3, min_value=0.01)
    t.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1100, 0))
    gout = node(ng, "NodeGroupOutput", location=(1300, 0))

    # "Evaluated" follows the spline faithfully: smooth where it's smooth (curved wall) and
    # sharp where you use corner/vector handles (angled wall). Resampling by length would
    # chamfer sharp corners, so it can't do crisp angles.
    resample = node(ng, "GeometryNodeResampleCurve", location=(-900, 160))
    resample.inputs["Mode"].default_value = "Evaluated"
    link(ng, gin.outputs["Geometry"], resample.inputs["Curve"])
    spine = node(ng, "GeometryNodeSetCurveNormal", location=(-720, 160))
    spine.inputs["Mode"].default_value = "Z Up"
    link(ng, resample.outputs["Curve"], spine.inputs["Curve"])
    spine_sock = bake_spine_frame(ng, spine.outputs["Curve"])

    half_h = fmath(ng, "MULTIPLY", gin.outputs["Height"], 0.5, location=(-720, -120))
    slab = sweep_rect_along(ng, spine_sock, gin.outputs["Thickness"], gin.outputs["Height"],
                            off_x=0.0, off_y=half_h.outputs[0], location=(-400, 120))
    geo = store_flow_grid(ng, slab)
    shaded = shade_smooth_by_angle(ng, geo, base_x=700.0, base_y=-1100.0)

    setmat = node(ng, "GeometryNodeSetMaterial", location=(1000, 60))
    link(ng, shaded, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def ensure_wall():
    return ensure_group(GROUP_NAMES[TYPE_WALL], build_wall, GN_VERSION)
