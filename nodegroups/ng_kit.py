# BareBlocks - environment kit: composite props built from boxes / cylinders / spheres so the
# AI agent (and you) can dress a scene. Tree, Bush, Rock, Well, Bridge, Tower, Barrier, Bench,
# Lamppost, Fountain. All sit on the ground (origin at base).

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     store_grid_attributes, shade_smooth_by_angle)
from .shader_blockout import ensure_material
from ..core.ids import (GROUP_NAMES, GN_VERSION, TYPE_BUSH, TYPE_ROCK, TYPE_WELL,
                        TYPE_BRIDGE, TYPE_TOWER, TYPE_BARRIER, TYPE_BENCH, TYPE_LAMPPOST,
                        TYPE_FOUNTAIN)


# --------------------------------------------------------------------------- #
# tiny builders (accept sockets OR plain numbers for every dimension/offset)
# --------------------------------------------------------------------------- #
def _inp(ng, socket, val):
    if hasattr(val, "is_output"):
        link(ng, val, socket)
    else:
        socket.default_value = val


def _xform(ng, geo, tx, ty, tz, base):
    tr = combine_xyz(ng, tx, ty, tz, location=(base[0], base[1] - 150))
    xf = node(ng, "GeometryNodeTransform", location=(base[0] + 160, base[1]))
    link(ng, geo, xf.inputs["Geometry"])
    link(ng, tr.outputs[0], xf.inputs["Translation"])
    return xf.outputs["Geometry"]


def _cube(ng, sx, sy, sz, tx=0.0, ty=0.0, tz=0.0, base=(0, 0)):
    size = combine_xyz(ng, sx, sy, sz, location=base)
    cube = node(ng, "GeometryNodeMeshCube", location=(base[0] + 160, base[1] + 80))
    link(ng, size.outputs[0], cube.inputs["Size"])
    return _xform(ng, cube.outputs["Mesh"], tx, ty, tz, (base[0] + 340, base[1]))


def _cyl(ng, radius, depth, sides, tx=0.0, ty=0.0, tz=0.0, base=(0, 0)):
    c = node(ng, "GeometryNodeMeshCylinder", location=(base[0] + 160, base[1] + 80))
    _inp(ng, c.inputs["Vertices"], sides)
    _inp(ng, c.inputs["Radius"], radius)
    _inp(ng, c.inputs["Depth"], depth)
    return _xform(ng, c.outputs["Mesh"], tx, ty, tz, (base[0] + 340, base[1]))


def _sphere(ng, radius, tx=0.0, ty=0.0, tz=0.0, base=(0, 0), segs=16, rings=8):
    s = node(ng, "GeometryNodeMeshUVSphere", location=(base[0] + 160, base[1] + 80))
    _inp(ng, s.inputs["Segments"], segs)
    _inp(ng, s.inputs["Rings"], rings)
    _inp(ng, s.inputs["Radius"], radius)
    return _xform(ng, s.outputs["Mesh"], tx, ty, tz, (base[0] + 340, base[1]))


def _join(ng, geos, base=(0, 0)):
    jn = node(ng, "GeometryNodeJoinGeometry", location=base)
    for g in geos:
        link(ng, g, jn.inputs[0])
    return jn.outputs[0]


