# BareBlocks - the shared "Blockout" material: procedural grid + checker + top color.
#
# Coordinates default to OBJECT space, so the grid is locked to each block: it never
# swims when you move/rotate the block, and resizing via the GN params just reveals
# more/fewer cells (no stretching). Two line tiers (minor + bright major every N
# cells) act as a snapping reference, like Unreal's blockout grid.

import bpy

from .common import ensure_group, node, link, new_input, new_output, fmath, vmath, combine_xyz
from ..core.ids import SHADER_GROUP_NAME, MATERIAL_NAME, GN_VERSION

MINOR_HW = 0.018  # minor line half-width (fraction of a minor cell)
MAJOR_HW = 0.008  # major line half-width (fraction of a major cell; ~2x minor in world)
MINOR_WHITEN = 0.7
MAJOR_WHITEN = 0.95


def _connect(ng, value, socket):
    if value is None:
        return
    if hasattr(value, "is_output"):
        link(ng, value, socket)
    else:
        socket.default_value = value


def _mix(ng, data_type, fac, a, b, location=None):
    n = node(ng, "ShaderNodeMix", location=location)
    n.data_type = data_type
    _connect(ng, fac, n.inputs[0])
    if data_type == "FLOAT":
        ai, bi, oi = 2, 3, 0
    elif data_type == "VECTOR":
        ai, bi, oi = 4, 5, 1
    else:  # RGBA
        ai, bi, oi = 6, 7, 2
    _connect(ng, a, n.inputs[ai])
    _connect(ng, b, n.inputs[bi])
    return n.outputs[oi]


