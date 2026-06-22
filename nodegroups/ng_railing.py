# BareBlocks - Railing / side rails that follow an editable spline.
#
# Posts at regular spacing along the path, plus a top and bottom rail swept along it.
# The object is a CURVE (like the Track): bend the path in Edit Mode and it follows.

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     sweep_rect_along, store_grid_attributes)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_RAILING, GN_VERSION


def build_railing(ng):
    new_input(ng, "Geometry", "NodeSocketGeometry")
    h = new_input(ng, "Height", "NodeSocketFloat", default_value=1.1, min_value=0.01)
    h.subtype = "DISTANCE"
    ps = new_input(ng, "Post Spacing", "NodeSocketFloat", default_value=1.5, min_value=0.05)
    ps.subtype = "DISTANCE"
    pt = new_input(ng, "Post Thickness", "NodeSocketFloat", default_value=0.12, min_value=0.005)
    pt.subtype = "DISTANCE"
    rt = new_input(ng, "Rail Thickness", "NodeSocketFloat", default_value=0.1, min_value=0.005)
    rt.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1300, 0))
    gout = node(ng, "NodeGroupOutput", location=(1500, 0))
    curve = gin.outputs["Geometry"]
    height, rail_t = gin.outputs["Height"], gin.outputs["Rail Thickness"]

    # --- rails: smooth resample + Z-up normal, sweep a square profile at two heights ---
    rail_rs = node(ng, "GeometryNodeResampleCurve", location=(-1080, 240))
    rail_rs.inputs["Mode"].default_value = "Length"
    link(ng, curve, rail_rs.inputs["Curve"])
    rail_rs.inputs["Length"].default_value = 0.3
    rail_spine = node(ng, "GeometryNodeSetCurveNormal", location=(-880, 240))
    rail_spine.inputs["Mode"].default_value = "Z Up"
    link(ng, rail_rs.outputs["Curve"], rail_spine.inputs["Curve"])
    spine = rail_spine.outputs["Curve"]

    bot_off = fmath(ng, "MULTIPLY", height, 0.12, location=(-880, 60))
    top = sweep_rect_along(ng, spine, rail_t, rail_t, off_x=0.0, off_y=height,
                           location=(-600, 320))
    bottom = sweep_rect_along(ng, spine, rail_t, rail_t, off_x=0.0, off_y=bot_off.outputs[0],
                              location=(-600, 40))

    # --- posts: resample by Post Spacing, instance a vertical column at each point ---
    post_rs = node(ng, "GeometryNodeResampleCurve", location=(-1080, -260))
    post_rs.inputs["Mode"].default_value = "Length"
    link(ng, curve, post_rs.inputs["Curve"])
    link(ng, gin.outputs["Post Spacing"], post_rs.inputs["Length"])

    half_h = fmath(ng, "MULTIPLY", height, 0.5, location=(-880, -360))
    lift = combine_xyz(ng, 0.0, 0.0, half_h.outputs[0], location=(-700, -360))
    postpos = node(ng, "GeometryNodeSetPosition", location=(-520, -260))
    link(ng, post_rs.outputs["Curve"], postpos.inputs["Geometry"])
    link(ng, lift.outputs[0], postpos.inputs["Offset"])

    pscale = combine_xyz(ng, gin.outputs["Post Thickness"], gin.outputs["Post Thickness"],
                         height, location=(-520, -440))
    cube = node(ng, "GeometryNodeMeshCube", location=(-520, -560))
    cube.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    iop = node(ng, "GeometryNodeInstanceOnPoints", location=(-280, -320))
    link(ng, postpos.outputs["Geometry"], iop.inputs["Points"])
    link(ng, cube.outputs["Mesh"], iop.inputs["Instance"])
    link(ng, pscale.outputs[0], iop.inputs["Scale"])
    posts = node(ng, "GeometryNodeRealizeInstances", location=(-60, -320))
    link(ng, iop.outputs["Instances"], posts.inputs[0])

    joined = node(ng, "GeometryNodeJoinGeometry", location=(300, 60))
    link(ng, top, joined.inputs[0])
    link(ng, bottom, joined.inputs[0])
    link(ng, posts.outputs[0], joined.inputs[0])

    geo = store_grid_attributes(ng, joined.outputs[0])
    setmat = node(ng, "GeometryNodeSetMaterial", location=(800, 60))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def ensure_railing():
    return ensure_group(GROUP_NAMES[TYPE_RAILING], build_railing, GN_VERSION)
