# BareBlocks - Stairs: straight and curved, with solid/open steps and optional side rails.
#
# Steps are unit cubes instanced on points and scaled per-index. Fill Bottom = solid blocks
# rising from the ground; off = floating treads of Tread Thickness. Side Rails adds posts +
# a swept top rail down each side (sloped for straight, helical for curved).

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     vmath, sweep_rect_along, store_grid_attributes, named_attr, store_named,
                     object_scale)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_STAIRS, TYPE_STAIRS_CURVED, GN_VERSION


def _unit_cube(ng, location):
    c = node(ng, "GeometryNodeMeshCube", location=location)
    c.inputs["Size"].default_value = (1.0, 1.0, 1.0)
    return c


def _gswitch(ng, sw, false_geo, true_geo, location):
    n = node(ng, "GeometryNodeSwitch", location=location)
    n.input_type = "GEOMETRY"
    link(ng, sw, n.inputs["Switch"])
    link(ng, false_geo, n.inputs["False"])
    link(ng, true_geo, n.inputs["True"])
    return n.outputs["Output"]


def _fswitch(ng, sw, fval, tval, location):
    n = node(ng, "GeometryNodeSwitch", location=location)
    n.input_type = "FLOAT"
    link(ng, sw, n.inputs["Switch"])
    for key, v in (("False", fval), ("True", tval)):
        if hasattr(v, "is_output"):
            link(ng, v, n.inputs[key])
        else:
            n.inputs[key].default_value = v
    return n.outputs["Output"]


def _common_step_inputs(ng):
    new_input(ng, "Fill Bottom", "NodeSocketBool", default_value=True)
    tt = new_input(ng, "Tread Thickness", "NodeSocketFloat", default_value=0.15, min_value=0.01)
    tt.subtype = "DISTANCE"
    new_input(ng, "Side Rails", "NodeSocketBool", default_value=False)
    rh = new_input(ng, "Rail Height", "NodeSocketFloat", default_value=1.0, min_value=0.01)
    rh.subtype = "DISTANCE"
    rt = new_input(ng, "Rail Thickness", "NodeSocketFloat", default_value=0.08, min_value=0.005)
    rt.subtype = "DISTANCE"
    ps = new_input(ng, "Post Spacing", "NodeSocketFloat", default_value=0.6, min_value=0.05)
    ps.subtype = "DISTANCE"


def _step_height_and_center(ng, top, gin, x):
    """(box_height, box_center_z) honouring Fill Bottom: solid to the floor, or a thin tread."""
    tread = gin.outputs["Tread Thickness"]
    half_tread = fmath(ng, "MULTIPLY", tread, 0.5, location=(x, -360))
    half_top = fmath(ng, "MULTIPLY", top, 0.5, location=(x, -440))
    open_center = fmath(ng, "SUBTRACT", top, half_tread.outputs[0], location=(x + 160, -360))
    box_h = _fswitch(ng, gin.outputs["Fill Bottom"], tread, top, location=(x + 160, -200))
    center = _fswitch(ng, gin.outputs["Fill Bottom"], open_center.outputs[0],
                      half_top.outputs[0], location=(x + 340, -260))
    return box_h, center


def _swept_rail_and_posts(ng, line_geo, rail_t, rail_h, post_spacing, base):
    """Rail swept along a (mesh-line) path + vertical posts. Posts are placed by resampling
    the rail at Post Spacing, so they're independent of the step count."""
    bx, by = base
    m2c = node(ng, "GeometryNodeMeshToCurve", location=(bx, by))
    link(ng, line_geo, m2c.inputs["Mesh"])
    zup = node(ng, "GeometryNodeSetCurveNormal", location=(bx + 180, by))
    zup.inputs["Mode"].default_value = "Z Up"
    link(ng, m2c.outputs["Curve"], zup.inputs["Curve"])
    rail = sweep_rect_along(ng, zup.outputs["Curve"], rail_t, rail_t, off_x=0.0, off_y=0.0,
                            location=(bx + 360, by + 140))

    rs = node(ng, "GeometryNodeResampleCurve", location=(bx + 180, by - 160))
    rs.inputs["Mode"].default_value = "Length"
    link(ng, zup.outputs["Curve"], rs.inputs["Curve"])
    link(ng, post_spacing, rs.inputs["Length"])
    half_r = fmath(ng, "MULTIPLY", rail_h, -0.5, location=(bx + 180, by - 320))
    lower = combine_xyz(ng, 0.0, 0.0, half_r.outputs[0], location=(bx + 360, by - 320))
    pset = node(ng, "GeometryNodeSetPosition", location=(bx + 540, by - 160))
    link(ng, rs.outputs["Curve"], pset.inputs["Geometry"])
    link(ng, lower.outputs[0], pset.inputs["Offset"])
    pscale = combine_xyz(ng, rail_t, rail_t, rail_h, location=(bx + 540, by - 340))
    cube = _unit_cube(ng, (bx + 540, by - 460))
    iop = node(ng, "GeometryNodeInstanceOnPoints", location=(bx + 720, by - 160))
    link(ng, pset.outputs["Geometry"], iop.inputs["Points"])
    link(ng, cube.outputs["Mesh"], iop.inputs["Instance"])
    link(ng, pscale.outputs[0], iop.inputs["Scale"])
    posts = node(ng, "GeometryNodeRealizeInstances", location=(bx + 920, by - 160))
    link(ng, iop.outputs["Instances"], posts.inputs[0])

    j = node(ng, "GeometryNodeJoinGeometry", location=(bx + 1120, by))
    link(ng, rail, j.inputs[0])
    link(ng, posts.outputs[0], j.inputs[0])
    return j.outputs[0]


