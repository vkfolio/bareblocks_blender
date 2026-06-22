# BareBlocks - maps each block type to the function that builds/returns its GN group.
#
# Kept separate from core.ids (which is pure data) so the registry can stay import-free;
# this module is the one place that imports every ng_* builder. Add a new type here when
# you add its node group. Wall / Floor / Pillar are presets that reuse the Box group.

from ..core.ids import (
    TYPE_BOX, TYPE_CORNER_RAMP, TYPE_CORNER_CURVED, TYPE_WINDOW, TYPE_TRACK,
    TYPE_PLANE, TYPE_CYLINDER, TYPE_TUBE, TYPE_SPHERE, TYPE_WALL, TYPE_FLOOR, TYPE_PILLAR,
    TYPE_SLEEVE, TYPE_DOORWAY, TYPE_STAIRS, TYPE_STAIRS_CURVED, TYPE_RAILING,
    TYPE_CONE, TYPE_ARCH, TYPE_SIGN, TYPE_BILLBOARD,
    TYPE_TREE, TYPE_BUSH, TYPE_ROCK, TYPE_WELL, TYPE_BRIDGE, TYPE_TOWER,
    TYPE_BARRIER, TYPE_BENCH, TYPE_LAMPPOST, TYPE_FOUNTAIN,
    TYPE_PINE, TYPE_PALM, TYPE_OAK, TYPE_BIRCH, TYPE_WILLOW, TYPE_CYPRESS,
    TYPE_ACACIA, TYPE_CHERRY, TYPE_BANYAN, TYPE_BAOBAB, TYPE_BAMBOO,
)
from . import ng_kit
from .ng_tree import ensure_tree
from .ng_box import ensure_box
from .ng_corner_ramp import ensure_corner_ramp
from .ng_corner_curved import ensure_corner_curved
from .ng_window import ensure_window
from .ng_track import ensure_track
from .ng_round import ensure_cylinder, ensure_tube, ensure_sphere, ensure_cone
from .ng_simple import ensure_plane, ensure_sleeve
from .ng_doorway import ensure_doorway
from .ng_stairs import ensure_stairs, ensure_stairs_curved
from .ng_railing import ensure_railing
from .ng_wall import ensure_wall
from .ng_arch import ensure_arch
from .ng_signage import ensure_sign, ensure_billboard

ENSURE = {
    TYPE_BOX: ensure_box,
    TYPE_CORNER_RAMP: ensure_corner_ramp,
    TYPE_CORNER_CURVED: ensure_corner_curved,
    TYPE_WINDOW: ensure_window,
    TYPE_TRACK: ensure_track,
    TYPE_PLANE: ensure_plane,
    TYPE_CYLINDER: ensure_cylinder,
    TYPE_TUBE: ensure_tube,
    TYPE_SPHERE: ensure_sphere,
    TYPE_WALL: ensure_wall,   # spline-based wall slab
    TYPE_FLOOR: ensure_box,   # preset: Box group, floor-sized defaults
    TYPE_PILLAR: ensure_box,  # preset: Box group, column-sized defaults
    TYPE_SLEEVE: ensure_sleeve,
    TYPE_DOORWAY: ensure_doorway,
    TYPE_STAIRS: ensure_stairs,
    TYPE_STAIRS_CURVED: ensure_stairs_curved,
    TYPE_RAILING: ensure_railing,
    TYPE_CONE: ensure_cone,
    TYPE_ARCH: ensure_arch,
    TYPE_SIGN: ensure_sign,
    TYPE_BILLBOARD: ensure_billboard,
    TYPE_TREE: ensure_tree,
    TYPE_BUSH: ng_kit.ensure_bush,
    TYPE_ROCK: ng_kit.ensure_rock,
    TYPE_WELL: ng_kit.ensure_well,
    TYPE_BRIDGE: ng_kit.ensure_bridge,
    TYPE_TOWER: ng_kit.ensure_tower,
    TYPE_BARRIER: ng_kit.ensure_barrier,
    TYPE_BENCH: ng_kit.ensure_bench,
    TYPE_LAMPPOST: ng_kit.ensure_lamppost,
    TYPE_FOUNTAIN: ng_kit.ensure_fountain,
    # all tree species share the one BB_Tree generator (presets set its inputs)
    TYPE_PINE: ensure_tree, TYPE_PALM: ensure_tree, TYPE_OAK: ensure_tree, TYPE_BIRCH: ensure_tree,
    TYPE_WILLOW: ensure_tree, TYPE_CYPRESS: ensure_tree, TYPE_ACACIA: ensure_tree,
    TYPE_CHERRY: ensure_tree, TYPE_BANYAN: ensure_tree, TYPE_BAOBAB: ensure_tree,
    TYPE_BAMBOO: ensure_tree,
}


def ensure_group_for(bb_type):
    return ENSURE[bb_type]()
