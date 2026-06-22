# BareBlocks - the tool layer the AI agent calls. Pure bpy operations (run on the main
# thread), plus the OpenAI tool/function schemas + system prompt auto-generated from the
# block registry, so new block types become available to the agent for free.

import json

import bpy
from mathutils import Vector

from ..core.ids import BLOCK_TYPES, _flatten_params, anchor
from ..core.sockets import set_mod, mod_value, is_bareblocks
from ..nodegroups.shader_blockout import get_shader_group_node
from .add_primitives import create_primitive


# --------------------------------------------------------------------------- #
# Type lookup (accept key OR label, case-insensitive) and the prompt catalog
# --------------------------------------------------------------------------- #
def _resolve_type(name):
    if name in BLOCK_TYPES:
        return name
    n = str(name).strip().lower()
    for key, spec in BLOCK_TYPES.items():
        if key.lower() == n or spec["label"].lower() == n:
            return key
    return None


def type_catalog():
    lines = []
    for key, spec in BLOCK_TYPES.items():
        kind = "path-curve, bend with shape_path" if spec["kind"] == "CURVE" else "mesh"
        params = ", ".join(_flatten_params(key)) or "(none)"
        lines.append(f"- {key} ({spec['label']}, {kind}, {anchor(key)}): {params}")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are BareBlocks Architect, an assistant that builds greybox / blockout \
3D environments inside Blender using the BareBlocks add-on, by calling tools.

BASE RULES
- Units are metres. +Z is up, +X right, +Y forward. The ground is the z = 0 plane.
- Anchoring: a type marked [centered] is centred on its origin, so to set it ON the ground \
give its location a z of half its height (e.g. a 2 m Box -> z = 1). A type marked [on-ground] \
already sits on z = 0 (use z = 0). Never leave solid pieces floating or sunk unless intended.
- Use a believable human scale: wall ~3 m tall, doorway ~2.5 m, tree ~5 m, lamppost ~3.5 m.
- Avoid unwanted overlaps and leave sensible spacing; lay out pieces so they read clearly.
- For many repeats (rows of trees, fences, lamps) space them evenly along a line or grid.

TOOLS
- add_block(type, location, params): create a piece. `params` maps a parameter name to a value.
- shape_path(name, points): bend a path-curve type (Track, Wall, Railing, Stairs Curved) \
through a list of [x,y,z] world points (e.g. a race-track loop or an L-shaped wall).
- list_blocks() before editing to learn object names, then edit_block / move_block / set_color \
/ delete_block.

Work step by step. Briefly say what you're doing as you go. When the scene matches the \
request, stop and give a one-line summary.