# --------------------------------------------------------------------------- #
# Straight stairs
# --------------------------------------------------------------------------- #
def build_stairs(ng):
    new_input(ng, "Steps", "NodeSocketInt", default_value=8, min_value=1, max_value=200)
    w = new_input(ng, "Width", "NodeSocketFloat", default_value=2.0, min_value=0.001)
    w.subtype = "DISTANCE"
    sh = new_input(ng, "Step Height", "NodeSocketFloat", default_value=0.3, min_value=0.001)
    sh.subtype = "DISTANCE"
    sd = new_input(ng, "Step Depth", "NodeSocketFloat", default_value=0.35, min_value=0.001)
    sd.subtype = "DISTANCE"
    _common_step_inputs(ng)
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1500, 0))
    gout = node(ng, "NodeGroupOutput", location=(2100, 0))
    steps, width = gin.outputs["Steps"], gin.outputs["Width"]
    sh_o, sd_o = gin.outputs["Step Height"], gin.outputs["Step Depth"]

    line = node(ng, "GeometryNodeMeshLine", location=(-1280, 120))
    line.mode = "OFFSET"; line.count_mode = "TOTAL"
    link(ng, steps, line.inputs["Count"])
    line.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
    off = combine_xyz(ng, sd_o, 0.0, 0.0, location=(-1460, -120))
    link(ng, off.outputs[0], line.inputs["Offset"])

    idx = node(ng, "GeometryNodeInputIndex", location=(-1280, -260))
    idx1 = fmath(ng, "ADD", idx.outputs[0], 1.0, location=(-1100, -260))
    top = fmath(ng, "MULTIPLY", idx1.outputs[0], sh_o, location=(-920, -260))
    box_h, center_z = _step_height_and_center(ng, top.outputs[0], gin, -740)

    lift = combine_xyz(ng, 0.0, 0.0, center_z, location=(-360, -120))
    setpos = node(ng, "GeometryNodeSetPosition", location=(-180, 120))
    link(ng, line.outputs["Mesh"], setpos.inputs["Geometry"])
    link(ng, lift.outputs[0], setpos.inputs["Offset"])
    scale = combine_xyz(ng, sd_o, width, box_h, location=(-180, -120))
    cube = _unit_cube(ng, (-180, -300))
    iop = node(ng, "GeometryNodeInstanceOnPoints", location=(60, 60))
    link(ng, setpos.outputs["Geometry"], iop.inputs["Points"])
    link(ng, cube.outputs["Mesh"], iop.inputs["Instance"])
    link(ng, scale.outputs[0], iop.inputs["Scale"])
    real = node(ng, "GeometryNodeRealizeInstances", location=(280, 60))
    link(ng, iop.outputs["Instances"], real.inputs[0])
    steps_geo = real.outputs[0]

    # --- side rails: a line per side at rail height, swept + posts; mirror to the other side
    rail_t, rail_h = gin.outputs["Rail Thickness"], gin.outputs["Rail Height"]
    side_y = fmath(ng, "SUBTRACT", fmath(ng, "MULTIPLY", width, 0.5, location=(60, -360)).outputs[0],
                   rail_t, location=(240, -360))
    railz = fmath(ng, "ADD", top.outputs[0], rail_h, location=(240, -460))
    rline = node(ng, "GeometryNodeMeshLine", location=(60, -560))
    rline.mode = "OFFSET"; rline.count_mode = "TOTAL"
    link(ng, steps, rline.inputs["Count"])
    rline.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
    link(ng, off.outputs[0], rline.inputs["Offset"])
    roff = combine_xyz(ng, 0.0, side_y.outputs[0], railz.outputs[0], location=(240, -560))
    rset = node(ng, "GeometryNodeSetPosition", location=(420, -560))
    link(ng, rline.outputs["Mesh"], rset.inputs["Geometry"])
    link(ng, roff.outputs[0], rset.inputs["Offset"])
    left = _swept_rail_and_posts(ng, rset.outputs["Geometry"], rail_t, rail_h,
                                 gin.outputs["Post Spacing"], base=(620, -560))
    mirror = node(ng, "GeometryNodeTransform", location=(1720, -560))
    link(ng, left, mirror.inputs["Geometry"])
    mirror.inputs["Scale"].default_value = (1.0, -1.0, 1.0)
    rails = node(ng, "GeometryNodeJoinGeometry", location=(1900, -300))
    link(ng, left, rails.inputs[0])
    link(ng, mirror.outputs["Geometry"], rails.inputs[0])
    with_rails = node(ng, "GeometryNodeJoinGeometry", location=(700, 60))
    link(ng, steps_geo, with_rails.inputs[0])
    link(ng, rails.outputs[0], with_rails.inputs[0])
    chosen = _gswitch(ng, gin.outputs["Side Rails"], steps_geo, with_rails.outputs[0],
                      location=(900, 60))

    stepsm1 = fmath(ng, "SUBTRACT", steps, 1.0, location=(900, -160))
    runspan = fmath(ng, "MULTIPLY", stepsm1.outputs[0], sd_o, location=(1060, -160))
    shiftx = fmath(ng, "MULTIPLY", runspan.outputs[0], -0.5, location=(1220, -160))
    trans = combine_xyz(ng, shiftx.outputs[0], 0.0, 0.0, location=(1220, 20))
    xform = node(ng, "GeometryNodeTransform", location=(1420, 60))
    link(ng, chosen, xform.inputs["Geometry"])
    link(ng, trans.outputs[0], xform.inputs["Translation"])

    geo = store_grid_attributes(ng, xform.outputs["Geometry"])
    setmat = node(ng, "GeometryNodeSetMaterial", location=(1900, 60))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def _rail_along_curve(ng, base_curve, rail_t, rail_h, post_spacing, base):
    """Sweep a rail along a curve + drop posts (resampled at Post Spacing, turned to face
    along the path). For the spline-based curved stairs' side rails."""
    bx, by = base
    zup = node(ng, "GeometryNodeSetCurveNormal", location=(bx, by))
    zup.inputs["Mode"].default_value = "Z Up"
    link(ng, base_curve, zup.inputs["Curve"])
    spine = zup.outputs["Curve"]
    rail = sweep_rect_along(ng, spine, rail_t, rail_t, off_x=0.0, off_y=0.0, location=(bx + 200, by + 140))

    rs = node(ng, "GeometryNodeResampleCurve", location=(bx + 200, by - 160))
    rs.inputs["Mode"].default_value = "Length"
    link(ng, spine, rs.inputs["Curve"])
    link(ng, post_spacing, rs.inputs["Length"])
    halfr = fmath(ng, "MULTIPLY", rail_h, -0.5, location=(bx + 200, by - 320))
    lower = combine_xyz(ng, 0.0, 0.0, halfr.outputs[0], location=(bx + 380, by - 320))
    pset = node(ng, "GeometryNodeSetPosition", location=(bx + 560, by - 160))
    link(ng, rs.outputs["Curve"], pset.inputs["Geometry"])
    link(ng, lower.outputs[0], pset.inputs["Offset"])
    ptan = node(ng, "GeometryNodeInputTangent", location=(bx + 380, by - 460))
    psep = node(ng, "ShaderNodeSeparateXYZ", location=(bx + 560, by - 460))
    link(ng, ptan.outputs[0], psep.inputs[0])
    pyaw = fmath(ng, "ARCTAN2", psep.outputs["Y"], psep.outputs["X"], location=(bx + 740, by - 460))
    peul = combine_xyz(ng, 0.0, 0.0, pyaw.outputs[0], location=(bx + 740, by - 360))
    prot = node(ng, "FunctionNodeEulerToRotation", location=(bx + 900, by - 360))
    link(ng, peul.outputs[0], prot.inputs[0])
    pscale = combine_xyz(ng, rail_t, rail_t, rail_h, location=(bx + 560, by - 300))
    cube = _unit_cube(ng, (bx + 560, by - 580))
    iop = node(ng, "GeometryNodeInstanceOnPoints", location=(bx + 940, by - 160))
    link(ng, pset.outputs["Geometry"], iop.inputs["Points"])
    link(ng, cube.outputs["Mesh"], iop.inputs["Instance"])
    link(ng, prot.outputs[0], iop.inputs["Rotation"])
    link(ng, pscale.outputs[0], iop.inputs["Scale"])
    posts = node(ng, "GeometryNodeRealizeInstances", location=(bx + 1140, by - 160))
    link(ng, iop.outputs["Instances"], posts.inputs[0])
    j = node(ng, "GeometryNodeJoinGeometry", location=(bx + 1340, by))
    link(ng, rail, j.inputs[0])
    link(ng, posts.outputs[0], j.inputs[0])
    return j.outputs[0]


