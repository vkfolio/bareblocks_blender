# BareBlocks - procedural multi-species Tree (pure Geometry Nodes, blockout style).
#
# One recipe: a tapered trunk (optionally a multi-trunk ring) + a canopy whose silhouette is
# chosen by a Canopy Shape index. The canopy is low-poly foliage blobs instanced on the
# vertices of a crown volume (sphere / cone / column / umbrella), a radial frond crown (palm),
# or nothing (bamboo). Species are registry presets that set these inputs (see core.ids).
#
# Canopy Shape: 0 Sphere  1 Cone  2 Column  3 Umbrella  4 Fronds  5 None

import math

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath, vmath,
                     store_grid_attributes, shade_smooth_by_angle)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_TREE, GN_VERSION


def _f(ng, name, default, mn=0.0, mx=None):
    s = new_input(ng, name, "NodeSocketFloat", default_value=default, min_value=mn)
    if mx is not None:
        s.max_value = mx
    s.subtype = "DISTANCE"
    return s


def _eq(ng, socket, k, loc):
    """1.0 when int socket == k (within 0.5), else 0.0 - drives a geometry Switch."""
    n = fmath(ng, "COMPARE", socket, float(k), location=loc)
    n.inputs[2].default_value = 0.5  # epsilon
    return n


def _switch_geo(ng, cond, false_geo, true_geo, loc):
    sw = node(ng, "GeometryNodeSwitch", location=loc)
    sw.input_type = "GEOMETRY"
    link(ng, cond, sw.inputs["Switch"])
    link(ng, false_geo, sw.inputs["False"])
    link(ng, true_geo, sw.inputs["True"])
    return sw.outputs["Output"]


def _ico(ng, subdiv, loc):
    n = node(ng, "GeometryNodeMeshIcoSphere", location=loc)
    n.inputs["Radius"].default_value = 1.0
    if hasattr(subdiv, "is_output"):
        link(ng, subdiv, n.inputs["Subdivisions"])
    else:
        n.inputs["Subdivisions"].default_value = subdiv
    return n.outputs["Mesh"]


def _scaled(ng, geo, sx, sy, sz, loc):
    sc = combine_xyz(ng, sx, sy, sz, location=(loc[0], loc[1] - 150))
    xf = node(ng, "GeometryNodeTransform", location=loc)
    link(ng, geo, xf.inputs["Geometry"])
    link(ng, sc.outputs[0], xf.inputs["Scale"])
    return xf.outputs["Geometry"]


