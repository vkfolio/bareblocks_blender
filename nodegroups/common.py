# BareBlocks - node-tree build helpers shared by every primitive builder.

import math

import bpy


# --------------------------------------------------------------------------- #
# Idempotent, versioned node-group creation
# --------------------------------------------------------------------------- #
def ensure_group(name, builder, version, tree_type="GeometryNodeTree"):
    """Return a node group built by `builder`, rebuilding in place on a version bump.

    Rebuilding in place (rather than creating a new datablock) means every modifier
    that already points at this group in an opened .blend upgrades automatically.
    Sockets must be appended in a stable order so their identifiers don't shift.
    """
    ng = bpy.data.node_groups.get(name)
    if ng is not None and ng.get("bb_version", -1) == version:
        return ng
    if ng is not None:
        ng.nodes.clear()
        ng.interface.clear()
    else:
        ng = bpy.data.node_groups.new(name, tree_type)
    builder(ng)
    ng["bb_version"] = version
    return ng


# --------------------------------------------------------------------------- #
# Tiny node/link/interface helpers
# --------------------------------------------------------------------------- #
def node(ng, idname, name=None, location=None, **props):
    n = ng.nodes.new(idname)
    if name:
        n.name = n.label = name
    if location:
        n.location = location
    for key, value in props.items():
        setattr(n, key, value)
    return n


def link(ng, from_socket, to_socket):
    ng.links.new(from_socket, to_socket)


def new_input(ng, name, socket_type, **attrs):
    sock = ng.interface.new_socket(name=name, in_out="INPUT", socket_type=socket_type)
    for key, value in attrs.items():
        setattr(sock, key, value)
    return sock


def new_output(ng, name, socket_type):
    return ng.interface.new_socket(name=name, in_out="OUTPUT", socket_type=socket_type)


def combine_xyz(ng, x, y, z, location=None):
    """Create a Combine XYZ node from three scalar sockets/values; return its node."""
    n = node(ng, "ShaderNodeCombineXYZ", location=location)
    for idx, val in enumerate((x, y, z)):
        if hasattr(val, "is_output"):  # it's a socket
            link(ng, val, n.inputs[idx])
        elif val is not None:
            n.inputs[idx].default_value = val
    return n


def vmath(ng, operation, a=None, b=None, location=None):
    n = node(ng, "ShaderNodeVectorMath", operation=operation, location=location)
    if a is not None:
        link(ng, a, n.inputs[0]) if hasattr(a, "is_output") else _set(n.inputs[0], a)
    if b is not None:
        link(ng, b, n.inputs[1]) if hasattr(b, "is_output") else _set(n.inputs[1], b)
    return n


def fmath(ng, operation, a=None, b=None, location=None):
    n = node(ng, "ShaderNodeMath", operation=operation, location=location)
    if a is not None:
        link(ng, a, n.inputs[0]) if hasattr(a, "is_output") else _set(n.inputs[0], a)
    if b is not None:
        link(ng, b, n.inputs[1]) if hasattr(b, "is_output") else _set(n.inputs[1], b)
    return n


def _set(socket, value):
    socket.default_value = value