def _finish(ng, geo, gin, gout, smooth=True, loc_x=1300):
    g = shade_smooth_by_angle(ng, geo, base_x=loc_x - 250, base_y=-1000.0) if smooth else geo
    g = store_grid_attributes(ng, g, base_x=loc_x - 250, base_y=-1500.0)
    setmat = node(ng, "GeometryNodeSetMaterial", location=(loc_x, 80))
    link(ng, g, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def _f(ng, name, default, mn=0.0):
    s = new_input(ng, name, "NodeSocketFloat", default_value=default, min_value=mn)
    s.subtype = "DISTANCE"
    return s


def _io(ng):
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")
    gin = node(ng, "NodeGroupInput", location=(-1200, 0))
    gout = node(ng, "NodeGroupOutput", location=(1500, 0))
    return gin, gout


# --------------------------------------------------------------------------- #
# builders
# --------------------------------------------------------------------------- #
def build_bush(ng):
    _f(ng, "Radius", 0.6, 0.01)
    _f(ng, "Height", 0.8, 0.01)
    gin, gout = _io(ng)
    r, h = gin.outputs["Radius"], gin.outputs["Height"]
    s = node(ng, "GeometryNodeMeshUVSphere", location=(-700, 120))
    _inp(ng, s.inputs["Radius"], r)
    s.inputs["Segments"].default_value = 14
    s.inputs["Rings"].default_value = 8
    half_h = fmath(ng, "MULTIPLY", h, 0.5, location=(-700, -80))
    ratio = fmath(ng, "DIVIDE", half_h.outputs[0], r, location=(-520, -80))
    scale = combine_xyz(ng, 1.0, 1.0, ratio.outputs[0], location=(-340, -80))
    xf = node(ng, "GeometryNodeTransform", location=(-160, 60))
    link(ng, s.outputs["Mesh"], xf.inputs["Geometry"])
    link(ng, scale.outputs[0], xf.inputs["Scale"])
    link(ng, combine_xyz(ng, 0.0, 0.0, half_h.outputs[0], location=(-340, -220)).outputs[0],
         xf.inputs["Translation"])
    _finish(ng, xf.outputs["Geometry"], gin, gout)


def build_rock(ng):
    _f(ng, "Size", 1.0, 0.02)
    new_input(ng, "Detail", "NodeSocketInt", default_value=2, min_value=0, max_value=5)
    rg = new_input(ng, "Roughness", "NodeSocketFloat", default_value=0.35, min_value=0.0, max_value=1.0)
    rg.subtype = "FACTOR"
    gin, gout = _io(ng)
    size = gin.outputs["Size"]
    ico = node(ng, "GeometryNodeMeshIcoSphere", location=(-900, 120))
    _inp(ng, ico.inputs["Radius"], size)
    _inp(ng, ico.inputs["Subdivisions"], gin.outputs["Detail"])
    # displace verts along normal by a noise field for an irregular boulder
    pos = node(ng, "GeometryNodeInputPosition", location=(-900, -120))
    noise = node(ng, "ShaderNodeTexNoise", location=(-720, -120))
    noise.inputs["Scale"].default_value = 1.8
    link(ng, pos.outputs[0], noise.inputs["Vector"])
    amt = fmath(ng, "SUBTRACT", noise.outputs["Fac"], 0.5, location=(-540, -120))
    rough = fmath(ng, "MULTIPLY", gin.outputs["Roughness"], size, location=(-540, -260))
    disp = fmath(ng, "MULTIPLY", amt.outputs[0], rough.outputs[0], location=(-360, -180))
    nrm = node(ng, "GeometryNodeInputNormal", location=(-540, -380))
    off = node(ng, "ShaderNodeVectorMath", operation="SCALE", location=(-200, -260))
    link(ng, nrm.outputs[0], off.inputs[0])
    link(ng, disp.outputs[0], off.inputs[3])
    setpos = node(ng, "GeometryNodeSetPosition", location=(20, 60))
    link(ng, ico.outputs["Mesh"], setpos.inputs["Geometry"])
    link(ng, off.outputs[0], setpos.inputs["Offset"])
    # flatten a touch and sit on the ground
    flat = node(ng, "GeometryNodeTransform", location=(220, 60))
    link(ng, setpos.outputs["Geometry"], flat.inputs["Geometry"])
    flat.inputs["Scale"].default_value = (1.0, 0.9, 0.7)
    up = fmath(ng, "MULTIPLY", size, 0.6, location=(220, -120))
    flat2 = _xform(ng, flat.outputs["Geometry"], 0.0, 0.0, up.outputs[0], base=(400, 60))
    _finish(ng, flat2, gin, gout, smooth=False)


def build_well(ng):
    _f(ng, "Radius", 1.0, 0.05)
    _f(ng, "Height", 1.0, 0.05)
    _f(ng, "Wall Thickness", 0.2, 0.02)
    gin, gout = _io(ng)
    r, h, wt = gin.outputs["Radius"], gin.outputs["Height"], gin.outputs["Wall Thickness"]
    half_h = fmath(ng, "MULTIPLY", h, 0.5, location=(-900, 200))
    outer = _cyl(ng, r, h, 24, tz=half_h.outputs[0], base=(-700, 200))
    inner_r = fmath(ng, "MAXIMUM", fmath(ng, "SUBTRACT", r, wt, location=(-900, -100)).outputs[0],
                    0.02, location=(-720, -100))
    taller = fmath(ng, "MULTIPLY", h, 1.2, location=(-900, -240))
    inner = _cyl(ng, inner_r.outputs[0], taller.outputs[0], 24, tz=half_h.outputs[0], base=(-540, -100))
    boolean = node(ng, "GeometryNodeMeshBoolean", location=(200, 80))
    boolean.operation = "DIFFERENCE"
    link(ng, outer, boolean.inputs["Mesh 1"])
    link(ng, inner, boolean.inputs["Mesh 2"])
    _finish(ng, boolean.outputs["Mesh"], gin, gout)


def build_bridge(ng):
    _f(ng, "Length", 6.0, 0.1)
    _f(ng, "Width", 3.0, 0.1)
    _f(ng, "Deck Thickness", 0.3, 0.02)
    _f(ng, "Pier Height", 2.0, 0.0)
    _f(ng, "Rail Height", 0.9, 0.0)
    gin, gout = _io(ng)
    L, W = gin.outputs["Length"], gin.outputs["Width"]
    dt, ph, rh = gin.outputs["Deck Thickness"], gin.outputs["Pier Height"], gin.outputs["Rail Height"]
    deck_z = fmath(ng, "ADD", ph, fmath(ng, "MULTIPLY", dt, 0.5, location=(-950, 240)).outputs[0],
                   location=(-780, 240))
    deck = _cube(ng, L, W, dt, tz=deck_z.outputs[0], base=(-600, 240))
    # piers at each end
    half_L = fmath(ng, "MULTIPLY", L, 0.5, location=(-950, 40))
    pier_x = fmath(ng, "SUBTRACT", half_L.outputs[0], 0.25, location=(-780, 40))
    neg_px = fmath(ng, "MULTIPLY", pier_x.outputs[0], -1.0, location=(-600, 40))
    half_ph = fmath(ng, "MULTIPLY", ph, 0.5, location=(-950, -80))
    pier_l = _cube(ng, 0.5, W, ph, tx=neg_px.outputs[0], tz=half_ph.outputs[0], base=(-440, -60))
    pier_r = _cube(ng, 0.5, W, ph, tx=pier_x.outputs[0], tz=half_ph.outputs[0], base=(-440, -200))
    # side rails
    rail_z = fmath(ng, "ADD", fmath(ng, "ADD", ph, dt, location=(-950, -320)).outputs[0],
                   fmath(ng, "MULTIPLY", rh, 0.5, location=(-950, -420)).outputs[0],
                   location=(-780, -360))
    rail_y = fmath(ng, "SUBTRACT", fmath(ng, "MULTIPLY", W, 0.5, location=(-950, -520)).outputs[0],
                   0.06, location=(-780, -520))
    neg_ry = fmath(ng, "MULTIPLY", rail_y.outputs[0], -1.0, location=(-600, -520))
    rail_l = _cube(ng, L, 0.12, rh, ty=rail_y.outputs[0], tz=rail_z.outputs[0], base=(-440, -360))
    rail_r = _cube(ng, L, 0.12, rh, ty=neg_ry.outputs[0], tz=rail_z.outputs[0], base=(-440, -500))
    _finish(ng, _join(ng, [deck, pier_l, pier_r, rail_l, rail_r], base=(300, 60)), gin, gout,
            smooth=False)


def build_tower(ng):
    _f(ng, "Radius", 1.2, 0.05)
    _f(ng, "Height", 4.0, 0.1)
    new_input(ng, "Sides", "NodeSocketInt", default_value=8, min_value=3, max_value=64)
    gin, gout = _io(ng)
    r, h, sides = gin.outputs["Radius"], gin.outputs["Height"], gin.outputs["Sides"]
    body = _cyl(ng, r, h, sides, tz=fmath(ng, "MULTIPLY", h, 0.5, location=(-900, 200)).outputs[0],
                base=(-700, 200))
    cap_r = fmath(ng, "MULTIPLY", r, 1.2, location=(-900, -80))
    cap_h = fmath(ng, "MULTIPLY", h, 0.12, location=(-900, -200))
    cap_z = fmath(ng, "SUBTRACT", h, fmath(ng, "MULTIPLY", cap_h.outputs[0], 0.5,
                  location=(-900, -320)).outputs[0], location=(-720, -260))
    cap = _cyl(ng, cap_r.outputs[0], cap_h.outputs[0], sides, tz=cap_z.outputs[0], base=(-540, -80))
    _finish(ng, _join(ng, [body, cap], base=(300, 60)), gin, gout)


def build_barrier(ng):
    _f(ng, "Length", 2.0, 0.05)
    _f(ng, "Height", 0.8, 0.05)
    _f(ng, "Base Width", 0.6, 0.02)
    _f(ng, "Top Width", 0.25, 0.02)
    gin, gout = _io(ng)
    L, H = gin.outputs["Length"], gin.outputs["Height"]
    bw, tw = gin.outputs["Base Width"], gin.outputs["Top Width"]
    size = combine_xyz(ng, L, bw, H, location=(-900, 160))
    cube = node(ng, "GeometryNodeMeshCube", location=(-720, 160))
    link(ng, size.outputs[0], cube.inputs["Size"])
    # taper the top (z>0) Y by Top/Base, then sit on the ground
    pos = node(ng, "GeometryNodeInputPosition", location=(-900, -120))
    sep = node(ng, "ShaderNodeSeparateXYZ", location=(-720, -120))
    link(ng, pos.outputs[0], sep.inputs[0])
    sel = fmath(ng, "GREATER_THAN", sep.outputs["Z"], 0.0, location=(-540, -80))
    ratio = fmath(ng, "DIVIDE", tw, bw, location=(-540, -220))
    new_y = fmath(ng, "MULTIPLY", sep.outputs["Y"], ratio.outputs[0], location=(-360, -180))
    newpos = combine_xyz(ng, sep.outputs["X"], new_y.outputs[0], sep.outputs["Z"], location=(-180, -120))
    setpos = node(ng, "GeometryNodeSetPosition", location=(20, 80))
    link(ng, cube.outputs["Mesh"], setpos.inputs["Geometry"])
    link(ng, sel.outputs[0], setpos.inputs["Selection"])
    link(ng, newpos.outputs[0], setpos.inputs["Position"])
    up = _xform(ng, setpos.outputs["Geometry"], 0.0, 0.0,
                fmath(ng, "MULTIPLY", H, 0.5, location=(220, -120)).outputs[0], base=(400, 80))
    _finish(ng, up, gin, gout, smooth=False)


def build_bench(ng):
    _f(ng, "Length", 1.8, 0.1)
    _f(ng, "Seat Height", 0.45, 0.05)
    _f(ng, "Depth", 0.5, 0.05)
    _f(ng, "Back Height", 0.5, 0.0)
    gin, gout = _io(ng)
    L, sh, d, bh = (gin.outputs["Length"], gin.outputs["Seat Height"],
                    gin.outputs["Depth"], gin.outputs["Back Height"])
    seat = _cube(ng, L, d, 0.08, tz=sh, base=(-700, 240))
    half_sh = fmath(ng, "MULTIPLY", sh, 0.5, location=(-950, 60))
    legx = fmath(ng, "SUBTRACT", fmath(ng, "MULTIPLY", L, 0.5, location=(-950, -40)).outputs[0],
                 0.1, location=(-780, -40))
    neg_lx = fmath(ng, "MULTIPLY", legx.outputs[0], -1.0, location=(-600, -40))
    leg_l = _cube(ng, 0.08, d, sh, tx=neg_lx.outputs[0], tz=half_sh.outputs[0], base=(-440, 60))
    leg_r = _cube(ng, 0.08, d, sh, tx=legx.outputs[0], tz=half_sh.outputs[0], base=(-440, -80))
    back_y = fmath(ng, "SUBTRACT", fmath(ng, "MULTIPLY", d, 0.5, location=(-950, -200)).outputs[0],
                   0.04, location=(-780, -200))
    neg_by = fmath(ng, "MULTIPLY", back_y.outputs[0], -1.0, location=(-600, -200))
    back_z = fmath(ng, "ADD", sh, fmath(ng, "MULTIPLY", bh, 0.5, location=(-950, -320)).outputs[0],
                   location=(-780, -320))
    back = _cube(ng, L, 0.06, bh, ty=neg_by.outputs[0], tz=back_z.outputs[0], base=(-440, -240))
    _finish(ng, _join(ng, [seat, leg_l, leg_r, back], base=(300, 60)), gin, gout, smooth=False)


def build_lamppost(ng):
    _f(ng, "Height", 3.5, 0.1)
    _f(ng, "Post Radius", 0.07, 0.005)
    _f(ng, "Lamp Size", 0.35, 0.02)
    gin, gout = _io(ng)
    h, pr, ls = gin.outputs["Height"], gin.outputs["Post Radius"], gin.outputs["Lamp Size"]
    post = _cyl(ng, pr, h, 12, tz=fmath(ng, "MULTIPLY", h, 0.5, location=(-900, 200)).outputs[0],
                base=(-700, 200))
    lamp = _cube(ng, ls, ls, ls, tz=fmath(ng, "ADD", h, fmath(ng, "MULTIPLY", ls, 0.4,
                 location=(-900, -160)).outputs[0], location=(-720, -160)).outputs[0], base=(-540, -120))
    _finish(ng, _join(ng, [post, lamp], base=(300, 60)), gin, gout)


def build_fountain(ng):
    _f(ng, "Radius", 1.6, 0.05)
    _f(ng, "Height", 0.8, 0.05)
    gin, gout = _io(ng)
    r, h = gin.outputs["Radius"], gin.outputs["Height"]
    h_base = fmath(ng, "MULTIPLY", h, 0.5, location=(-950, 220))
    base = _cyl(ng, r, h_base.outputs[0], 24,
                tz=fmath(ng, "MULTIPLY", h_base.outputs[0], 0.5, location=(-950, 120)).outputs[0],
                base=(-720, 220))
    r2 = fmath(ng, "MULTIPLY", r, 0.5, location=(-950, -40))
    tier_z = fmath(ng, "ADD", h_base.outputs[0],
                   fmath(ng, "MULTIPLY", h_base.outputs[0], 0.5, location=(-950, -140)).outputs[0],
                   location=(-780, -100))
    tier = _cyl(ng, r2.outputs[0], h_base.outputs[0], 20, tz=tier_z.outputs[0], base=(-600, -40))
    spout = _cyl(ng, fmath(ng, "MULTIPLY", r, 0.1, location=(-950, -280)).outputs[0], h, 10,
                 tz=fmath(ng, "ADD", h, fmath(ng, "MULTIPLY", h, 0.5, location=(-950, -380)).outputs[0],
                         location=(-780, -340)).outputs[0], base=(-600, -280))
    _finish(ng, _join(ng, [base, tier, spout], base=(300, 60)), gin, gout)


_BUILDERS = {
    TYPE_BUSH: build_bush, TYPE_ROCK: build_rock, TYPE_WELL: build_well,
    TYPE_BRIDGE: build_bridge, TYPE_TOWER: build_tower, TYPE_BARRIER: build_barrier,
    TYPE_BENCH: build_bench, TYPE_LAMPPOST: build_lamppost, TYPE_FOUNTAIN: build_fountain,
}


def _make(bb_type):
    return lambda: ensure_group(GROUP_NAMES[bb_type], _BUILDERS[bb_type], GN_VERSION)


ensure_bush = _make(TYPE_BUSH)
ensure_rock = _make(TYPE_ROCK)
ensure_well = _make(TYPE_WELL)
ensure_bridge = _make(TYPE_BRIDGE)
ensure_tower = _make(TYPE_TOWER)
ensure_barrier = _make(TYPE_BARRIER)
ensure_bench = _make(TYPE_BENCH)
ensure_lamppost = _make(TYPE_LAMPPOST)
ensure_fountain = _make(TYPE_FOUNTAIN)
