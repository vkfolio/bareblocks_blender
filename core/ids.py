# BareBlocks - shared constants and the central block-type REGISTRY.
#
# Every block type is declared once in BLOCK_TYPES. Operators, the Add palette, menus,
# the edit panel and the gizmos are all generated from it, so adding a new type is just a
# new registry entry plus one Geometry-Nodes builder (registered in nodegroups/builders.py).
# The legacy LABELS / GROUP_NAMES / ... dicts are derived from the registry for callers
# that still look them up by name.

# Bump when any GN group / shader graph changes so existing .blend files rebuild.
GN_VERSION = 27

# Active-tool idname for the "BareBlocks mode" toolbar tool.
TOOL_IDNAME = "bareblocks.edit_tool"

# Modifier handle used on every primitive object (single, predictable lookup key).
MOD_NAME = "BareBlocks"

# Collection that holds all blockout primitives.
COLL_NAME = "Blockout"

# Shared material / shader node group names.
MATERIAL_NAME = "BareBlocks_Blockout"
SHADER_GROUP_NAME = "BB_BlockoutShader"

# Primitive type tags (stored on obj["bareblocks_type"]).
TYPE_BOX = "BOX"
TYPE_CORNER_RAMP = "CORNER_RAMP"
TYPE_CORNER_CURVED = "CORNER_CURVED"
TYPE_WINDOW = "WINDOW"
TYPE_TRACK = "TRACK"
TYPE_PLANE = "PLANE"
TYPE_CYLINDER = "CYLINDER"
TYPE_TUBE = "TUBE"
TYPE_SPHERE = "SPHERE"
TYPE_WALL = "WALL"
TYPE_FLOOR = "FLOOR"
TYPE_PILLAR = "PILLAR"
TYPE_SLEEVE = "SLEEVE"
TYPE_DOORWAY = "DOORWAY"
TYPE_STAIRS = "STAIRS"
TYPE_STAIRS_CURVED = "STAIRS_CURVED"
TYPE_RAILING = "RAILING"
TYPE_CONE = "CONE"
TYPE_ARCH = "ARCH"
TYPE_SIGN = "SIGN"
TYPE_BILLBOARD = "BILLBOARD"
# Environment kit
TYPE_TREE = "TREE"
TYPE_BUSH = "BUSH"
TYPE_ROCK = "ROCK"
TYPE_WELL = "WELL"
TYPE_BRIDGE = "BRIDGE"
TYPE_TOWER = "TOWER"
TYPE_BARRIER = "BARRIER"
TYPE_BENCH = "BENCH"
TYPE_LAMPPOST = "LAMPPOST"
TYPE_FOUNTAIN = "FOUNTAIN"
# Tree species (all share the BB_Tree generator; presets just set its inputs)
TYPE_PINE = "PINE"
TYPE_PALM = "PALM"
TYPE_OAK = "OAK"
TYPE_BIRCH = "BIRCH"
TYPE_WILLOW = "WILLOW"
TYPE_CYPRESS = "CYPRESS"
TYPE_ACACIA = "ACACIA"
TYPE_CHERRY = "CHERRY"
TYPE_BANYAN = "BANYAN"
TYPE_BAOBAB = "BAOBAB"
TYPE_BAMBOO = "BAMBOO"

# Display order of categories in the Add palette.
CATEGORY_ORDER = ["Primitives", "Structural", "Ramps & Corners", "Openings", "Stairs", "Path",
                  "Signage", "Nature", "Trees", "Structures", "Props"]

# Shared param layout for the Tree generator and all its species presets.
TREE_PARAMS = ["Height", "Trunk Height Frac", ["Trunk Radius", "Trunk Taper"],
               ["Trunk Count", "Trunk Spread"], "Canopy Shape", ["Canopy Width", "Canopy Height"],
               "Foliage Density", "Droop", "Seed"]

