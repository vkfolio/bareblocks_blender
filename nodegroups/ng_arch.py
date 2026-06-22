# BareBlocks - Arch primitive (wall with an arched, floor-to-crown opening).
#
# Like the Doorway, but the top of the opening is a semicircle. The cutter is a rectangle
# (lower straight part) unioned with a horizontal cylinder (the arch), then subtracted from
# the wall. The cutter overshoots below the floor so the boolean cuts cleanly.

import math

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     store_grid_attributes, shade_smooth_by_angle)
from .shader_blockout import ensure_material
from ..core.ids import GROUP_NAMES, TYPE_ARCH, GN_VERSION


def build_arch(ng):
    for axis, default in (("X", 3.0), ("Y", 0.4), ("Z", 3.5)):
        s = new_input(ng, f"Size {axis}", "NodeSocketFloat", default_value=default, min_value=0.001)
        s.subtype = "DISTANCE"
    top = new_input(ng, "Top Thickness", "NodeSocketFloat", default_value=0.5, min_value=0.0)
    top.subtype = "DISTANCE"
    side = new_input(ng, "Side Thickness", "NodeSocketFloat", default_value=0.6, min_value=0.0)
    side.subtype = "DISTANCE"
    new_input(ng, "Quality", "NodeSocketInt", default_value=24, min_value=4, max_value=256)
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-1500, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))
    sx, sy, sz = gin.outputs["Size X"], gin.outputs["Size Y"], gin.outputs["Size Z"]
    topt, sidet = gin.outputs["Top Thickness"], gin.outputs["Side Thickness"]
    margin = 0.2

    outer_vec = combine_xyz(ng, sx, sy, sz, location=(-1300, 220))
    outer = node(ng, "GeometryNodeMeshCube", location=(-1120, 220))
    link(ng, outer_vec.outputs[0], outer.inputs["Size"])

    # Opening width, arch radius, crown (top of arch) and spring (arch base) heights.
    two_side = fmath(ng, "MULTIPLY", sidet, 2.0, location=(-1300, -40))
    open_w = fmath(ng, "MAXIMUM", fmath(ng, "SUBTRACT", sx, two_side.outputs[0],
                   location=(-1120, -40)).outputs[0], 0.02, location=(-960, -40))
    # Slightly wider than half the opening so the rectangle's top corners fall INSIDE the
    # arch circle (not exactly on it) - an exact tangency degenerates the boolean.
    arch_r = fmath(ng, "MULTIPLY", open_w.outputs[0], 0.52, location=(-800, -40))
    half_z = fmath(ng, "MULTIPLY", sz, 0.5, location=(-1300, -160))
    crown = fmath(ng, "SUBTRACT", half_z.outputs[0], topt, location=(-1120, -160))      # local z of crown
    spring = fmath(ng, "SUBTRACT", crown.outputs[0], arch_r.outputs[0], location=(-960, -160))
    floor = fmath(ng, "MULTIPLY", sz, -0.5, location=(-1300, -300))
    floor_m = fmath(ng, "SUBTRACT", floor.outputs[0], margin, location=(-1120, -300))    # below floor

    deep = fmath(ng, "MULTIPLY", sy, 2.0, location=(-1300, -440))

    # Rectangle (straight lower part): from floor_m up to spring.
    rect_h = fmath(ng, "SUBTRACT", spring.outputs[0], floor_m.outputs[0], location=(-780, -300))
    rect_cz = fmath(ng, "MULTIPLY", fmath(ng, "ADD", spring.outputs[0], floor_m.outputs[0],
                    location=(-620, -300)).outputs[0], 0.5, location=(-460, -300))
    rect_vec = combine_xyz(ng, open_w.outputs[0], deep.outputs[0], rect_h.outputs[0],
                           location=(-300, -260))
    rect = node(ng, "GeometryNodeMeshCube", location=(-120, -260))
    link(ng, rect_vec.outputs[0], rect.inputs["Size"])
    rect_off = combine_xyz(ng, 0.0, 0.0, rect_cz.outputs[0], location=(-120, -420))
    rect_x = node(ng, "GeometryNodeTransform", location=(60, -260))
    link(ng, rect.outputs["Mesh"], rect_x.inputs["Geometry"])
    link(ng, rect_off.outputs[0], rect_x.inputs["Translation"])

    # Arch (semicircle): a cylinder with its axis along Y, centred at the spring line.
    arch_cyl = node(ng, "GeometryNodeMeshCylinder", location=(-300, 120))
    link(ng, gin.outputs["Quality"], arch_cyl.inputs["Vertices"])
    link(ng, arch_r.outputs[0], arch_cyl.inputs["Radius"])
    link(ng, deep.outputs[0], arch_cyl.inputs["Depth"])
    arch_off = combine_xyz(ng, 0.0, 0.0, spring.outputs[0], location=(-120, 40))
    arch_x = node(ng, "GeometryNodeTransform", location=(60, 120))
    link(ng, arch_cyl.outputs["Mesh"], arch_x.inputs["Geometry"])
    arch_x.inputs["Rotation"].default_value = (math.radians(90.0), 0.0, 0.0)
    link(ng, arch_off.outputs[0], arch_x.inputs["Translation"])

    # Single difference subtracting BOTH cutters at once (Mesh 2 is multi-input → it unions
    # the rectangle + arch cylinder internally and cuts in one clean pass).
    boolean = node(ng, "GeometryNodeMeshBoolean", location=(360, 160))
    boolean.operation = "DIFFERENCE"
    link(ng, outer.outputs["Mesh"], boolean.inputs["Mesh 1"])
    link(ng, rect_x.outputs["Geometry"], boolean.inputs["Mesh 2"])
    link(ng, arch_x.outputs["Geometry"], boolean.inputs["Mesh 2"])

    smoothed = shade_smooth_by_angle(ng, boolean.outputs["Mesh"], base_x=560.0, base_y=-700.0)
    geo = store_grid_attributes(ng, smoothed)
    setmat = node(ng, "GeometryNodeSetMaterial", location=(900, 160))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def ensure_arch():
    return ensure_group(GROUP_NAMES[TYPE_ARCH], build_arch, GN_VERSION)