# --------------------------------------------------------------------------- #
# Rounded-box subgraph (Geometry Nodes has no bevel node in 4.2/5.x).
#
# Builds, inside `ng`, a sharp Mesh Cube and a rounded version (convex hull of
# small spheres placed at the shrunken cube's corners), then a Switch picks
# between them based on `round_socket`. Returns the output Geometry socket.
# --------------------------------------------------------------------------- #
def add_rounded_box(ng, size_socket, round_socket, quality_socket=None,
                    radius_factor=0.06, base_x=-600.0, base_y=0.0):
    L = lambda dx, dy: (base_x + dx, base_y + dy)

    # Sharp cube.
    cube = node(ng, "GeometryNodeMeshCube", location=L(0, 200))
    link(ng, size_socket, cube.inputs["Size"])

    # Corner radius r = min(size_x, size_y, size_z) * factor.
    sep = node(ng, "ShaderNodeSeparateXYZ", location=L(0, -40))
    link(ng, size_socket, sep.inputs[0])
    min_xy = fmath(ng, "MINIMUM", sep.outputs["X"], sep.outputs["Y"], location=L(180, -40))
    min_xyz = fmath(ng, "MINIMUM", min_xy.outputs[0], sep.outputs["Z"], location=L(360, -40))
    r = fmath(ng, "MULTIPLY", min_xyz.outputs[0], radius_factor, location=L(540, -40))

    # Inner cube size = size - 2r (clamped to a small positive vector).
    two_r = fmath(ng, "MULTIPLY", r.outputs[0], 2.0, location=L(540, -200))
    two_r_vec = combine_xyz(ng, two_r.outputs[0], two_r.outputs[0], two_r.outputs[0],
                            location=L(720, -200))
    inner = vmath(ng, "SUBTRACT", size_socket, two_r_vec.outputs[0], location=L(900, -120))
    floor_vec = combine_xyz(ng, 0.002, 0.002, 0.002, location=L(900, -280))
    inner_clamped = vmath(ng, "MAXIMUM", inner.outputs[0], floor_vec.outputs[0],
                          location=L(1080, -120))

    inner_cube = node(ng, "GeometryNodeMeshCube", location=L(1260, -120))
    link(ng, inner_clamped.outputs[0], inner_cube.inputs["Size"])

    pts = node(ng, "GeometryNodeMeshToPoints", location=L(1440, -120))
    pts.mode = "VERTICES"
    link(ng, inner_cube.outputs["Mesh"], pts.inputs["Mesh"])

    sphere = node(ng, "GeometryNodeMeshUVSphere", location=L(1440, -320))
    link(ng, r.outputs[0], sphere.inputs["Radius"])
    if quality_socket is not None:
        link(ng, quality_socket, sphere.inputs["Segments"])
        link(ng, quality_socket, sphere.inputs["Rings"])
    else:
        sphere.inputs["Segments"].default_value = 8
        sphere.inputs["Rings"].default_value = 6

    iop = node(ng, "GeometryNodeInstanceOnPoints", location=L(1620, -120))
    link(ng, pts.outputs["Points"], iop.inputs["Points"])
    link(ng, sphere.outputs["Mesh"], iop.inputs["Instance"])

    realize = node(ng, "GeometryNodeRealizeInstances", location=L(1800, -120))
    link(ng, iop.outputs["Instances"], realize.inputs[0])

    hull = node(ng, "GeometryNodeConvexHull", location=L(1980, -120))
    link(ng, realize.outputs[0], hull.inputs[0])

    # Switch: sharp cube vs rounded hull.
    switch = node(ng, "GeometryNodeSwitch", location=L(2160, 80))
    switch.input_type = "GEOMETRY"
    link(ng, round_socket, switch.inputs["Switch"])
    link(ng, cube.outputs["Mesh"], switch.inputs["False"])
    link(ng, hull.outputs[0], switch.inputs["True"])

    # Smooth shading when rounded, flat when sharp.
    smooth = node(ng, "GeometryNodeSetShadeSmooth", location=L(2340, 80))
    link(ng, switch.outputs["Output"], smooth.inputs["Geometry"])
    link(ng, round_socket, smooth.inputs["Shade Smooth"])

    return smooth.outputs["Geometry"]


def sweep_rect_along(ng, spine_socket, width, height, off_x=0.0, off_y=0.0,
                     fill_caps=True, location=(0.0, 0.0)):
    """Sweep a solid rectangular bar (Width x Height cross-section) along `spine_socket`.

    The spine is expected to already have a Z-up normal so the rectangle's local +Y maps
    to world up and +X to the horizontal across-direction. `off_x` / `off_y` shift the
    cross-section within that plane (e.g. push a wall to the track edge, sit it on the
    ground). `Fill Caps` closes the two ends, so the result is a fully solid bar.

    `width`/`height`/`off_x`/`off_y` may be sockets or plain numbers. Returns the mesh
    output socket.
    """
    bx, by = location

    quad = node(ng, "GeometryNodeCurvePrimitiveQuadrilateral", location=(bx, by))
    quad.mode = "RECTANGLE"
    if hasattr(width, "is_output"):
        link(ng, width, quad.inputs["Width"])
    else:
        quad.inputs["Width"].default_value = width
    if hasattr(height, "is_output"):
        link(ng, height, quad.inputs["Height"])
    else:
        quad.inputs["Height"].default_value = height

    # Under a Z-up curve normal the profile's local +Y maps to world -Z, so negate the
    # vertical offset to make `off_y` an intuitive world-up shift (sit walls on the ground).
    if hasattr(off_y, "is_output"):
        off_y = fmath(ng, "MULTIPLY", off_y, -1.0, location=(bx - 180, by - 160)).outputs[0]
    else:
        off_y = -off_y
    off = combine_xyz(ng, off_x, off_y, 0.0, location=(bx, by - 160))
    xform = node(ng, "GeometryNodeTransform", location=(bx + 180, by))
    link(ng, quad.outputs[0], xform.inputs["Geometry"])
    link(ng, off.outputs[0], xform.inputs["Translation"])

    ctm = node(ng, "GeometryNodeCurveToMesh", location=(bx + 380, by + 120))
    link(ng, spine_socket, ctm.inputs["Curve"])
    link(ng, xform.outputs["Geometry"], ctm.inputs["Profile Curve"])
    ctm.inputs["Fill Caps"].default_value = bool(fill_caps)
    return ctm.outputs["Mesh"]