def build_blockout_shader(ng):
    new_input(ng, "Color", "NodeSocketColor", default_value=(0.16, 0.42, 0.85, 1.0))
    new_input(ng, "Use Grid", "NodeSocketBool", default_value=True)
    new_input(ng, "World Aligned", "NodeSocketBool", default_value=False)
    gs = new_input(ng, "Grid Size", "NodeSocketFloat", default_value=1.0, min_value=0.001)
    gs.subtype = "DISTANCE"
    me = new_input(ng, "Major Every", "NodeSocketInt", default_value=5, min_value=2, max_value=100)
    cl = new_input(ng, "Checker Luminance", "NodeSocketFloat", default_value=0.62,
                   min_value=0.0, max_value=1.0)
    cl.subtype = "FACTOR"
    rg = new_input(ng, "Roughness", "NodeSocketFloat", default_value=0.4,
                   min_value=0.0, max_value=1.0)
    rg.subtype = "FACTOR"
    new_input(ng, "Use Top Color", "NodeSocketBool", default_value=True)
    new_input(ng, "Top Color", "NodeSocketColor", default_value=(0.42, 0.42, 0.42, 1.0))
    new_output(ng, "BSDF", "NodeSocketShader")

    gin = node(ng, "NodeGroupInput", location=(-1600, 0))
    gout = node(ng, "NodeGroupOutput", location=(1700, 0))
    I = lambda name: gin.outputs[name]

    # --- coordinate & normal ---
    # Object-locked grid reads the GN-baked local coords (x object scale) and local
    # normal, so the grid rotates / moves / scales WITH the block and stays aligned to
    # its faces (no diagonal cross on rotation, no stretch on scale). World Aligned
    # switches to raw world position/normal.
    geo = node(ng, "ShaderNodeNewGeometry", location=(-1500, -460))
    attr_co = node(ng, "ShaderNodeAttribute", location=(-1500, -120))
    attr_co.attribute_type = "GEOMETRY"
    attr_co.attribute_name = "bb_grid_co"
    attr_n = node(ng, "ShaderNodeAttribute", location=(-1500, -300))
    attr_n.attribute_type = "GEOMETRY"
    attr_n.attribute_name = "bb_grid_n"
    coord = _mix(ng, "VECTOR", I("World Aligned"), attr_co.outputs["Vector"],
                 geo.outputs["Position"], location=(-1180, -120))
    nrm = _mix(ng, "VECTOR", I("World Aligned"), attr_n.outputs["Vector"],
               geo.outputs["Normal"], location=(-1180, -300))
    grid_vec = combine_xyz(ng, I("Grid Size"), I("Grid Size"), I("Grid Size"), location=(-1200, -320))
    P = vmath(ng, "DIVIDE", coord, grid_vec.outputs[0], location=(-1020, -140)).outputs[0]

    # --- per-face base hue: sides = Color, up-facing = Top Color ---
    # Use the object-locked normal so the top surface rotates WITH the block
    # (like a race-track top that stays attached when you turn the piece).
    rawn = node(ng, "ShaderNodeSeparateXYZ", location=(-900, 360))
    link(ng, nrm, rawn.inputs[0])
    topmask = fmath(ng, "GREATER_THAN", rawn.outputs["Z"], 0.85, location=(-720, 360))
    topgate = fmath(ng, "MULTIPLY", topmask.outputs[0], I("Use Top Color"), location=(-540, 360))
    cell_color = _mix(ng, "RGBA", topgate.outputs[0], I("Color"), I("Top Color"), location=(-360, 320))

    # --- checker tiles IN that hue, so the top keeps the checker + grid too ---
    chk = node(ng, "ShaderNodeTexChecker", location=(-620, 240))
    chk.inputs["Scale"].default_value = 1.0
    link(ng, P, chk.inputs["Vector"])
    dark = vmath(ng, "SCALE", cell_color, location=(-360, 100))
    link(ng, I("Checker Luminance"), dark.inputs[3])
    cell = _mix(ng, "RGBA", chk.outputs["Fac"], dark.outputs[0], cell_color, location=(-160, 200))

    # --- triplanar weights from the (object-locked or world) normal ---
    nabs = vmath(ng, "ABSOLUTE", nrm, location=(-820, -360))
    sn = node(ng, "ShaderNodeSeparateXYZ", location=(-640, -360))
    link(ng, nabs.outputs[0], sn.inputs[0])

    def line_mask(coord_socket, half_width, y):
        fr = vmath(ng, "FRACTION", coord_socket, location=(-420, y)).outputs[0]
        sf = node(ng, "ShaderNodeSeparateXYZ", location=(-240, y))
        link(ng, fr, sf.inputs[0])

        def axis(comp, weight, yy):
            inv = fmath(ng, "SUBTRACT", 1.0, comp, location=(-60, yy))
            dist = fmath(ng, "MINIMUM", comp, inv.outputs[0], location=(120, yy))
            near = fmath(ng, "LESS_THAN", dist.outputs[0], half_width, location=(300, yy))
            inplane = fmath(ng, "SUBTRACT", 1.0, weight, location=(300, yy - 60))
            return fmath(ng, "MULTIPLY", near.outputs[0], inplane.outputs[0],
                         location=(480, yy)).outputs[0]

        lx = axis(sf.outputs["X"], sn.outputs["X"], y)
        ly = axis(sf.outputs["Y"], sn.outputs["Y"], y - 140)
        lz = axis(sf.outputs["Z"], sn.outputs["Z"], y - 280)
        m1 = fmath(ng, "MAXIMUM", lx, ly, location=(660, y - 70))
        return fmath(ng, "MAXIMUM", m1.outputs[0], lz, location=(820, y - 70)).outputs[0]

    minor_mask = line_mask(P, MINOR_HW, -160)

    inv_major = fmath(ng, "DIVIDE", 1.0, I("Major Every"), location=(-1020, -520))
    major_node = node(ng, "ShaderNodeVectorMath", operation="SCALE", location=(-840, -520))
    link(ng, P, major_node.inputs[0])
    link(ng, inv_major.outputs[0], major_node.inputs[3])
    major_mask = line_mask(major_node.outputs[0], MAJOR_HW, -760)

    minor_on = fmath(ng, "MULTIPLY", minor_mask, I("Use Grid"), location=(1000, -160))
    major_on = fmath(ng, "MULTIPLY", major_mask, I("Use Grid"), location=(1000, -760))

    minor_col = _mix(ng, "RGBA", MINOR_WHITEN, cell, (1.0, 1.0, 1.0, 1.0), location=(1000, 40))
    major_col = _mix(ng, "RGBA", MAJOR_WHITEN, cell, (1.0, 1.0, 1.0, 1.0), location=(1000, -40))
    g1 = _mix(ng, "RGBA", minor_on.outputs[0], cell, minor_col, location=(1200, 80))
    final = _mix(ng, "RGBA", major_on.outputs[0], g1, major_col, location=(1380, 80))

    bsdf = node(ng, "ShaderNodeBsdfPrincipled", location=(1450, -160))
    link(ng, final, bsdf.inputs["Base Color"])
    link(ng, I("Roughness"), bsdf.inputs["Roughness"])
    link(ng, bsdf.outputs["BSDF"], gout.inputs["BSDF"])


def ensure_shader_group():
    return ensure_group(SHADER_GROUP_NAME, build_blockout_shader, GN_VERSION,
                        tree_type="ShaderNodeTree")


def ensure_material():
    group = ensure_shader_group()
    mat = bpy.data.materials.get(MATERIAL_NAME)
    if mat is not None and mat.get("bb_version", -1) == GN_VERSION:
        return mat
    if mat is None:
        mat = bpy.data.materials.new(MATERIAL_NAME)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    gnode = nt.nodes.new("ShaderNodeGroup")
    gnode.node_tree = group
    gnode.location = (0, 0)
    nt.links.new(gnode.outputs["BSDF"], out.inputs["Surface"])
    mat["bb_version"] = GN_VERSION
    return mat


def get_shader_group_node(mat):
    if not mat or not mat.use_nodes:
        return None
    for n in mat.node_tree.nodes:
        if n.type == "GROUP" and n.node_tree and n.node_tree.name == SHADER_GROUP_NAME:
            return n
    return None
