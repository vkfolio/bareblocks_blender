# BareBlocks - round primitives: Cylinder, Tube (hollow pipe), Sphere.

from .common import (ensure_group, node, link, new_input, new_output, combine_xyz, fmath,
                     store_grid_attributes, shade_smooth_by_angle)
from .shader_blockout import ensure_material
from ..core.ids import (GROUP_NAMES, TYPE_CYLINDER, TYPE_TUBE, TYPE_SPHERE, TYPE_CONE, GN_VERSION)


def _finish(ng, geo_socket, gin, gout, loc_x=900):
    geo = store_grid_attributes(ng, geo_socket)
    setmat = node(ng, "GeometryNodeSetMaterial", location=(loc_x, 80))
    link(ng, geo, setmat.inputs["Geometry"])
    link(ng, gin.outputs["Material"], setmat.inputs["Material"])
    link(ng, setmat.outputs["Geometry"], gout.inputs["Geometry"])


def build_cylinder(ng):
    r = new_input(ng, "Radius", "NodeSocketFloat", default_value=1.0, min_value=0.001)
    r.subtype = "DISTANCE"
    h = new_input(ng, "Height", "NodeSocketFloat", default_value=2.0, min_value=0.001)
    h.subtype = "DISTANCE"
    new_input(ng, "Sides", "NodeSocketInt", default_value=24, min_value=3, max_value=256)
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-700, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))

    cyl = node(ng, "GeometryNodeMeshCylinder", location=(-400, 0))
    link(ng, gin.outputs["Sides"], cyl.inputs["Vertices"])
    link(ng, gin.outputs["Radius"], cyl.inputs["Radius"])
    link(ng, gin.outputs["Height"], cyl.inputs["Depth"])

    smoothed = shade_smooth_by_angle(ng, cyl.outputs["Mesh"])
    _finish(ng, smoothed, gin, gout)


def build_tube(ng):
    r = new_input(ng, "Radius", "NodeSocketFloat", default_value=1.0, min_value=0.001)
    r.subtype = "DISTANCE"
    h = new_input(ng, "Height", "NodeSocketFloat", default_value=2.0, min_value=0.001)
    h.subtype = "DISTANCE"
    wt = new_input(ng, "Wall Thickness", "NodeSocketFloat", default_value=0.2, min_value=0.01)
    wt.subtype = "DISTANCE"
    new_input(ng, "Sides", "NodeSocketInt", default_value=24, min_value=3, max_value=256)
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-900, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))

    outer = node(ng, "GeometryNodeMeshCylinder", location=(-600, 120))
    link(ng, gin.outputs["Sides"], outer.inputs["Vertices"])
    link(ng, gin.outputs["Radius"], outer.inputs["Radius"])
    link(ng, gin.outputs["Height"], outer.inputs["Depth"])

    inner_r = fmath(ng, "SUBTRACT", gin.outputs["Radius"], gin.outputs["Wall Thickness"],
                    location=(-600, -160))
    inner_r_c = fmath(ng, "MAXIMUM", inner_r.outputs[0], 0.005, location=(-440, -160))
    tall = fmath(ng, "MULTIPLY", gin.outputs["Height"], 1.2, location=(-440, -300))
    inner = node(ng, "GeometryNodeMeshCylinder", location=(-260, -160))
    link(ng, gin.outputs["Sides"], inner.inputs["Vertices"])
    link(ng, inner_r_c.outputs[0], inner.inputs["Radius"])
    link(ng, tall.outputs[0], inner.inputs["Depth"])

    boolean = node(ng, "GeometryNodeMeshBoolean", location=(0, 60))
    boolean.operation = "DIFFERENCE"
    link(ng, outer.outputs["Mesh"], boolean.inputs["Mesh 1"])
    link(ng, inner.outputs["Mesh"], boolean.inputs["Mesh 2"])

    smoothed = shade_smooth_by_angle(ng, boolean.outputs["Mesh"])
    _finish(ng, smoothed, gin, gout)