Block types  (KEY (Label, kind, anchor): parameters):
{catalog}
"""


def system_prompt():
    return SYSTEM_PROMPT.format(catalog=type_catalog())


# --------------------------------------------------------------------------- #
# OpenAI tool (function) schemas
# --------------------------------------------------------------------------- #
def tool_specs():
    keys = list(BLOCK_TYPES.keys())
    vec3 = {"type": "array", "items": {"type": "number"}, "description": "[x, y, z] in metres"}
    params_obj = {"type": "object",
                  "description": "parameter name -> number/bool value for this block type"}

    def fn(name, desc, props, required):
        return {"type": "function", "function": {
            "name": name, "description": desc,
            "parameters": {"type": "object", "properties": props, "required": required}}}

    return [
        fn("add_block", "Create a blockout primitive of the given type.",
           {"type": {"type": "string", "enum": keys, "description": "block type key"},
            "location": vec3, "params": params_obj}, ["type"]),
        fn("edit_block", "Change parameters (and optionally location) of an existing block.",
           {"name": {"type": "string"}, "params": params_obj, "location": vec3}, ["name"]),
        fn("move_block", "Move a block to a new location.",
           {"name": {"type": "string"}, "location": vec3}, ["name", "location"]),
        fn("set_color", "Set a block's blockout colour (0-1 RGB).",
           {"name": {"type": "string"},
            "color": {"type": "array", "items": {"type": "number"},
                      "description": "[r, g, b] 0-1"}}, ["name", "color"]),
        fn("shape_path", "Bend a curve/path block (Track, Wall, Railing, Stairs Curved) "
           "through a list of world points.",
           {"name": {"type": "string"},
            "points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}},
                       "description": "list of [x,y,z] world points"},
            "smooth": {"type": "boolean", "description": "smooth curve (default) vs sharp angles"}},
           ["name", "points"]),
        fn("delete_block", "Delete a block by name.", {"name": {"type": "string"}}, ["name"]),
        fn("list_blocks", "List all blockout objects with their type, location and parameters.",
           {}, []),
    ]


# --------------------------------------------------------------------------- #
# Tool execution (main thread)
# --------------------------------------------------------------------------- #
def _find(name):
    obj = bpy.data.objects.get(name)
    if obj is None or not is_bareblocks(obj):
        return None
    return obj


def _apply_params(obj, params):
    applied, skipped = [], []
    for sock, val in (params or {}).items():
        try:
            set_mod(obj, sock, val)
            applied.append(sock)
        except Exception:
            skipped.append(sock)
    return applied, skipped


def _set_loc(obj, location):
    if location and len(location) == 3:
        obj.location = Vector(location)


def _block_info(obj):
    info = {"name": obj.name, "type": obj.get("bareblocks_type"),
            "location": [round(c, 3) for c in obj.location]}
    vals = {}
    for p in _flatten_params(obj["bareblocks_type"]):
        try:
            v = mod_value(obj, p)
            vals[p] = round(v, 3) if isinstance(v, float) else v
        except Exception:
            pass
    info["params"] = vals
    return info


def _shape_path(obj, points, smooth=True):
    if obj.type != "CURVE":
        return f"{obj.name} is not a path/curve type"
    loc = obj.location
    cu = obj.data
    cu.splines.clear()
    if smooth:
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(points) - 1)
        for bp, p in zip(sp.bezier_points, points):
            bp.co = (p[0] - loc.x, p[1] - loc.y, p[2] - loc.z)
            bp.handle_left_type = bp.handle_right_type = "AUTO"
    else:
        sp = cu.splines.new("POLY")
        sp.points.add(len(points) - 1)
        for pt, p in zip(sp.points, points):
            pt.co = (p[0] - loc.x, p[1] - loc.y, p[2] - loc.z, 1.0)
    obj.update_tag()
    return f"shaped {obj.name} through {len(points)} points"


def execute_tool(context, name, args):
    if name == "add_block":
        key = _resolve_type(args.get("type", ""))
        if key is None:
            return f"ERROR: unknown type '{args.get('type')}'"
        obj = create_primitive(context, key)
        _set_loc(obj, args.get("location"))
        applied, skipped = _apply_params(obj, args.get("params"))
        msg = f"added {obj.name} ({key}) at {[round(c,2) for c in obj.location]}"
        if skipped:
            msg += f"; ignored unknown params: {skipped}"
        return msg

    if name == "edit_block":
        obj = _find(args.get("name", ""))
        if obj is None:
            return f"ERROR: no block named '{args.get('name')}'"
        _set_loc(obj, args.get("location"))
        applied, skipped = _apply_params(obj, args.get("params"))
        return f"edited {obj.name}: set {applied}" + (f"; ignored {skipped}" if skipped else "")

    if name == "move_block":
        obj = _find(args.get("name", ""))
        if obj is None:
            return f"ERROR: no block named '{args.get('name')}'"
        _set_loc(obj, args.get("location"))
        return f"moved {obj.name} to {[round(c,2) for c in obj.location]}"

    if name == "set_color":
        obj = _find(args.get("name", ""))
        if obj is None:
            return f"ERROR: no block named '{args.get('name')}'"
        col = args.get("color") or [0.8, 0.8, 0.8]
        mat = mod_value(obj, "Material")
        gn = get_shader_group_node(mat) if mat else None
        if gn is None:
            return f"ERROR: {obj.name} has no blockout material"
        gn.inputs["Color"].default_value = (col[0], col[1], col[2], 1.0)
        return f"coloured {obj.name}"

    if name == "shape_path":
        obj = _find(args.get("name", ""))
        if obj is None:
            return f"ERROR: no block named '{args.get('name')}'"
        pts = args.get("points") or []
        if len(pts) < 2:
            return "ERROR: need at least 2 points"
        return _shape_path(obj, pts, args.get("smooth", True))

    if name == "delete_block":
        obj = _find(args.get("name", ""))
        if obj is None:
            return f"ERROR: no block named '{args.get('name')}'"
        nm = obj.name
        bpy.data.objects.remove(obj, do_unlink=True)
        return f"deleted {nm}"

    if name == "list_blocks":
        blocks = [_block_info(o) for o in bpy.data.objects if is_bareblocks(o)]
        return json.dumps(blocks) if blocks else "no blockout objects yet"

    return f"ERROR: unknown tool '{name}'"