# --------------------------------------------------------------------------- #
# Curved stairs - steps climb along an editable spline (the object's curve).
# --------------------------------------------------------------------------- #
def build_stairs_curved(ng):
    new_input(ng, "Geometry", "NodeSocketGeometry")
    new_input(ng, "Steps", "NodeSocketInt", default_value=12, min_value=1, max_value=400)
    sw = new_input(ng, "Step Width", "NodeSocketFloat", default_value=2.0, min_value=0.001)
    sw.subtype = "DISTANCE"
    shh = new_input(ng, "Step Height", "NodeSocketFloat", default_value=0.3, min_value=0.001)
    shh.subtype = "DISTANCE"
    _common_step_inputs(ng)
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1700, 0))
    gout = node(ng, "NodeGroupOutput", location=(2300, 0))
    curve, steps = gin.outputs["Geometry"], gin.outputs["Steps"]
    sw_o, sh_o = gin.outputs["Step Width"], gin.outputs["Step Height"]

    # One step point per resampled count, climbing by Step Height, turned along the path.
    rs = node(ng, "GeometryNodeResampleCurve", location=(-1480, 160))
    rs.inputs["Mode"].default_value = "Count"
    link(ng, curve, rs.inputs["Curve"])
    link(ng, steps, rs.inputs["Count"])
    idx = node(ng, "GeometryNodeInputIndex", location=(-1480, -120))
    idx1 = fmath(ng, "ADD", idx.outputs[0], 1.0, location=(-1300, -200))
    top = fmath(ng, "MULTIPLY", idx1.outputs[0], sh_o, location=(-1120, -200))
    box_h, center_z = _step_height_and_center(ng, top.outputs[0], gin, -940)

    clen = node(ng, "GeometryNodeCurveLength", location=(-1300, 320))
    link(ng, curve, clen.inputs[0])
    depth = fmath(ng, "DIVIDE", clen.outputs["Length"], steps, location=(-1120, 320))
    tan = node(ng, "GeometryNodeInputTangent", location=(-1300, -360))
    tsep = node(ng, "ShaderNodeSeparateXYZ", location=(-1120, -360))
    link(ng, tan.outputs[0], tsep.inputs[0])
    yaw = fmath(ng, "ARCTAN2", tsep.outputs["Y"], tsep.outputs["X"], location=(-940, -360))

    lift = combine_xyz(ng, 0.0, 0.0, center_z, location=(-760, 120))
    setpos = node(ng, "GeometryNodeSetPosition", location=(-560, 160))
    link(ng, rs.outputs["Curve"], setpos.inputs["Geometry"])
    link(ng, lift.outputs[0], setpos.inputs["Offset"])
    eul = combine_xyz(ng, 0.0, 0.0, yaw.outputs[0], location=(-760, -120))
    rot = node(ng, "FunctionNodeEulerToRotation", location=(-560, -120))
    link(ng, eul.outputs[0], rot.inputs[0])
    scale = combine_xyz(ng, depth.outputs[0], sw_o, box_h, location=(-560, -260))

    # step-local grid frame (vector attrs aren't rotated by the instance, so the grid stays
    # square to each step's faces - see straight stairs note).
    cube = _unit_cube(ng, (-560, -440))
    lpos = node(ng, "GeometryNodeInputPosition", location=(-760, -480))
    cube_a = store_named(ng, cube.outputs["Mesh"], "bb_lpos", lpos.outputs[0],
                         domain="POINT", location=(-560, -560))
    lnorm = node(ng, "GeometryNodeInputNormal", location=(-760, -640))
    cube_a = store_named(ng, cube_a, "bb_lnorm", lnorm.outputs[0], domain="FACE", location=(-360, -560))
    pts_a = store_named(ng, setpos.outputs["Geometry"], "bb_ssize", scale.outputs[0],
                        domain="POINT", location=(-360, 160))
    iop = node(ng, "GeometryNodeInstanceOnPoints", location=(-160, 80))
    link(ng, pts_a, iop.inputs["Points"])
    link(ng, cube_a, iop.inputs["Instance"])
    link(ng, rot.outputs[0], iop.inputs["Rotation"])
    link(ng, scale.outputs[0], iop.inputs["Scale"])
    real = node(ng, "GeometryNodeRealizeInstances", location=(40, 80))
    link(ng, iop.outputs["Instances"], real.inputs[0])
    co_local = vmath(ng, "MULTIPLY", named_attr(ng, "bb_lpos", location=(40, -200)),
                     named_attr(ng, "bb_ssize", location=(40, -340)), location=(220, -240))
    co = vmath(ng, "MULTIPLY", co_local.outputs[0], object_scale(ng, location=(220, -420)),
               location=(400, -300))
    g1 = store_named(ng, real.outputs[0], "bb_grid_co", co.outputs[0], domain="POINT", location=(480, 80))
    steps_geo = store_named(ng, g1, "bb_grid_n", named_attr(ng, "bb_lnorm", location=(480, -120)),
                            domain="FACE", location=(660, 80))

    # --- side rails: offset the step points to each side (curve binormal), raise, sweep ---
    rail_t, rail_h = gin.outputs["Rail Thickness"], gin.outputs["Rail Height"]
    railz = fmath(ng, "ADD", top.outputs[0], rail_h, location=(-940, -560))
    half_sw = fmath(ng, "MULTIPLY", sw_o, 0.5, location=(-940, -640))
    off_in = fmath(ng, "SUBTRACT", half_sw.outputs[0], rail_t, location=(-760, -640))
    neg_off = fmath(ng, "MULTIPLY", off_in.outputs[0], -1.0, location=(-580, -640))
    zupv = combine_xyz(ng, 0.0, 0.0, 1.0, location=(-940, -760))
    binorm = vmath(ng, "NORMALIZE",
                   vmath(ng, "CROSS_PRODUCT", tan.outputs[0], zupv.outputs[0],
                         location=(-760, -760)).outputs[0], location=(-580, -760))

    def rail(sign_socket, by):
        lat = vmath(ng, "SCALE", binorm.outputs[0], location=(-380, by))
        link(ng, sign_socket, lat.inputs[3])
        zc = combine_xyz(ng, 0.0, 0.0, railz.outputs[0], location=(-380, by - 120))
        off = vmath(ng, "ADD", lat.outputs[0], zc.outputs[0], location=(-200, by))
        rl = node(ng, "GeometryNodeSetPosition", location=(-20, by))
        link(ng, rs.outputs["Curve"], rl.inputs["Geometry"])
        link(ng, off.outputs[0], rl.inputs["Offset"])
        return _rail_along_curve(ng, rl.outputs["Geometry"], rail_t, rail_h,
                                 gin.outputs["Post Spacing"], base=(160, by))

    rail_in = rail(off_in.outputs[0], -900)
    rail_out = rail(neg_off.outputs[0], -1400)
    rails = node(ng, "GeometryNodeJoinGeometry", location=(1700, -1100))
    link(ng, rail_in, rails.inputs[0])
    link(ng, rail_out, rails.inputs[0])
    rails_grid = store_grid_attributes(ng, rails.outputs[0], base_x=1900.0, base_y=-1500.0)
    all_geo = node(ng, "GeometryNodeJoinGeometry", location=(900, 80))
    link(ng, steps_geo, all_geo.inputs[0])
    link(ng, rails_grid, all_geo.inputs[0])
    chosen = _gswitch(ng, gin.outputs["Side Rails"], steps_geo, all_geo.outputs[0], location=(1100, 80))

    setmat = node(ng, "GeometryNodeSetMaterial", location=(2000, 80))
    link(ng, chosen, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def ensure_stairs():
    return ensure_group(GROUP_NAMES[TYPE_STAIRS], build_stairs, GN_VERSION)


def ensure_stairs_curved():
    return ensure_group(GROUP_NAMES[TYPE_STAIRS_CURVED], build_stairs_curved, GN_VERSION)
