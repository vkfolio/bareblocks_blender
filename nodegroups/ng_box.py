# BareBlocks - Box primitive (sharp cuboid).

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz,
                     store_grid_attributes)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_BOX, GN_VERSION


def build_box(ng):
    for axis in ("X", "Y", "Z"):
        s = new_input(ng, f"Size {axis}", "NodeSocketFloat", default_value=2.0, min_value=0.0)
        s.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1100, 0))
    gout = node(ng, "NodeGroupOutput", location=(900, 0))

    size_vec = combine_xyz(ng, gin.outputs["Size X"], gin.outputs["Size Y"],
                           gin.outputs["Size Z"], location=(-900, 0))
    cube = node(ng, "GeometryNodeMeshCube", location=(-700, 0))
    link(ng, size_vec.outputs[0], cube.inputs["Size"])
    geo = store_grid_attributes(ng, cube.outputs["Mesh"])

    setmat = node(ng, "GeometryNodeSetMaterial", location=(640, 80))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def ensure_box():
    return ensure_group(GROUP_NAMES[TYPE_BOX], build_box, GN_VERSION)
