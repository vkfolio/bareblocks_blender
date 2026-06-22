# BareBlocks - Corner Ramp primitive (triangular-prism wedge).
#
# A box of Size X x Y x Z whose +X / +Z top edge is collapsed to the base, producing a
# slope that rises from +X (low) to -X (full height). Size X is the run (length), Size Y
# the width, Size Z the rise (height) - so the slope angle = atan(Size Z / Size X) is
# fully controllable via the three dimensions, like Unreal's vector "Corner Ramp Size".

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     store_grid_attributes)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_CORNER_RAMP, GN_VERSION


def build_corner_ramp(ng):
    for axis in ("X", "Y", "Z"):
        s = new_input(ng, f"Size {axis}", "NodeSocketFloat", default_value=2.0, min_value=0.0)
        s.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1100, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))
    sx, sy, sz = gin.outputs["Size X"], gin.outputs["Size Y"], gin.outputs["Size Z"]

    size_vec = combine_xyz(ng, sx, sy, sz, location=(-900, 120))
    cube = node(ng, "GeometryNodeMeshCube", location=(-720, 120))
    link(ng, size_vec.outputs[0], cube.inputs["Size"])

    # Collapse the +X & +Z corner: verts with x>0 and z>0 -> drop z to the base (-Z/2).
    pos = node(ng, "GeometryNodeInputPosition", location=(-900, -160))
    sep = node(ng, "ShaderNodeSeparateXYZ", location=(-720, -160))
    link(ng, pos.outputs[0], sep.inputs[0])
    selx = fmath(ng, "GREATER_THAN", sep.outputs["X"], 0.0, location=(-540, -100))
    selz = fmath(ng, "GREATER_THAN", sep.outputs["Z"], 0.0, location=(-540, -220))
    sel = fmath(ng, "MULTIPLY", selx.outputs[0], selz.outputs[0], location=(-360, -160))

    base_z = fmath(ng, "MULTIPLY", sz, -0.5, location=(-540, -360))
    newpos = combine_xyz(ng, sep.outputs["X"], sep.outputs["Y"], base_z.outputs[0],
                         location=(-360, -360))

    setpos = node(ng, "GeometryNodeSetPosition", location=(-120, 60))
    link(ng, cube.outputs["Mesh"], setpos.inputs["Geometry"])
    link(ng, sel.outputs[0], setpos.inputs["Selection"])
    link(ng, newpos.outputs[0], setpos.inputs["Position"])

    geo = store_grid_attributes(ng, setpos.outputs["Geometry"])
    setmat = node(ng, "GeometryNodeSetMaterial", location=(720, 60))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def ensure_corner_ramp():
    return ensure_group(GROUP_NAMES[TYPE_CORNER_RAMP], build_corner_ramp, GN_VERSION)