def store_grid_attributes(ng, geo_socket, base_x=2500.0, base_y=-500.0):
    """Bake local grid coordinates + normal so the material's grid stays locked to the
    block under move/rotate/scale.

    - "bb_grid_co" (POINT): local position * object scale -> rotates/moves with the
      block, fixed real cell size (scaling reveals more cells, never stretches).
    - "bb_grid_n" (FACE): local face normal -> triplanar weighting stays aligned to the
      block's faces even when the object is rotated.
    """
    L = lambda dx, dy: (base_x + dx, base_y + dy)

    self_obj = node(ng, "GeometryNodeSelfObject", location=L(0, 0))
    obj_info = node(ng, "GeometryNodeObjectInfo", location=L(180, 0))
    link(ng, self_obj.outputs[0], obj_info.inputs["Object"])

    pos = node(ng, "GeometryNodeInputPosition", location=L(0, -180))
    co = vmath(ng, "MULTIPLY", pos.outputs[0], obj_info.outputs["Scale"], location=L(380, -120))
    nrm = node(ng, "GeometryNodeInputNormal", location=L(0, -340))

    store_co = node(ng, "GeometryNodeStoreNamedAttribute", location=L(600, 80))
    store_co.data_type = "FLOAT_VECTOR"
    store_co.domain = "POINT"
    store_co.inputs["Name"].default_value = "bb_grid_co"
    link(ng, geo_socket, store_co.inputs["Geometry"])
    link(ng, co.outputs[0], store_co.inputs["Value"])

    store_n = node(ng, "GeometryNodeStoreNamedAttribute", location=L(820, 80))
    store_n.data_type = "FLOAT_VECTOR"
    store_n.domain = "FACE"
    store_n.inputs["Name"].default_value = "bb_grid_n"
    link(ng, store_co.outputs["Geometry"], store_n.inputs["Geometry"])
    link(ng, nrm.outputs[0], store_n.inputs["Value"])

    return store_n.outputs["Geometry"]


def shade_smooth_by_angle(ng, geo_socket, angle_deg=40.0, base_x=-200.0, base_y=-1000.0):
    """Smooth only faces meeting at a shallow angle; sharp edges (e.g. a 90 deg cap rim)
    stay flat. Avoids the lit-triangle-fan look on the flat top/bottom of round/curved
    pieces while still rounding their curved sides."""
    L = lambda dx, dy: (base_x + dx, base_y + dy)
    face = node(ng, "GeometryNodeSetShadeSmooth", location=L(0, 0))
    face.domain = "FACE"
    link(ng, geo_socket, face.inputs["Geometry"])
    face.inputs["Shade Smooth"].default_value = True

    ea = node(ng, "GeometryNodeInputMeshEdgeAngle", location=L(0, -180))
    soft = fmath(ng, "LESS_THAN", ea.outputs["Unsigned Angle"], math.radians(angle_deg),
                 location=L(200, -180))
    edge = node(ng, "GeometryNodeSetShadeSmooth", location=L(400, 0))
    edge.domain = "EDGE"
    link(ng, face.outputs["Geometry"], edge.inputs["Geometry"])
    link(ng, soft.outputs[0], edge.inputs["Shade Smooth"])
    return edge.outputs["Geometry"]


def named_attr(ng, name, data_type="FLOAT_VECTOR", location=None):
    n = node(ng, "GeometryNodeInputNamedAttribute", location=location)
    n.data_type = data_type
    n.inputs["Name"].default_value = name
    return n.outputs["Attribute"]


