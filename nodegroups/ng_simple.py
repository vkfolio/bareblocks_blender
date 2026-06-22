# BareBlocks - Plane (flat grid) and Sleeve (tapered square beam).

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     store_grid_attributes)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_PLANE, TYPE_SLEEVE, GN_VERSION


def _finish(ng, geo_socket, gin, gout, loc_x=900):
    geo = store_grid_attributes(ng, geo_socket)
    setmat = node(ng, "GeometryNodeSetMaterial", location=(loc_x, 80))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def build_plane(ng):
    sx = new_input(ng, "Size X", "NodeSocketFloat", default_value=4.0, min_value=0.001)
    sx.subtype = "DISTANCE"
    sy = new_input(ng, "Size Y", "NodeSocketFloat", default_value=4.0, min_value=0.001)
    sy.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-700, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))

    grid = node(ng, "GeometryNodeMeshGrid", location=(-400, 0))
    link(ng, gin.outputs["Size X"], grid.inputs["Size X"])
    link(ng, gin.outputs["Size Y"], grid.inputs["Size Y"])
    grid.inputs["Vertices X"].default_value = 2
    grid.inputs["Vertices Y"].default_value = 2
    _finish(ng, grid.outputs["Mesh"], gin, gout)


def build_sleeve(ng):
    ln = new_input(ng, "Length", "NodeSocketFloat", default_value=4.0, min_value=0.001)
    ln.subtype = "DISTANCE"
    ss = new_input(ng, "Start Size", "NodeSocketFloat", default_value=1.0, min_value=0.001)
    ss.subtype = "DISTANCE"
    es = new_input(ng, "End Size", "NodeSocketFloat", default_value=0.4, min_value=0.001)
    es.subtype = "DISTANCE"
    sky = new_input(ng, "Skew Y", "NodeSocketFloat", default_value=0.0)
    sky.subtype = "DISTANCE"
    skz = new_input(ng, "Skew Z", "NodeSocketFloat", default_value=0.0)
    skz.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1000, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))

    # Box of Length x StartSize x StartSize, centred on the origin.
    size_vec = combine_xyz(ng, gin.outputs["Length"], gin.outputs["Start Size"],
                           gin.outputs["Start Size"], location=(-800, 120))
    cube = node(ng, "GeometryNodeMeshCube", location=(-620, 120))
    link(ng, size_vec.outputs[0], cube.inputs["Size"])

    # Taper + skew the +X end: verts with x>0 scale their Y/Z by EndSize/StartSize and
    # shift by Skew Y / Skew Z, so the beam can both taper and slant (sheared parallelepiped).
    pos = node(ng, "GeometryNodeInputPosition", location=(-800, -160))
    sep = node(ng, "ShaderNodeSeparateXYZ", location=(-620, -160))
    link(ng, pos.outputs[0], sep.inputs[0])
    sel = fmath(ng, "GREATER_THAN", sep.outputs["X"], 0.0, location=(-440, -120))
    ratio = fmath(ng, "DIVIDE", gin.outputs["End Size"], gin.outputs["Start Size"],
                  location=(-440, -300))
    sy = fmath(ng, "MULTIPLY", sep.outputs["Y"], ratio.outputs[0], location=(-260, -220))
    new_y = fmath(ng, "ADD", sy.outputs[0], gin.outputs["Skew Y"], location=(-80, -220))
    sz = fmath(ng, "MULTIPLY", sep.outputs["Z"], ratio.outputs[0], location=(-260, -380))
    new_z = fmath(ng, "ADD", sz.outputs[0], gin.outputs["Skew Z"], location=(-80, -380))
    newpos = combine_xyz(ng, sep.outputs["X"], new_y.outputs[0], new_z.outputs[0],
                         location=(100, -280))
    setpos = node(ng, "GeometryNodeSetPosition", location=(120, 60))
    link(ng, cube.outputs["Mesh"], setpos.inputs["Geometry"])
    link(ng, sel.outputs[0], setpos.inputs["Selection"])
    link(ng, newpos.outputs[0], setpos.inputs["Position"])
    _finish(ng, setpos.outputs["Geometry"], gin, gout)


def ensure_plane():
    return ensure_group(GROUP_NAMES[TYPE_PLANE], build_plane, GN_VERSION)


def ensure_sleeve():
    return ensure_group(GROUP_NAMES[TYPE_SLEEVE], build_sleeve, GN_VERSION)
