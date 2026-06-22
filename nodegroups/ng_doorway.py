# BareBlocks - Doorway primitive (wall panel with a floor-to-top opening).
#
# Like the Window but the opening reaches the floor: only Side jambs + a Top lintel remain.

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     store_grid_attributes)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_DOORWAY, GN_VERSION


def build_doorway(ng):
    for axis, default in (("X", 3.0), ("Y", 0.4), ("Z", 3.0)):
        s = new_input(ng, f"Size {axis}", "NodeSocketFloat", default_value=default, min_value=0.001)
        s.subtype = "DISTANCE"
    for name, default in (("Top Thickness", 0.6), ("Side Thickness", 0.6)):
        s = new_input(ng, name, "NodeSocketFloat", default_value=default, min_value=0.0)
        s.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1300, 0))
    gout = node(ng, "NodeGroupOutput", location=(900, 0))
    sx, sy, sz = gin.outputs["Size X"], gin.outputs["Size Y"], gin.outputs["Size Z"]
    top, side = gin.outputs["Top Thickness"], gin.outputs["Side Thickness"]

    outer_vec = combine_xyz(ng, sx, sy, sz, location=(-1100, 200))
    outer = node(ng, "GeometryNodeMeshCube", location=(-920, 200))
    link(ng, outer_vec.outputs[0], outer.inputs["Size"])

    two_side = fmath(ng, "MULTIPLY", side, 2.0, location=(-1100, -40))
    open_w = fmath(ng, "SUBTRACT", sx, two_side.outputs[0], location=(-920, -40))
    open_w_c = fmath(ng, "MAXIMUM", open_w.outputs[0], 0.01, location=(-740, -40))
    open_h = fmath(ng, "SUBTRACT", sz, top, location=(-920, -200))
    open_h_c = fmath(ng, "MAXIMUM", open_h.outputs[0], 0.01, location=(-740, -200))
    deep = fmath(ng, "MULTIPLY", sy, 2.0, location=(-1100, -340))
    # Extend the cutter below the floor by MARGIN so its bottom face isn't coplanar with
    # the wall's bottom (that exact tangency makes the boolean drop the cut).
    margin = 0.2
    hole_h = fmath(ng, "ADD", open_h_c.outputs[0], margin, location=(-560, -120))
    hole_vec = combine_xyz(ng, open_w_c.outputs[0], deep.outputs[0], hole_h.outputs[0],
                           location=(-400, -120))
    hole = node(ng, "GeometryNodeMeshCube", location=(-220, -120))
    link(ng, hole_vec.outputs[0], hole.inputs["Size"])

    # Opening top stays at Size Z/2 - Top; bottom overshoots to -Size Z/2 - margin.
    halfz = fmath(ng, "MULTIPLY", sz, -0.5, location=(-560, -360))
    halfopen = fmath(ng, "MULTIPLY", open_h_c.outputs[0], 0.5, location=(-560, -460))
    offz0 = fmath(ng, "ADD", halfz.outputs[0], halfopen.outputs[0], location=(-380, -400))
    offz = fmath(ng, "SUBTRACT", offz0.outputs[0], margin * 0.5, location=(-200, -460))
    off_vec = combine_xyz(ng, 0.0, 0.0, offz.outputs[0], location=(-40, -400))
    xform = node(ng, "GeometryNodeTransform", location=(-20, -160))
    link(ng, hole.outputs["Mesh"], xform.inputs["Geometry"])
    link(ng, off_vec.outputs[0], xform.inputs["Translation"])

    boolean = node(ng, "GeometryNodeMeshBoolean", location=(220, 120))
    boolean.operation = "DIFFERENCE"
    link(ng, outer.outputs["Mesh"], boolean.inputs["Mesh 1"])
    link(ng, xform.outputs["Geometry"], boolean.inputs["Mesh 2"])

    geo = store_grid_attributes(ng, boolean.outputs["Mesh"])
    setmat = node(ng, "GeometryNodeSetMaterial", location=(640, 120))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def ensure_doorway():
    return ensure_group(GROUP_NAMES[TYPE_DOORWAY], build_doorway, GN_VERSION)
