# BareBlocks - collection helpers (mirrors Bagapie's get_or_create_collection idea).

import bpy

from .ids import COLL_NAME


def ensure_collection(name=COLL_NAME, context=None):
    """Return the Blockout collection, creating + linking it to the scene if needed."""
    context = context or bpy.context
    scene_coll = context.scene.collection
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if name not in scene_coll.children:
        # Only link if not already somewhere in the scene tree.
        if not _in_scene_tree(scene_coll, coll):
            scene_coll.children.link(coll)
    return coll


def _in_scene_tree(parent, target):
    for child in parent.children:
        if child == target or _in_scene_tree(child, target):
            return True
    return False


def link_object(obj, coll=None):
    """Unlink obj from its current collections and link it into the Blockout collection."""
    coll = coll or ensure_collection()
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