def store_named(ng, geo_socket, name, value, data_type="FLOAT_VECTOR", domain="POINT",
                location=None):
    n = node(ng, "GeometryNodeStoreNamedAttribute", location=location)
    n.data_type = data_type
    n.domain = domain
    n.inputs["Name"].default_value = name
    link(ng, geo_socket, n.inputs["Geometry"])
    if hasattr(value, "is_output"):
        link(ng, value, n.inputs["Value"])
    else:
        n.inputs["Value"].default_value = value
    return n.outputs["Geometry"]


def object_scale(ng, location=None):
    """The owning object's world scale (so baked grid coords scale with the object)."""
    so = node(ng, "GeometryNodeSelfObject", location=location)
    oi = node(ng, "GeometryNodeObjectInfo", location=location)
    link(ng, so.outputs[0], oi.inputs["Object"])
    return oi.outputs["Scale"]


def bake_spine_frame(ng, spine, base_x=-700.0, base_y=-900.0):
    """Store a moving frame on a curve so swept geometry can build a grid that FLOWS along
    it: bb_u = arc length, bb_t = tangent, bb_n = (Z-up) normal, bb_p = curve position.
    Curve to Mesh propagates these point attributes onto every swept vertex."""
    L = lambda dx, dy: (base_x + dx, base_y + dy)
    sp = node(ng, "GeometryNodeSplineParameter", location=L(0, 0))
    g = store_named(ng, spine, "bb_u", sp.outputs["Length"], "FLOAT", "POINT", location=L(200, 0))
    tan = node(ng, "GeometryNodeInputTangent", location=L(0, -120))
    g = store_named(ng, g, "bb_t", tan.outputs["Tangent"], "FLOAT_VECTOR", "POINT", location=L(380, 0))
    nor = node(ng, "GeometryNodeInputNormal", location=L(0, -240))
    g = store_named(ng, g, "bb_n", nor.outputs["Normal"], "FLOAT_VECTOR", "POINT", location=L(560, 0))
    pos = node(ng, "GeometryNodeInputPosition", location=L(0, -360))
    g = store_named(ng, g, "bb_p", pos.outputs[0], "FLOAT_VECTOR", "POINT", location=L(740, 0))
    return g


def store_flow_grid(ng, geo, base_x=900.0, base_y=-1100.0):
    """Build bb_grid_co = (arc length, lateral, up) and a local bb_grid_n from the frame
    baked by bake_spine_frame, so the material grid follows the curve through bends."""
    L = lambda dx, dy: (base_x + dx, base_y + dy)
    u = named_attr(ng, "bb_u", "FLOAT", location=L(0, 0))
    t = named_attr(ng, "bb_t", "FLOAT_VECTOR", location=L(0, -100))
    nrm = named_attr(ng, "bb_n", "FLOAT_VECTOR", location=L(0, -200))
    p = named_attr(ng, "bb_p", "FLOAT_VECTOR", location=L(0, -300))
    b = vmath(ng, "NORMALIZE", vmath(ng, "CROSS_PRODUCT", t, nrm, location=L(180, -150)).outputs[0],
              location=L(360, -150)).outputs[0]
    pos = node(ng, "GeometryNodeInputPosition", location=L(0, -420))
    rel = vmath(ng, "SUBTRACT", pos.outputs[0], p, location=L(200, -420)).outputs[0]
    w = vmath(ng, "DOT_PRODUCT", rel, b, location=L(400, -380)).outputs["Value"]
    z = vmath(ng, "DOT_PRODUCT", rel, nrm, location=L(400, -480)).outputs["Value"]
    co = combine_xyz(ng, u, w, z, location=L(600, -300))
    g1 = store_named(ng, geo, "bb_grid_co", co.outputs[0], "FLOAT_VECTOR", "POINT", location=L(800, 0))

    wn = node(ng, "GeometryNodeInputNormal", location=L(600, -620)).outputs["Normal"]
    nx = vmath(ng, "DOT_PRODUCT", wn, t, location=L(800, -560)).outputs["Value"]
    ny = vmath(ng, "DOT_PRODUCT", wn, b, location=L(800, -640)).outputs["Value"]
    nz = vmath(ng, "DOT_PRODUCT", wn, nrm, location=L(800, -720)).outputs["Value"]
    nloc = combine_xyz(ng, nx, ny, nz, location=L(980, -600))
    return store_named(ng, g1, "bb_grid_n", nloc.outputs[0], "FLOAT_VECTOR", "FACE", location=L(1160, 0))