def build_sphere(ng):
    r = new_input(ng, "Radius", "NodeSocketFloat", default_value=1.0, min_value=0.001)
    r.subtype = "DISTANCE"
    new_input(ng, "Quality", "NodeSocketInt", default_value=24, min_value=3, max_value=256)
    new_input(ng, "Is Hemisphere", "NodeSocketBool", default_value=False)
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-900, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))

    hq = fmath(ng, "DIVIDE", gin.outputs["Quality"], 2.0, location=(-880, -200))
    sphere = node(ng, "GeometryNodeMeshUVSphere", location=(-600, 120))
    link(ng, gin.outputs["Quality"], sphere.inputs["Segments"])
    link(ng, hq.outputs[0], sphere.inputs["Rings"])
    link(ng, gin.outputs["Radius"], sphere.inputs["Radius"])

    # Hemisphere: subtract a box that covers everything below z = 0.
    cut_size = node(ng, "ShaderNodeCombineXYZ", location=(-600, -120))
    big = fmath(ng, "MULTIPLY", gin.outputs["Radius"], 4.0, location=(-780, -120))
    link(ng, big.outputs[0], cut_size.inputs[0])
    link(ng, big.outputs[0], cut_size.inputs[1])
    twor = fmath(ng, "MULTIPLY", gin.outputs["Radius"], 2.0, location=(-780, -260))
    link(ng, twor.outputs[0], cut_size.inputs[2])
    cutter = node(ng, "GeometryNodeMeshCube", location=(-420, -120))
    link(ng, cut_size.outputs[0], cutter.inputs["Size"])
    negr = fmath(ng, "MULTIPLY", gin.outputs["Radius"], -1.0, location=(-420, -280))
    cut_off = combine_xyz(ng, 0.0, 0.0, negr.outputs[0], location=(-240, -280))
    cut_xform = node(ng, "GeometryNodeTransform", location=(-240, -120))
    link(ng, cutter.outputs["Mesh"], cut_xform.inputs["Geometry"])
    link(ng, cut_off.outputs[0], cut_xform.inputs["Translation"])
    hemi = node(ng, "GeometryNodeMeshBoolean", location=(-40, -40))
    hemi.operation = "DIFFERENCE"
    link(ng, sphere.outputs["Mesh"], hemi.inputs["Mesh 1"])
    link(ng, cut_xform.outputs["Geometry"], hemi.inputs["Mesh 2"])

    switch = node(ng, "GeometryNodeSwitch", location=(200, 80))
    switch.input_type = "GEOMETRY"
    link(ng, gin.outputs["Is Hemisphere"], switch.inputs["Switch"])
    link(ng, sphere.outputs["Mesh"], switch.inputs["False"])
    link(ng, hemi.outputs["Mesh"], switch.inputs["True"])

    smoothed = shade_smooth_by_angle(ng, switch.outputs["Output"])
    _finish(ng, smoothed, gin, gout)


def build_cone(ng):
    rb = new_input(ng, "Bottom Radius", "NodeSocketFloat", default_value=1.0, min_value=0.0)
    rb.subtype = "DISTANCE"
    rt = new_input(ng, "Top Radius", "NodeSocketFloat", default_value=0.4, min_value=0.0)
    rt.subtype = "DISTANCE"
    h = new_input(ng, "Height", "NodeSocketFloat", default_value=2.0, min_value=0.001)
    h.subtype = "DISTANCE"
    new_input(ng, "Sides", "NodeSocketInt", default_value=24, min_value=3, max_value=256)
    new_input(ng, "Material", "NodeSocketMaterial", default_value=ensure_material())
    new_output(ng, "Geometry", "NodeSocketGeometry")

    gin = node(ng, "NodeGroupInput", location=(-700, 0))
    gout = node(ng, "NodeGroupOutput", location=(1100, 0))

    cone = node(ng, "GeometryNodeMeshCone", location=(-400, 0))
    link(ng, gin.outputs["Sides"], cone.inputs["Vertices"])
    link(ng, gin.outputs["Bottom Radius"], cone.inputs["Radius Bottom"])
    link(ng, gin.outputs["Top Radius"], cone.inputs["Radius Top"])
    link(ng, gin.outputs["Height"], cone.inputs["Depth"])
    smoothed = shade_smooth_by_angle(ng, cone.outputs["Mesh"])
    _finish(ng, smoothed, gin, gout)


def ensure_cylinder():
    return ensure_group(GROUP_NAMES[TYPE_CYLINDER], build_cylinder, GN_VERSION)


def ensure_cone():
    return ensure_group(GROUP_NAMES[TYPE_CONE], build_cone, GN_VERSION)


def ensure_tube():
    return ensure_group(GROUP_NAMES[TYPE_TUBE], build_tube, GN_VERSION)


def ensure_sphere():
    return ensure_group(GROUP_NAMES[TYPE_SPHERE], build_sphere, GN_VERSION)
