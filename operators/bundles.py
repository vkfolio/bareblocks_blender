# BareBlocks - save/load reusable "bundles" (prefab collections of blocks) and register
# the bundle folder as a native Asset Library for drag-drop from the Asset Browser.
#
# A bundle is just a .blend holding the selected objects (marked as assets too). Save the
# selection, import it later into any scene, or browse the folder as an asset library.

import os
import bpy

from ..core.collections import ensure_collection
from ..core.props import get_prefs, _bundle_items_cache

ASSET_LIB_NAME = "BareBlocks Bundles"


def get_bundle_dir():
    prefs = get_prefs()
    if prefs and prefs.bundle_dir:
        d = bpy.path.abspath(prefs.bundle_dir)
    else:
        d = bpy.utils.user_resource("DATAFILES", path="bareblocks_bundles", create=True)
    os.makedirs(d, exist_ok=True)
    return d


def refresh_bundle_items():
    """Rebuild the cached (file, label, desc) list backing the import EnumProperty."""
    items = []
    try:
        for f in sorted(os.listdir(get_bundle_dir())):
            if f.lower().endswith(".blend"):
                items.append((f, f[:-6], "Import this bundle"))
    except Exception:
        pass
    _bundle_items_cache[:] = items or [("", "(no bundles)", "")]


class BAREBLOCKS_OT_save_bundle(bpy.types.Operator):
    bl_idname = "bareblocks.save_bundle"
    bl_label = "Save Bundle"
    bl_description = "Save the selected objects as a reusable bundle (.blend) you can re-import"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT" and len(context.selected_objects) >= 1

    def execute(self, context):
        objs = set(context.selected_objects)
        # Mark as assets too, so the bundle folder works as an Asset Browser library.
        for o in objs:
            try:
                o.asset_mark()
                o.asset_generate_preview()
            except Exception:
                pass
        name = bpy.path.clean_name(context.scene.bareblocks.bundle_name) or "bundle"
        path = os.path.join(get_bundle_dir(), name + ".blend")
        try:
            bpy.data.libraries.write(path, objs, fake_user=True, compress=True)
        except Exception as exc:  # noqa: BLE001
            self.report({"ERROR"}, f"Could not save bundle: {exc}")
            return {"CANCELLED"}
        refresh_bundle_items()
        self.report({"INFO"}, f"Saved bundle '{name}' ({len(objs)} object(s))")
        return {"FINISHED"}


class BAREBLOCKS_OT_import_bundle(bpy.types.Operator):
    bl_idname = "bareblocks.import_bundle"
    bl_label = "Import Bundle"
    bl_description = "Append the chosen bundle's objects into the scene"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        fname = context.scene.bareblocks.bundle_enum
        if not fname:
            self.report({"WARNING"}, "No bundle selected")
            return {"CANCELLED"}
        path = os.path.join(get_bundle_dir(), fname)
        if not os.path.isfile(path):
            self.report({"ERROR"}, "Bundle file not found")
            return {"CANCELLED"}
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = list(src.objects)
        coll = ensure_collection(context=context)
        added = 0
        for o in dst.objects:
            if o is None:
                continue
            if o.name not in coll.objects:
                coll.objects.link(o)
            added += 1
        self.report({"INFO"}, f"Imported {added} object(s) from '{fname}'")
        return {"FINISHED"}


class BAREBLOCKS_OT_refresh_bundles(bpy.types.Operator):
    bl_idname = "bareblocks.refresh_bundles"
    bl_label = "Refresh Bundles"
    bl_description = "Rescan the bundle folder"
    bl_options = {"REGISTER"}

    def execute(self, context):
        refresh_bundle_items()
        return {"FINISHED"}


class BAREBLOCKS_OT_open_bundle_dir(bpy.types.Operator):
    bl_idname = "bareblocks.open_bundle_dir"
    bl_label = "Open Bundle Folder"
    bl_description = "Open the bundle folder in your file browser"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.path_open(filepath=get_bundle_dir())
        return {"FINISHED"}


class BAREBLOCKS_OT_register_asset_library(bpy.types.Operator):
    bl_idname = "bareblocks.register_asset_library"
    bl_label = "Register Asset Library"
    bl_description = ("Add the bundle folder to Blender's Asset Libraries so bundles show in "
                     "the Asset Browser for drag-drop")
    bl_options = {"REGISTER"}

    def execute(self, context):
        d = get_bundle_dir()
        libs = context.preferences.filepaths.asset_libraries
        for lib in libs:
            if lib.path and os.path.normcase(bpy.path.abspath(lib.path)) == os.path.normcase(d):
                self.report({"INFO"}, "Asset library already registered")
                return {"FINISHED"}
        bpy.ops.preferences.asset_library_add(directory=d)
        libs[-1].name = ASSET_LIB_NAME
        self.report({"INFO"}, f"Registered asset library: {ASSET_LIB_NAME}")
        return {"FINISHED"}


classes = [
    BAREBLOCKS_OT_save_bundle,
    BAREBLOCKS_OT_import_bundle,
    BAREBLOCKS_OT_refresh_bundles,
    BAREBLOCKS_OT_open_bundle_dir,
    BAREBLOCKS_OT_register_asset_library,
]
