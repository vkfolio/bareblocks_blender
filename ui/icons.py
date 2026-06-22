# BareBlocks - custom thumbnail icons for the Add palette.
#
# Loads every PNG in bareblocks/icons/ into a preview collection on register. The Add
# palette uses icon_id(name) and falls back to a stock Blender icon when a thumbnail is
# missing, so the UI works whether or not the thumbnails have been rendered yet.

import os
import bpy.utils.previews

_pcoll = None


def _icons_dir():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")


def icon_id(name):
    """Preview icon_id for `name`, or 0 (no icon) if it isn't loaded."""
    if _pcoll is not None and name in _pcoll:
        return _pcoll[name].icon_id
    return 0


def register():
    global _pcoll
    _pcoll = bpy.utils.previews.new()
    d = _icons_dir()
    if os.path.isdir(d):
        for fname in sorted(os.listdir(d)):
            if fname.lower().endswith(".png"):
                try:
                    _pcoll.load(fname[:-4], os.path.join(d, fname), "IMAGE")
                except Exception:
                    pass


def unregister():
    global _pcoll
    if _pcoll is not None:
        bpy.utils.previews.remove(_pcoll)
        _pcoll = None
