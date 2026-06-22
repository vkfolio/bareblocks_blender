# BareBlocks - Corner Curved primitive (solid rounded corner block).
#
# Default (outer): a solid quarter-cylinder wedge that rounds a CONVEX corner - the
# curved face bulges outward, the two flat radial faces sit flush against the walls.
# Is Inner: the CONCAVE complement - a square block with a quarter-cylinder scooped out,
# rounding an inside corner. Both occupy the [0,R] x [0,R] x [0,Height] quadrant with the
# right-angle vertex at the object origin. Quality = arc resolution.

import math

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     store_grid_attributes, shade_smooth_by_angle)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_CORNER_CURVED, GN_VERSION


def build_corner_curved(ng):
    r = new_input(ng, "Radius", "NodeSocketFloat", default_value=2.0, min_value=0.001)
    r.subtype = "DISTANCE"
    h = new_input(ng, "Height", "NodeSocketFloat", default_value=2.0, min_value=0.001)
    h.subtype = "DISTANCE"
    new_input(ng, "Quality", "NodeSocketInt", default_value=16, min_value=2, max_value=256)
    new_input(ng, "Is Inner", "NodeSocketBool", default_value=False)
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1300, 0))
    gout = node(ng, "NodeGroupOutput", location=(1500, 0))
    R, H, Q = gin.outputs["Radius"], gin.outputs["Height"], gin.outputs["Quality"]

    half_r = fmath(ng, "MULTIPLY", R, 0.5, location=(-1100, -260))
    half_h = fmath(ng, "MULTIPLY", H, 0.5, location=(-1100, -360))

    # --- OUTER: solid quarter-cylinder wedge (convex), vertex at origin ---
    arc = node(ng, "GeometryNodeCurveArc", location=(-1080, 320))
    arc.mode = "RADIUS"
    link(ng, Q, arc.inputs["Resolution"])
    link(ng, R, arc.inputs["Radius"])
    arc.inputs["Sweep Angle"].default_value = math.pi / 2.0
    arc.inputs["Connect Center"].default_value = True  # close into a pie sector

    fill = node(ng, "GeometryNodeFillCurve", location=(-880, 320))
    link(ng, arc.outputs["Curve"], fill.inputs["Curve"])

    up = combine_xyz(ng, 0.0, 0.0, H, location=(-880, 180))
    extrude = node(ng, "GeometryNodeExtrudeMesh", location=(-680, 320))
    extrude.mode = "FACES"
    link(ng, fill.outputs["Mesh"], extrude.inputs["Mesh"])
    link(ng, up.outputs[0], extrude.inputs["Offset"])
    extrude.inputs["Offset Scale"].default_value = 1.0
    outer = extrude.outputs["Mesh"]

    # --- INNER: square block minus a cylinder = concave fillet ---
    sq_size = combine_xyz(ng, R, R, H, location=(-880, -120))
    square = node(ng, "GeometryNodeMeshCube", location=(-700, -120))
    link(ng, sq_size.outputs[0], square.inputs["Size"])
    sq_off = combine_xyz(ng, half_r.outputs[0], half_r.outputs[0], half_h.outputs[0],
                         location=(-700, -280))
    sq_xform = node(ng, "GeometryNodeTransform", location=(-520, -120))
    link(ng, square.outputs["Mesh"], sq_xform.inputs["Geometry"])
    link(ng, sq_off.outputs[0], sq_xform.inputs["Translation"])

    # Full cylinder centred at the far corner (R, R); its curved wall is the only thing
    # that cuts the square interior (no coplanar radial faces) -> clean concave scoop.
    # Radius is nudged 2% past R so the cut crosses the square edges transversally instead
    # of passing exactly through its corners - an exact tangency the boolean solver drops
    # at larger radii (the bug where big inner corners collapsed back to a square).
    cyl_verts = fmath(ng, "MULTIPLY", Q, 4.0, location=(-880, -460))
    tall = fmath(ng, "MULTIPLY", H, 3.0, location=(-880, -560))
    cut_r = fmath(ng, "MULTIPLY", R, 1.02, location=(-880, -400))
    cyl = node(ng, "GeometryNodeMeshCylinder", location=(-700, -460))
    link(ng, cyl_verts.outputs[0], cyl.inputs["Vertices"])
    link(ng, cut_r.outputs[0], cyl.inputs["Radius"])
    link(ng, tall.outputs[0], cyl.inputs["Depth"])
    cyl_off = combine_xyz(ng, R, R, half_h.outputs[0], location=(-700, -620))
    cyl_xform = node(ng, "GeometryNodeTransform", location=(-520, -460))
    link(ng, cyl.outputs["Mesh"], cyl_xform.inputs["Geometry"])
    link(ng, cyl_off.outputs[0], cyl_xform.inputs["Translation"])

    inner = node(ng, "GeometryNodeMeshBoolean", location=(-300, -200))
    inner.operation = "DIFFERENCE"
    link(ng, sq_xform.outputs["Geometry"], inner.inputs["Mesh 1"])
    link(ng, cyl_xform.outputs["Geometry"], inner.inputs["Mesh 2"])

    switch = node(ng, "GeometryNodeSwitch", location=(120, 60))
    switch.input_type = "GEOMETRY"
    link(ng, gin.outputs["Is Inner"], switch.inputs["Switch"])
    link(ng, outer, switch.inputs["False"])
    link(ng, inner.outputs["Mesh"], switch.inputs["True"])

    # Smooth the curved face only; the flat top/bottom and 90 deg edges stay sharp.
    smoothed = shade_smooth_by_angle(ng, switch.outputs["Output"])
    geo = store_grid_attributes(ng, smoothed)
    setmat = node(ng, "GeometryNodeSetMaterial", location=(940, 60))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def ensure_corner_curved():
    return ensure_group(GROUP_NAMES[TYPE_CORNER_CURVED], build_corner_curved, GN_VERSION)