def build_tree(ng):
    _f(ng, "Height", 6.0, 0.1)
    fr = new_input(ng, "Trunk Height Frac", "NodeSocketFloat", default_value=0.35,
                   min_value=0.0, max_value=1.0)
    fr.subtype = "FACTOR"
    _f(ng, "Trunk Radius", 0.18, 0.005)
    tp = new_input(ng, "Trunk Taper", "NodeSocketFloat", default_value=0.6, min_value=0.0, max_value=1.0)
    tp.subtype = "FACTOR"
    new_input(ng, "Trunk Count", "NodeSocketInt", default_value=1, min_value=1, max_value=24)
    _f(ng, "Trunk Spread", 0.0, 0.0)
    new_input(ng, "Canopy Shape", "NodeSocketInt", default_value=0, min_value=0, max_value=5)
    _f(ng, "Canopy Width", 3.0, 0.05)
    _f(ng, "Canopy Height", 3.0, 0.05)
    new_input(ng, "Foliage Density", "NodeSocketInt", default_value=2, min_value=1, max_value=4)
    dr = new_input(ng, "Droop", "NodeSocketFloat", default_value=0.0, min_value=0.0, max_value=1.0)
    dr.subtype = "FACTOR"
    new_input(ng, "Seed", "NodeSocketInt", default_value=0)
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1700, 0))
    gout = node(ng, "NodeGroupOutput", location=(2100, 0))
    H = gin.outputs["Height"]
    W, CH = gin.outputs["Canopy Width"], gin.outputs["Canopy Height"]
    shape = gin.outputs["Canopy Shape"]
    half_w = fmath(ng, "MULTIPLY", W, 0.5, location=(-1500, -700))
    half_ch = fmath(ng, "MULTIPLY", CH, 0.5, location=(-1500, -780))
    base_z = fmath(ng, "MULTIPLY", gin.outputs["Trunk Height Frac"], H, location=(-1500, -860))
    center_z = fmath(ng, "ADD", base_z.outputs[0], half_ch.outputs[0], location=(-1320, -860))

    # ---------------- trunk(s) ----------------
    # Trunk rises to the canopy base (+ a little into it) so it tucks in, not poking out the top.
    trunk_h = fmath(ng, "ADD", base_z.outputs[0],
                    fmath(ng, "MULTIPLY", CH, 0.4, location=(-1680, 300)).outputs[0],
                    location=(-1500, 300))
    taper_top = fmath(ng, "MULTIPLY", gin.outputs["Trunk Radius"], gin.outputs["Trunk Taper"],
                      location=(-1500, 360))
    trunk_cone = node(ng, "GeometryNodeMeshCone", location=(-1320, 360))
    trunk_cone.inputs["Vertices"].default_value = 8
    link(ng, taper_top.outputs[0], trunk_cone.inputs["Radius Top"])
    link(ng, gin.outputs["Trunk Radius"], trunk_cone.inputs["Radius Bottom"])
    link(ng, trunk_h.outputs[0], trunk_cone.inputs["Depth"])
    trunk_up = node(ng, "GeometryNodeTransform", location=(-1140, 360))
    link(ng, trunk_cone.outputs["Mesh"], trunk_up.inputs["Geometry"])
    link(ng, combine_xyz(ng, 0.0, 0.0, fmath(ng, "MULTIPLY", trunk_h.outputs[0], 0.5,
         location=(-1320, 240)).outputs[0], location=(-1320, 200)).outputs[0],
         trunk_up.inputs["Translation"])

    line = node(ng, "GeometryNodeMeshLine", location=(-1320, 80))
    line.mode = "OFFSET"; line.count_mode = "TOTAL"
    link(ng, gin.outputs["Trunk Count"], line.inputs["Count"])
    line.inputs["Offset"].default_value = (0.0, 0.0, 0.0)
    idx = node(ng, "GeometryNodeInputIndex", location=(-1320, -60))
    tau = fmath(ng, "DIVIDE", 6.2831853, gin.outputs["Trunk Count"], location=(-1140, -60))
    ang = fmath(ng, "MULTIPLY", idx.outputs[0], tau.outputs[0], location=(-960, -60))
    tx = fmath(ng, "MULTIPLY", fmath(ng, "COSINE", ang.outputs[0], location=(-780, 0)).outputs[0],
               gin.outputs["Trunk Spread"], location=(-600, 0))
    ty = fmath(ng, "MULTIPLY", fmath(ng, "SINE", ang.outputs[0], location=(-780, -120)).outputs[0],
               gin.outputs["Trunk Spread"], location=(-600, -120))
    ring = node(ng, "GeometryNodeSetPosition", location=(-420, 40))
    link(ng, line.outputs["Mesh"], ring.inputs["Geometry"])
    link(ng, combine_xyz(ng, tx.outputs[0], ty.outputs[0], 0.0, location=(-600, 120)).outputs[0],
         ring.inputs["Position"])
    tiop = node(ng, "GeometryNodeInstanceOnPoints", location=(-220, 120))
    link(ng, ring.outputs["Geometry"], tiop.inputs["Points"])
    link(ng, trunk_up.outputs["Geometry"], tiop.inputs["Instance"])
    trunks = node(ng, "GeometryNodeRealizeInstances", location=(-40, 120))
    link(ng, tiop.outputs["Instances"], trunks.inputs[0])

    # ---------------- crown volume (centred at origin, scaled to W x CH) ----------------
    dens = gin.outputs["Foliage Density"]
    sphere_m = _scaled(ng, _ico(ng, dens, (-1320, -300)), half_w.outputs[0], half_w.outputs[0],
                       half_ch.outputs[0], (-1100, -300))
    cone_src = node(ng, "GeometryNodeMeshCone", location=(-1320, -460))
    cone_src.inputs["Vertices"].default_value = 10
    link(ng, half_w.outputs[0], cone_src.inputs["Radius Bottom"])
    cone_src.inputs["Radius Top"].default_value = 0.0
    link(ng, CH, cone_src.inputs["Depth"])
    cone_m = cone_src.outputs["Mesh"]
    col_w = fmath(ng, "MULTIPLY", half_w.outputs[0], 0.55, location=(-1320, -560))
    column_m = _scaled(ng, _ico(ng, dens, (-1320, -640)), col_w.outputs[0], col_w.outputs[0],
                       half_ch.outputs[0], (-1100, -640))
    umb_h = fmath(ng, "MULTIPLY", half_ch.outputs[0], 0.4, location=(-1320, -940))
    umbrella_m = _scaled(ng, _ico(ng, dens, (-1320, -1020)), half_w.outputs[0], half_w.outputs[0],
                         umb_h.outputs[0], (-1100, -1020))

    crown = sphere_m
    crown = _switch_geo(ng, _eq(ng, shape, 1, (-900, -360)).outputs[0], crown, cone_m, (-720, -360))
    crown = _switch_geo(ng, _eq(ng, shape, 2, (-900, -540)).outputs[0], crown, column_m, (-540, -540))
    crown = _switch_geo(ng, _eq(ng, shape, 3, (-900, -720)).outputs[0], crown, umbrella_m, (-360, -720))

    # The crown MESH is the canopy (clean blockout silhouette). Droop deforms it downward by
    # horizontal distance from the trunk axis (weeping); then place it at the canopy centre.
    p_in = node(ng, "GeometryNodeInputPosition", location=(-180, -560))
    p_xy = vmath(ng, "MULTIPLY", p_in.outputs[0], (1.0, 1.0, 0.0), location=(0, -560))
    p_dist = vmath(ng, "LENGTH", p_xy.outputs[0], location=(180, -560))
    droop_z = fmath(ng, "MULTIPLY",
                    fmath(ng, "MULTIPLY", p_dist.outputs["Value"], gin.outputs["Droop"],
                          location=(360, -560)).outputs[0], -1.0, location=(360, -640))
    droop = node(ng, "GeometryNodeSetPosition", location=(220, -360))
    link(ng, crown, droop.inputs["Geometry"])
    link(ng, combine_xyz(ng, 0.0, 0.0, droop_z.outputs[0], location=(40, -700)).outputs[0],
         droop.inputs["Offset"])
    crown_at = node(ng, "GeometryNodeTransform", location=(440, -360))
    link(ng, droop.outputs["Geometry"], crown_at.inputs["Geometry"])
    link(ng, combine_xyz(ng, 0.0, 0.0, center_z.outputs[0], location=(260, -480)).outputs[0],
         crown_at.inputs["Translation"])
    canopy_solid = crown_at.outputs["Geometry"]

    # ---------------- fronds (palm) ----------------
    fronds = _build_fronds(ng, gin, base_z.outputs[0])

    # empty geometry for "None"
    empty = node(ng, "GeometryNodePoints", location=(860, -900))
    empty.inputs["Count"].default_value = 0

    canopy = _switch_geo(ng, _eq(ng, shape, 4, (1040, -200)).outputs[0], canopy_solid, fronds,
                         (1220, -200))
    canopy = _switch_geo(ng, _eq(ng, shape, 5, (1040, -420)).outputs[0], canopy, empty.outputs[0],
                         (1400, -300))

    joined = node(ng, "GeometryNodeJoinGeometry", location=(1600, 60))
    link(ng, trunks.outputs[0], joined.inputs[0])
    link(ng, canopy, joined.inputs[0])
    smoothed = shade_smooth_by_angle(ng, joined.outputs[0], base_x=1500.0, base_y=-1300.0)
    geo = store_grid_attributes(ng, smoothed, base_x=1800.0, base_y=-1300.0)
    setmat = node(ng, "GeometryNodeSetMaterial", location=(2000, 60))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def _build_fronds(ng, gin, apex_z):
    """A radial burst of long thin cones at the apex (palm crown). Returns realized mesh."""
    count = gin.outputs["Foliage Density"]
    n = fmath(ng, "MULTIPLY", count, 4.0, location=(900, -1100))  # more fronds than blob density
    line = node(ng, "GeometryNodeMeshLine", location=(1080, -1100))
    line.mode = "OFFSET"; line.count_mode = "TOTAL"
    link(ng, n.outputs[0], line.inputs["Count"])
    line.inputs["Offset"].default_value = (0.0, 0.0, 0.0)
    setp = node(ng, "GeometryNodeSetPosition", location=(1260, -1100))
    link(ng, line.outputs["Mesh"], setp.inputs["Geometry"])
    link(ng, combine_xyz(ng, 0.0, 0.0, apex_z, location=(1080, -1240)).outputs[0],
         setp.inputs["Position"])
    idx = node(ng, "GeometryNodeInputIndex", location=(1080, -1360))
    tau = fmath(ng, "DIVIDE", 6.2831853, n.outputs[0], location=(1260, -1360))
    ang = fmath(ng, "MULTIPLY", idx.outputs[0], tau.outputs[0], location=(1440, -1360))
    eul = combine_xyz(ng, math.radians(115.0), 0.0, ang.outputs[0], location=(1440, -1240))
    rot = node(ng, "FunctionNodeEulerToRotation", location=(1620, -1240))
    link(ng, eul.outputs[0], rot.inputs[0])
    # frond mesh: long thin cone pointing +Z, base at origin
    frond = node(ng, "GeometryNodeMeshCone", location=(1080, -1480))
    frond.inputs["Vertices"].default_value = 4
    fw = fmath(ng, "MULTIPLY", gin.outputs["Canopy Width"], 0.06, location=(900, -1480))
    link(ng, fw.outputs[0], frond.inputs["Radius Bottom"])
    frond.inputs["Radius Top"].default_value = 0.02
    link(ng, gin.outputs["Canopy Width"], frond.inputs["Depth"])
    fr_up = node(ng, "GeometryNodeTransform", location=(1260, -1480))
    link(ng, frond.outputs["Mesh"], fr_up.inputs["Geometry"])
    link(ng, combine_xyz(ng, 0.0, 0.0, fmath(ng, "MULTIPLY", gin.outputs["Canopy Width"], 0.5,
         location=(1080, -1600)).outputs[0], location=(1080, -1640)).outputs[0],
         fr_up.inputs["Translation"])
    iop = node(ng, "GeometryNodeInstanceOnPoints", location=(1820, -1180))
    link(ng, setp.outputs["Geometry"], iop.inputs["Points"])
    link(ng, fr_up.outputs["Geometry"], iop.inputs["Instance"])
    link(ng, rot.outputs[0], iop.inputs["Rotation"])
    real = node(ng, "GeometryNodeRealizeInstances", location=(2000, -1180))
    link(ng, iop.outputs["Instances"], real.inputs[0])
    return real.outputs[0]


def ensure_tree():
    return ensure_group(GROUP_NAMES[TYPE_TREE], build_tree, GN_VERSION)
