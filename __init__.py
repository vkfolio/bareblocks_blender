# BareBlocks - parametric blockout primitives for Blender (recreation of the
# Unreal "Blockout Tools" plugin). See blender_manifest.toml for extension metadata.

import bpy

from .core import props as props_mod
from .operators import add_primitives, material_ops, convert, align, bundles, ai_agent
from .ui import panels, menus, icons
from .gizmos import resize
from . import tool

# Modules that expose a `classes` list, registered after the core props/prefs.
_MODULES = [add_primitives, material_ops, convert, align, bundles, ai_agent,
            panels, menus, resize]


def register():
    icons.register()  # preview thumbnails, used by the palette/menu draw code
    for cls in props_mod.classes:
        bpy.utils.register_class(cls)
    props_mod.register_props()
    for module in _MODULES:
        for cls in module.classes:
            bpy.utils.register_class(cls)
    bundles.refresh_bundle_items()  # populate the import dropdown
    bpy.types.VIEW3D_MT_add.append(menus.menu_add)
    tool.register_tool()  # references the resize gizmo group, so register after it


def unregister():
    tool.unregister_tool()
    bpy.types.VIEW3D_MT_add.remove(menus.menu_add)
    for module in reversed(_MODULES):
        for cls in reversed(module.classes):
            bpy.utils.unregister_class(cls)
    props_mod.unregister_props()
    for cls in reversed(props_mod.classes):
        bpy.utils.unregister_class(cls)
    icons.unregister()
