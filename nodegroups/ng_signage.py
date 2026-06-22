# BareBlocks - Signage props: road Sign (post + board) and Billboard (two legs + big board).

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     store_grid_attributes, shade_smooth_by_angle)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_SIGN, TYPE_BILLBOARD, GN_VERSION


def _box(ng, size_socket, translation_socket, location):
    cube = node(ng, "GeometryNodeMeshCube", location=location)
    link(ng, size_socket, cube.inputs["Size"])
    xf = node(ng, "GeometryNodeTransform", location=(location[0] + 180, location[1]))
    link(ng, cube.outputs["Mesh"], xf.inputs["Geometry"])
    link(ng, translation_socket, xf.inputs["Translation"])
    return xf.outputs["Geometry"]


def _finish(ng, geo, gin, gout, loc_x=900):
    smoothed = shade_smooth_by_angle(ng, geo, base_x=loc_x - 200, base_y=-900.0)
    out = store_grid_attributes(ng, smoothed)
    setmat = node(ng, "GeometryNodeSetMaterial", location=(loc_x, 80))
    link(ng, out, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def build_sign(ng):
    ph = new_input(ng, "Post Height", "NodeSocketFloat", default_value=2.5, min_value=0.01)
    ph.subtype = "DISTANCE"
    pr = new_input(ng, "Post Radius", "NodeSocketFloat", default_value=0.06, min_value=0.005)
    pr.subtype = "DISTANCE"
    bw = new_input(ng, "Board Width", "NodeSocketFloat", default_value=1.0, min_value=0.01)
    bw.subtype = "DISTANCE"
    bh = new_input(ng, "Board Height", "NodeSocketFloat", default_value=0.7, min_value=0.01)
    bh.subtype = "DISTANCE"
    bt = new_input(ng, "Board Thickness", "NodeSocketFloat", default_value=0.06, min_value=0.005)
    bt.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-900, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))

    post = node(ng, "GeometryNodeMeshCylinder", location=(-700, 200))
    post.inputs["Vertices"].default_value = 16
    link(ng, gin.outputs["Post Radius"], post.inputs["Radius"])
    link(ng, gin.outputs["Post Height"], post.inputs["Depth"])
    half_ph = fmath(ng, "MULTIPLY", gin.outputs["Post Height"], 0.5, location=(-700, 60))
    post_off = combine_xyz(ng, 0.0, 0.0, half_ph.outputs[0], location=(-520, 60))
    post_x = node(ng, "GeometryNodeTransform", location=(-340, 200))
    link(ng, post.outputs["Mesh"], post_x.inputs["Geometry"])
    link(ng, post_off.outputs[0], post_x.inputs["Translation"])

    board_vec = combine_xyz(ng, gin.outputs["Board Width"], gin.outputs["Board Thickness"],
                            gin.outputs["Board Height"], location=(-520, -160))
    board_z = fmath(ng, "SUBTRACT", gin.outputs["Post Height"],
                    fmath(ng, "MULTIPLY", gin.outputs["Board Height"], 0.5,
                          location=(-520, -300)).outputs[0], location=(-340, -300))
    board_off = combine_xyz(ng, 0.0, 0.0, board_z.outputs[0], location=(-160, -300))
    board = _box(ng, board_vec.outputs[0], board_off.outputs[0], location=(-160, -160))

    joined = node(ng, "GeometryNodeJoinGeometry", location=(360, 60))
    link(ng, post_x.outputs["Geometry"], joined.inputs[0])
    link(ng, board, joined.inputs[0])
    _finish(ng, joined.outputs[0], gin, gout)


def build_billboard(ng):
    w = new_input(ng, "Width", "NodeSocketFloat", default_value=5.0, min_value=0.1)
    w.subtype = "DISTANCE"
    ht = new_input(ng, "Height", "NodeSocketFloat", default_value=2.2, min_value=0.1)
    ht.subtype = "DISTANCE"
    lh = new_input(ng, "Leg Height", "NodeSocketFloat", default_value=2.5, min_value=0.01)
    lh.subtype = "DISTANCE"
    pt = new_input(ng, "Post Thickness", "NodeSocketFloat", default_value=0.18, min_value=0.01)
    pt.subtype = "DISTANCE"
    bt = new_input(ng, "Board Thickness", "NodeSocketFloat", default_value=0.12, min_value=0.005)
    bt.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1100, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))

    leg_vec = combine_xyz(ng, gin.outputs["Post Thickness"], gin.outputs["Post Thickness"],
                          gin.outputs["Leg Height"], location=(-900, 200))
    half_lh = fmath(ng, "MULTIPLY", gin.outputs["Leg Height"], 0.5, location=(-900, 60))
    legx = fmath(ng, "MULTIPLY", gin.outputs["Width"], 0.35, location=(-900, -80))
    neg_legx = fmath(ng, "MULTIPLY", legx.outputs[0], -1.0, location=(-720, -80))
    leg_l_off = combine_xyz(ng, neg_legx.outputs[0], 0.0, half_lh.outputs[0], location=(-540, 120))
    leg_r_off = combine_xyz(ng, legx.outputs[0], 0.0, half_lh.outputs[0], location=(-540, 20))
    leg_l = _box(ng, leg_vec.outputs[0], leg_l_off.outputs[0], location=(-360, 200))
    leg_r = _box(ng, leg_vec.outputs[0], leg_r_off.outputs[0], location=(-360, 40))

    board_vec = combine_xyz(ng, gin.outputs["Width"], gin.outputs["Board Thickness"],
                            gin.outputs["Height"], location=(-540, -200))
    board_z = fmath(ng, "ADD", gin.outputs["Leg Height"],
                    fmath(ng, "MULTIPLY", gin.outputs["Height"], 0.5,
                          location=(-540, -340)).outputs[0], location=(-360, -340))
    board_off = combine_xyz(ng, 0.0, 0.0, board_z.outputs[0], location=(-180, -340))
    board = _box(ng, board_vec.outputs[0], board_off.outputs[0], location=(-180, -200))

    joined = node(ng, "GeometryNodeJoinGeometry", location=(360, 60))
    for s in (leg_l, leg_r, board):
        link(ng, s, joined.inputs[0])
    _finish(ng, joined.outputs[0], gin, gout)


def ensure_sign():
    return ensure_group(GROUP_NAMES[TYPE_SIGN], build_sign, GN_VERSION)


def ensure_billboard():
    return ensure_group(GROUP_NAMES[TYPE_BILLBOARD], build_billboard, GN_VERSION)
