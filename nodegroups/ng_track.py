# BareBlocks - Track primitive (race-track channel that follows an editable spline).
#
# The object is a CURVE: its spline IS the path. A U-channel cross-section (a floor with
# two raised side walls) is swept along that spline, so bending the curve in Edit Mode
# bends the whole track. Width / wall height / wall thickness / floor thickness are all
# live GN inputs. Segment Length controls how finely the spline is resampled (smoother
# bends = smaller value).

from .common import (ensure_group, node, link, new_input, new_output, fmath, vmath, combine_xyz,
                     sweep_rect_along, store_grid_attributes, bake_spine_frame, store_flow_grid,
                     named_attr, store_named, shade_smooth_by_angle)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_TRACK, GN_VERSION


def build_track(ng):
    # First input is the object's curve (the path the modifier pipes in).
    new_input(ng, "Geometry", "NodeSocketGeometry")
    w = new_input(ng, "Width", "NodeSocketFloat", default_value=3.0, min_value=0.01)
    w.subtype = "DISTANCE"
    wh = new_input(ng, "Wall Height", "NodeSocketFloat", default_value=1.0, min_value=0.0)
    wh.subtype = "DISTANCE"
    wt = new_input(ng, "Wall Thickness", "NodeSocketFloat", default_value=0.3, min_value=0.01)
    wt.subtype = "DISTANCE"
    ft = new_input(ng, "Floor Thickness", "NodeSocketFloat", default_value=0.2, min_value=0.01)
    ft.subtype = "DISTANCE"
    sl = new_input(ng, "Segment Length", "NodeSocketFloat", default_value=0.5, min_value=0.05)
    sl.subtype = "DISTANCE"
    new_input(ng, "Side Rails", "NodeSocketBool", default_value=False)
    rh = new_input(ng, "Rail Height", "NodeSocketFloat", default_value=1.0, min_value=0.01)
    rh.subtype = "DISTANCE"
    rt = new_input(ng, "Rail Thickness", "NodeSocketFloat", default_value=0.08, min_value=0.005)
    rt.subtype = "DISTANCE"
    ps = new_input(ng, "Post Spacing", "NodeSocketFloat", default_value=1.5, min_value=0.05)
    ps.subtype = "DISTANCE"
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1300, 0))
    gout = node(ng, "NodeGroupOutput", location=(1500, 0))

    # Resample the spline evenly so bends stay smooth and cells stay regular as it grows.
    resample = node(ng, "GeometryNodeResampleCurve", location=(-1080, 160))
    resample.inputs["Mode"].default_value = "Length"
    link(ng, gin.outputs["Geometry"], resample.inputs["Curve"])
    link(ng, gin.outputs["Segment Length"], resample.inputs["Length"])

    # Z-up normal keeps the floor horizontal and the walls vertical through every bend.
    spine = node(ng, "GeometryNodeSetCurveNormal", location=(-880, 160))
    spine.inputs["Mode"].default_value = "Z Up"
    link(ng, resample.outputs["Curve"], spine.inputs["Curve"])
    # Bake a moving frame so the swept grid flows along the curve (not a world grid).
    spine_sock = bake_spine_frame(ng, spine.outputs["Curve"])

    # Cross-section geometry (profile plane: local +X = across, +Y = up).
    half_w = fmath(ng, "MULTIPLY", gin.outputs["Width"], 0.5, location=(-880, -120))
    half_ft = fmath(ng, "MULTIPLY", gin.outputs["Floor Thickness"], 0.5, location=(-880, -260))
    half_wh = fmath(ng, "MULTIPLY", gin.outputs["Wall Height"], 0.5, location=(-880, -400))
    half_wt = fmath(ng, "MULTIPLY", gin.outputs["Wall Thickness"], 0.5, location=(-880, -540))
    # Wall centre x = +/-(Width/2 - WallThickness/2): sits flush to each edge.
    wall_x = fmath(ng, "SUBTRACT", half_w.outputs[0], half_wt.outputs[0], location=(-700, -480))
    neg_wall_x = fmath(ng, "MULTIPLY", wall_x.outputs[0], -1.0, location=(-520, -480))

    # Floor: full width, bottom sitting on z = 0.
    floor = sweep_rect_along(ng, spine_sock, gin.outputs["Width"], gin.outputs["Floor Thickness"],
                             off_x=0.0, off_y=half_ft.outputs[0], location=(-400, 320))
    # Left + right walls, each on the ground, rising to Wall Height.
    left = sweep_rect_along(ng, spine_sock, gin.outputs["Wall Thickness"], gin.outputs["Wall Height"],
                            off_x=neg_wall_x.outputs[0], off_y=half_wh.outputs[0], location=(-400, 40))
    right = sweep_rect_along(ng, spine_sock, gin.outputs["Wall Thickness"], gin.outputs["Wall Height"],
                             off_x=wall_x.outputs[0], off_y=half_wh.outputs[0], location=(-400, -240))

    joined = node(ng, "GeometryNodeJoinGeometry", location=(360, 60))
    link(ng, floor, joined.inputs[0])
    link(ng, left, joined.inputs[0])
    link(ng, right, joined.inputs[0])
    geo = store_flow_grid(ng, joined.outputs[0])

    # ---- optional side rails on top of the walls ----
    rt, rh = gin.outputs["Rail Thickness"], gin.outputs["Rail Height"]
    half_rh = fmath(ng, "MULTIPLY", rh, 0.5, location=(-200, -700))
    rail_z = fmath(ng, "ADD", gin.outputs["Wall Height"], rh, location=(-200, -780))
    post_c = fmath(ng, "ADD", gin.outputs["Wall Height"], half_rh.outputs[0], location=(-20, -780))

    rail_left = sweep_rect_along(ng, spine_sock, rt, rt, off_x=neg_wall_x.outputs[0],
                                 off_y=rail_z.outputs[0], location=(120, -440))
    rail_right = sweep_rect_along(ng, spine_sock, rt, rt, off_x=wall_x.outputs[0],
                                  off_y=rail_z.outputs[0], location=(120, -640))

    # Posts at Post Spacing, offset to each wall along the curve's lateral (binormal) dir,
    # and rotated to the curve heading so they stay square to the track through bends.
    rs0 = node(ng, "GeometryNodeResampleCurve", location=(-880, -900))
    rs0.inputs["Mode"].default_value = "Length"
    link(ng, spine_sock, rs0.inputs["Curve"])
    link(ng, gin.outputs["Post Spacing"], rs0.inputs["Length"])
    tan = node(ng, "GeometryNodeInputTangent", location=(-880, -1040))
    tsep = node(ng, "ShaderNodeSeparateXYZ", location=(-700, -1040))
    link(ng, tan.outputs[0], tsep.inputs[0])
    yaw = fmath(ng, "ARCTAN2", tsep.outputs["Y"], tsep.outputs["X"], location=(-520, -1040))
    rs = store_named(ng, rs0.outputs["Curve"], "bb_yaw", yaw.outputs[0], "FLOAT", "POINT",
                     location=(-340, -900))
    zup_v = combine_xyz(ng, 0.0, 0.0, 1.0, location=(-700, -1180))
    binorm = vmath(ng, "CROSS_PRODUCT", tan.outputs[0], zup_v.outputs[0], location=(-520, -1180))
    binorm_n = vmath(ng, "NORMALIZE", binorm.outputs[0], location=(-360, -1180))

    def posts(sign_socket, by):
        lat = vmath(ng, "SCALE", binorm_n.outputs[0], location=(-180, by))
        link(ng, sign_socket, lat.inputs[3])
        zc = combine_xyz(ng, 0.0, 0.0, post_c.outputs[0], location=(-180, by - 120))
        off = vmath(ng, "ADD", lat.outputs[0], zc.outputs[0], location=(20, by))
        pset = node(ng, "GeometryNodeSetPosition", location=(200, by))
        link(ng, rs, pset.inputs["Geometry"])
        link(ng, off.outputs[0], pset.inputs["Offset"])
        eul = combine_xyz(ng, 0.0, 0.0, named_attr(ng, "bb_yaw", "FLOAT", location=(20, by - 240)),
                          location=(200, by - 240))
        prot = node(ng, "FunctionNodeEulerToRotation", location=(380, by - 240))
        link(ng, eul.outputs[0], prot.inputs[0])
        pscale = combine_xyz(ng, rt, rt, rh, location=(200, by - 140))
        cube = node(ng, "GeometryNodeMeshCube", location=(200, by - 360))
        cube.inputs["Size"].default_value = (1.0, 1.0, 1.0)
        iop = node(ng, "GeometryNodeInstanceOnPoints", location=(560, by))
        link(ng, pset.outputs["Geometry"], iop.inputs["Points"])
        link(ng, cube.outputs["Mesh"], iop.inputs["Instance"])
        link(ng, prot.outputs[0], iop.inputs["Rotation"])
        link(ng, pscale.outputs[0], iop.inputs["Scale"])
        rz = node(ng, "GeometryNodeRealizeInstances", location=(760, by))
        link(ng, iop.outputs["Instances"], rz.inputs[0])
        return rz.outputs[0]

    posts_l = posts(neg_wall_x.outputs[0], -900)
    posts_r = posts(wall_x.outputs[0], -1180)

    # Rail bars are swept (flowing grid); posts are instanced (plain position grid).
    railbars = node(ng, "GeometryNodeJoinGeometry", location=(820, -480))
    link(ng, rail_left, railbars.inputs[0])
    link(ng, rail_right, railbars.inputs[0])
    railbars_geo = store_flow_grid(ng, railbars.outputs[0], base_x=2700.0, base_y=-1100.0)
    postjoin = node(ng, "GeometryNodeJoinGeometry", location=(820, -720))
    link(ng, posts_l, postjoin.inputs[0])
    link(ng, posts_r, postjoin.inputs[0])
    posts_geo = store_grid_attributes(ng, postjoin.outputs[0], base_x=2700.0, base_y=-2100.0)
    rails_join = node(ng, "GeometryNodeJoinGeometry", location=(1040, -560))
    link(ng, railbars_geo, rails_join.inputs[0])
    link(ng, posts_geo, rails_join.inputs[0])
    rails_geo = rails_join.outputs[0]

    with_rails = node(ng, "GeometryNodeJoinGeometry", location=(700, 60))
    link(ng, geo, with_rails.inputs[0])
    link(ng, rails_geo, with_rails.inputs[0])
    sw = node(ng, "GeometryNodeSwitch", location=(900, 60))
    sw.input_type = "GEOMETRY"
    link(ng, gin.outputs["Side Rails"], sw.inputs["Switch"])
    link(ng, geo, sw.inputs["False"])
    link(ng, with_rails.outputs[0], sw.inputs["True"])

    # Curve to Mesh shades smooth by default; keep the gentle bend smooth but the channel
    # corners crisp (sharp edges > 40 deg stay flat).
    shaded = shade_smooth_by_angle(ng, sw.outputs["Output"], base_x=950.0, base_y=-1100.0)
    setmat = node(ng, "GeometryNodeSetMaterial", location=(1150, 60))
    link(ng, shaded, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def ensure_track():
    return ensure_group(GROUP_NAMES[TYPE_TRACK], build_track, GN_VERSION)
