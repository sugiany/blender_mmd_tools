# -*- coding: utf-8 -*-

import bpy

from . import properties
from . import operators
from . import panels

bl_info= {
    "name": "mmd_tools",
    "author": "sugiany",
    "version": (0, 5, 0),
    "blender": (2, 70, 0),
    "location": "View3D > Tool Shelf > MMD Tools Panel",
    "description": "Utility tools for MMD model editing.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"}

# if "bpy" in locals():
#     import imp
#     if "import_pmx" in locals():
#         imp.reload(import_pmx)
#     if "export_pmx" in locals():
#         imp.reload(export_pmx)
#     if "import_vmd" in locals():
#         imp.reload(import_vmd)
#     if "mmd_camera" in locals():
#         imp.reload(mmd_camera)
#     if "utils" in locals():
#         imp.reload(utils)
#     if "cycles_converter" in locals():
#         imp.reload(cycles_converter)
#     if "auto_scene_setup" in locals():
#         imp.reload(auto_scene_setup)

def menu_func_import(self, context):
    self.layout.operator(operators.fileio.ImportPmx.bl_idname, text="MikuMikuDance Model (.pmd, .pmx)")
    self.layout.operator(operators.fileio.ImportVmd.bl_idname, text="MikuMikuDance Motion (.vmd)")

def menu_func_export(self, context):
    self.layout.operator(operators.fileio.ExportPmx.bl_idname, text="MikuMikuDance model (.pmx)")

def menu_func_armature(self, context):
    self.layout.operator(operators.model.CreateMMDModelRoot.bl_idname, text='Create MMD Model')


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.types.INFO_MT_armature_add.append(menu_func_armature)
    properties.register()

def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    properties.unregister()
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