# Types centred on their origin (the agent must set z = height/2 to sit them on the ground).
# Everything else has its origin at its base and sits on z = 0.
CENTERED_TYPES = {
    TYPE_BOX, TYPE_FLOOR, TYPE_PILLAR, TYPE_PLANE, TYPE_CYLINDER, TYPE_TUBE, TYPE_SPHERE,
    TYPE_CONE, TYPE_SLEEVE, TYPE_CORNER_RAMP, TYPE_WINDOW, TYPE_DOORWAY, TYPE_ARCH,
}


def anchor(bb_type):
    return "centered" if bb_type in CENTERED_TYPES else "on-ground"


# --------------------------------------------------------------------------- #
# Helper handles sit on a face and drag one size parameter:
#   (socket_name, axis, sign, mode, anchored)
#     axis    : 0=X 1=Y 2=Z
#     sign    : +1 / -1 face along that axis
#     mode    : "centered" (full extent centered on origin) / "origin" (from origin)
#     anchored: if True, dragging keeps the opposite face fixed (Alt = symmetric)
# --------------------------------------------------------------------------- #
def _box_gizmos():
    return [
        ("Size X", 0, 1, "centered", True), ("Size X", 0, -1, "centered", True),
        ("Size Y", 1, 1, "centered", True), ("Size Y", 1, -1, "centered", True),
        ("Size Z", 2, 1, "centered", True), ("Size Z", 2, -1, "centered", True),
    ]


# --------------------------------------------------------------------------- #
# THE REGISTRY. Fields per type:
#   label    : UI name
#   category : palette section (must be in CATEGORY_ORDER)
#   icon     : thumbnail basename in icons/ (falls back to a stock icon if missing)
#   stock    : stock Blender icon used until a thumbnail exists
#   kind     : "MESH" or "CURVE" (curve = editable spline path)
#   group    : Geometry-Nodes group name (also the object base name)
#   params   : edit-panel layout - entries are a socket name or a list (one row)
#   gizmos   : list of resize-handle tuples (see above); [] = none
#   defaults : {socket: value} applied right after creation (presets reuse a shared group)
# --------------------------------------------------------------------------- #
BLOCK_TYPES = {
    TYPE_BOX: {
        "label": "Box", "category": "Primitives", "icon": "box", "stock": "MESH_CUBE",
        "kind": "MESH", "group": "BB_Box",
        "params": [["Size X", "Size Y", "Size Z"]],
        "gizmos": _box_gizmos(),
    },
    TYPE_CORNER_RAMP: {
        "label": "Ramp", "category": "Ramps & Corners", "icon": "ramp", "stock": "MOD_BEVEL",
        "kind": "MESH", "group": "BB_CornerRamp",
        "params": [["Size X", "Size Y", "Size Z"]],
        "gizmos": _box_gizmos(),
    },
    TYPE_CORNER_CURVED: {
        "label": "Corner Curved", "category": "Ramps & Corners", "icon": "corner_curved",
        "stock": "SPHERECURVE", "kind": "MESH", "group": "BB_CornerCurved",
        "params": ["Radius", "Height", "Quality", "Is Inner"],
        "gizmos": [("Radius", 0, 1, "origin", False), ("Height", 2, 1, "origin", False)],
    },
    TYPE_WINDOW: {
        "label": "Window", "category": "Openings", "icon": "window", "stock": "MOD_WIREFRAME",
        "kind": "MESH", "group": "BB_Window",
        "params": [["Size X", "Size Y", "Size Z"],
                   ["Top Thickness", "Bottom Thickness", "Side Thickness"]],
        "gizmos": [
            ("Size X", 0, 1, "centered", True), ("Size X", 0, -1, "centered", True),
            ("Size Z", 2, 1, "centered", True), ("Size Z", 2, -1, "centered", True),
        ],
    },
    TYPE_TRACK: {
        "label": "Track", "category": "Path", "icon": "track", "stock": "CURVE_PATH",
        "kind": "CURVE", "group": "BB_Track",
        "params": ["Width", ["Wall Height", "Wall Thickness"], "Floor Thickness", "Segment Length",
                   "Side Rails", ["Rail Height", "Rail Thickness", "Post Spacing"]],
        "gizmos": [("Width", 1, 1, "centered", True), ("Width", 1, -1, "centered", True),
                   ("Wall Height", 2, 1, "origin", False)],
    },

    # ----- Primitives -----
    TYPE_PLANE: {
        "label": "Plane", "category": "Primitives", "icon": "plane", "stock": "MESH_PLANE",
        "kind": "MESH", "group": "BB_Plane",
        "params": [["Size X", "Size Y"]],
        "gizmos": [
            ("Size X", 0, 1, "centered", True), ("Size X", 0, -1, "centered", True),
            ("Size Y", 1, 1, "centered", True), ("Size Y", 1, -1, "centered", True),
        ],
    },
    TYPE_CYLINDER: {
        "label": "Cylinder", "category": "Primitives", "icon": "cylinder", "stock": "MESH_CYLINDER",
        "kind": "MESH", "group": "BB_Cylinder",
        "params": ["Radius", "Height", "Sides"],
        "gizmos": [("Radius", 0, 1, "origin", False),
                   ("Height", 2, 1, "centered", True), ("Height", 2, -1, "centered", True)],
    },
    TYPE_TUBE: {
        "label": "Tube", "category": "Primitives", "icon": "tube", "stock": "MESH_CIRCLE",
        "kind": "MESH", "group": "BB_Tube",
        "params": ["Radius", "Height", "Wall Thickness", "Sides"],
        "gizmos": [("Radius", 0, 1, "origin", False),
                   ("Height", 2, 1, "centered", True), ("Height", 2, -1, "centered", True)],
    },
    TYPE_SPHERE: {
        "label": "Sphere", "category": "Primitives", "icon": "sphere", "stock": "MESH_UVSPHERE",
        "kind": "MESH", "group": "BB_Sphere",
        "params": ["Radius", "Quality", "Is Hemisphere"],
        "gizmos": [("Radius", 0, 1, "origin", False)],
    },
    TYPE_CONE: {
        "label": "Cone", "category": "Primitives", "icon": "cone", "stock": "MESH_CONE",
        "kind": "MESH", "group": "BB_Cone",
        "params": [["Bottom Radius", "Top Radius"], "Height", "Sides"],
        "gizmos": [("Bottom Radius", 0, 1, "origin", False),
                   ("Height", 2, 1, "centered", True), ("Height", 2, -1, "centered", True)],
    },

    # ----- Structural (Wall / Floor / Pillar reuse the Box group as presets) -----
    TYPE_WALL: {
        "label": "Wall", "category": "Structural", "icon": "wall", "stock": "MOD_BUILD",
        "kind": "CURVE", "group": "BB_Wall",
        "params": ["Height", "Thickness"],
        "gizmos": [("Height", 2, 1, "origin", False)],
    },
    TYPE_FLOOR: {
        "label": "Floor", "category": "Structural", "icon": "floor", "stock": "MESH_GRID",
        "kind": "MESH", "group": "BB_Box", "obj": "BB_Floor",
        "params": [["Size X", "Size Y", "Size Z"]], "gizmos": _box_gizmos(),
        "defaults": {"Size X": 4.0, "Size Y": 4.0, "Size Z": 0.3},
    },
    TYPE_PILLAR: {
        "label": "Pillar", "category": "Structural", "icon": "pillar", "stock": "MESH_CUBE",
        "kind": "MESH", "group": "BB_Box", "obj": "BB_Pillar",
        "params": [["Size X", "Size Y", "Size Z"]], "gizmos": _box_gizmos(),
        "defaults": {"Size X": 0.6, "Size Y": 0.6, "Size Z": 3.0},
    },
    TYPE_SLEEVE: {
        "label": "Sleeve", "category": "Structural", "icon": "sleeve", "stock": "MESH_CONE",
        "kind": "MESH", "group": "BB_Sleeve",
        "params": ["Length", ["Start Size", "End Size"], ["Skew Y", "Skew Z"]],
        "gizmos": [("Length", 0, 1, "centered", True), ("Length", 0, -1, "centered", True)],
    },

    # ----- Openings -----
    TYPE_DOORWAY: {
        "label": "Doorway", "category": "Openings", "icon": "doorway", "stock": "MOD_WIREFRAME",
        "kind": "MESH", "group": "BB_Doorway",
        "params": [["Size X", "Size Y", "Size Z"], ["Top Thickness", "Side Thickness"]],
        "gizmos": [
            ("Size X", 0, 1, "centered", True), ("Size X", 0, -1, "centered", True),
            ("Size Z", 2, 1, "centered", True), ("Size Z", 2, -1, "centered", True),
        ],
    },
    TYPE_ARCH: {
        "label": "Arch", "category": "Openings", "icon": "arch", "stock": "MOD_WARP",
        "kind": "MESH", "group": "BB_Arch",
        "params": [["Size X", "Size Y", "Size Z"], ["Top Thickness", "Side Thickness"], "Quality"],
        "gizmos": [
            ("Size X", 0, 1, "centered", True), ("Size X", 0, -1, "centered", True),
            ("Size Z", 2, 1, "centered", True), ("Size Z", 2, -1, "centered", True),
        ],
    },

    # ----- Stairs -----
    TYPE_STAIRS: {
        "label": "Stairs", "category": "Stairs", "icon": "stairs", "stock": "MOD_ARRAY",
        "kind": "MESH", "group": "BB_Stairs",
        "params": ["Steps", "Width", ["Step Height", "Step Depth"],
                   ["Fill Bottom", "Tread Thickness"],
                   "Side Rails", ["Rail Height", "Rail Thickness", "Post Spacing"]],
        "gizmos": [("Width", 1, 1, "centered", True), ("Width", 1, -1, "centered", True)],
    },
    TYPE_STAIRS_CURVED: {
        "label": "Stairs Curved", "category": "Stairs", "icon": "stairs_curved", "stock": "MOD_SCREW",
        "kind": "CURVE", "group": "BB_StairsCurved", "curve_default": "arc",
        "params": ["Steps", ["Step Width", "Step Height"],
                   ["Fill Bottom", "Tread Thickness"],
                   "Side Rails", ["Rail Height", "Rail Thickness", "Post Spacing"]],
        "gizmos": [],
    },

    # ----- Path (curve-based) -----
    TYPE_RAILING: {
        "label": "Railing", "category": "Path", "icon": "railing", "stock": "ALIGN_JUSTIFY",
        "kind": "CURVE", "group": "BB_Railing",
        "params": ["Height", "Post Spacing", ["Post Thickness", "Rail Thickness"]],
        "gizmos": [("Height", 2, 1, "origin", False)],
    },

    # ----- Signage / props -----
    TYPE_SIGN: {
        "label": "Sign", "category": "Signage", "icon": "sign", "stock": "EMPTY_SINGLE_ARROW",
        "kind": "MESH", "group": "BB_Sign",
        "params": ["Post Height", "Post Radius", ["Board Width", "Board Height"], "Board Thickness"],
        "gizmos": [("Post Height", 2, 1, "origin", False)],
    },
    TYPE_BILLBOARD: {
        "label": "Billboard", "category": "Signage", "icon": "billboard", "stock": "IMAGE_PLANE",
        "kind": "MESH", "group": "BB_Billboard",
        "params": [["Width", "Height"], "Leg Height", ["Post Thickness", "Board Thickness"]],
        "gizmos": [],
    },

    # ----- Trees -----
    TYPE_TREE: {
        "label": "Tree", "category": "Trees", "icon": "tree", "stock": "OUTLINER_OB_FORCE_FIELD",
        "kind": "MESH", "group": "BB_Tree", "params": TREE_PARAMS, "gizmos": [],
    },

    # ----- Nature -----
    TYPE_BUSH: {
        "label": "Bush", "category": "Nature", "icon": "bush", "stock": "MESH_UVSPHERE",
        "kind": "MESH", "group": "BB_Bush",
        "params": ["Radius", "Height"],
        "gizmos": [],
    },
    TYPE_ROCK: {
        "label": "Rock", "category": "Nature", "icon": "rock", "stock": "MESH_ICOSPHERE",
        "kind": "MESH", "group": "BB_Rock",
        "params": ["Size", "Detail", "Roughness"],
        "gizmos": [],
    },

    # ----- Structures -----
    TYPE_WELL: {
        "label": "Well", "category": "Structures", "icon": "well", "stock": "MESH_CYLINDER",
        "kind": "MESH", "group": "BB_Well",
        "params": ["Radius", "Height", "Wall Thickness"],
        "gizmos": [],
    },
    TYPE_BRIDGE: {
        "label": "Bridge", "category": "Structures", "icon": "bridge", "stock": "MOD_SIMPLEDEFORM",
        "kind": "MESH", "group": "BB_Bridge",
        "params": [["Length", "Width"], ["Deck Thickness", "Pier Height"], "Rail Height"],
        "gizmos": [],
    },
    TYPE_TOWER: {
        "label": "Tower", "category": "Structures", "icon": "tower", "stock": "MESH_CYLINDER",
        "kind": "MESH", "group": "BB_Tower",
        "params": ["Radius", "Height", "Sides"],
        "gizmos": [],
    },

    # ----- Props -----
    TYPE_BARRIER: {
        "label": "Barrier", "category": "Props", "icon": "barrier", "stock": "MOD_BEVEL",
        "kind": "MESH", "group": "BB_Barrier",
        "params": ["Length", "Height", ["Base Width", "Top Width"]],
        "gizmos": [],
    },
    TYPE_BENCH: {
        "label": "Bench", "category": "Props", "icon": "bench", "stock": "MESH_PLANE",
        "kind": "MESH", "group": "BB_Bench",
        "params": ["Length", "Seat Height", ["Depth", "Back Height"]],
        "gizmos": [],
    },
    TYPE_LAMPPOST: {
        "label": "Lamppost", "category": "Props", "icon": "lamppost", "stock": "LIGHT_POINT",
        "kind": "MESH", "group": "BB_Lamppost",
        "params": ["Height", "Post Radius", "Lamp Size"],
        "gizmos": [],
    },
    TYPE_FOUNTAIN: {
        "label": "Fountain", "category": "Props", "icon": "fountain", "stock": "MESH_CYLINDER",
        "kind": "MESH", "group": "BB_Fountain",
        "params": ["Radius", "Height"],
        "gizmos": [],
    },
}

# Tree species presets - all reuse the BB_Tree generator, differing only by default inputs.
# Canopy Shape: 0 Sphere  1 Cone  2 Column  3 Umbrella  4 Fronds  5 None
_TREE_SPECIES = {
    TYPE_PINE: ("Pine", {"Canopy Shape": 1, "Height": 12.0, "Trunk Height Frac": 0.15,
                         "Trunk Radius": 0.25, "Canopy Width": 4.0, "Canopy Height": 8.0}),
    TYPE_PALM: ("Palm", {"Canopy Shape": 4, "Height": 9.0, "Trunk Height Frac": 0.85,
                         "Trunk Radius": 0.22, "Trunk Taper": 0.8, "Canopy Width": 4.5,
                         "Canopy Height": 1.0, "Foliage Density": 3}),
    TYPE_OAK: ("Oak", {"Canopy Shape": 0, "Height": 9.0, "Trunk Height Frac": 0.3,
                       "Trunk Radius": 0.4, "Canopy Width": 8.0, "Canopy Height": 6.0}),
    TYPE_BIRCH: ("Birch", {"Canopy Shape": 0, "Height": 8.0, "Trunk Height Frac": 0.4,
                           "Trunk Radius": 0.16, "Canopy Width": 3.5, "Canopy Height": 4.5,
                           "Foliage Density": 1}),
    TYPE_WILLOW: ("Willow", {"Canopy Shape": 0, "Height": 7.0, "Trunk Height Frac": 0.2,
                             "Trunk Radius": 0.45, "Canopy Width": 7.0, "Canopy Height": 5.0,
                             "Droop": 0.8}),
    TYPE_CYPRESS: ("Cypress", {"Canopy Shape": 2, "Height": 9.0, "Trunk Height Frac": 0.05,
                               "Trunk Radius": 0.25, "Canopy Width": 2.0, "Canopy Height": 8.5}),
    TYPE_ACACIA: ("Acacia", {"Canopy Shape": 3, "Height": 7.0, "Trunk Height Frac": 0.55,
                             "Trunk Radius": 0.3, "Canopy Width": 9.0, "Canopy Height": 2.5}),
    TYPE_CHERRY: ("Cherry", {"Canopy Shape": 0, "Height": 5.0, "Trunk Height Frac": 0.25,
                             "Trunk Radius": 0.22, "Canopy Width": 5.0, "Canopy Height": 4.0}),
    TYPE_BANYAN: ("Banyan", {"Canopy Shape": 0, "Height": 10.0, "Trunk Height Frac": 0.15,
                             "Trunk Radius": 0.4, "Trunk Count": 7, "Trunk Spread": 3.0,
                             "Canopy Width": 14.0, "Canopy Height": 7.0}),
    TYPE_BAOBAB: ("Baobab", {"Canopy Shape": 0, "Height": 12.0, "Trunk Height Frac": 0.7,
                             "Trunk Radius": 1.2, "Trunk Taper": 0.4, "Canopy Width": 8.0,
                             "Canopy Height": 3.0, "Foliage Density": 1}),
    TYPE_BAMBOO: ("Bamboo", {"Canopy Shape": 5, "Height": 10.0, "Trunk Height Frac": 0.85,
                             "Trunk Radius": 0.08, "Trunk Count": 12, "Trunk Spread": 0.6}),
}
for _t, (_label, _defs) in _TREE_SPECIES.items():
    BLOCK_TYPES[_t] = {
        "label": _label, "category": "Trees", "icon": _label.lower(),
        "stock": "OUTLINER_OB_FORCE_FIELD", "kind": "MESH", "group": "BB_Tree",
        "obj": "BB_" + _label, "params": TREE_PARAMS, "gizmos": [], "defaults": _defs,
    }


def block(bb_type):
    return BLOCK_TYPES[bb_type]


def types_in_category(category):
    return [t for t, d in BLOCK_TYPES.items() if d["category"] == category]


def _defaults(bb_type):
    return BLOCK_TYPES[bb_type].get("defaults", {})


def _flatten_params(bb_type):
    """Flat list of every param socket name in a type's layout (rows expanded)."""
    names = []
    for entry in BLOCK_TYPES[bb_type]["params"]:
        names.extend(entry if isinstance(entry, (list, tuple)) else [entry])
    return names


# --------------------------------------------------------------------------- #
# Legacy lookups derived from the registry (kept for existing callers).
# --------------------------------------------------------------------------- #
LABELS = {t: d["label"] for t, d in BLOCK_TYPES.items()}
GROUP_NAMES = {t: d["group"] for t, d in BLOCK_TYPES.items()}
OBJECT_NAMES = {t: d.get("obj", d["group"]) for t, d in BLOCK_TYPES.items()}
CURVE_TYPES = {t for t, d in BLOCK_TYPES.items() if d["kind"] == "CURVE"}
PARAM_LAYOUT = {t: d["params"] for t, d in BLOCK_TYPES.items()}
GIZMO_HANDLES = {t: d["gizmos"] for t, d in BLOCK_TYPES.items() if d["gizmos"]}
# Dial (angle) gizmos per type: list of (angle-socket-name, spin-axis 0/1/2).
ANGLE_GIZMOS = {t: d["dials"] for t, d in BLOCK_TYPES.items() if d.get("dials")}


def has_gizmos(bb_type):
    return bb_type in GIZMO_HANDLES or bb_type in ANGLE_GIZMOS
