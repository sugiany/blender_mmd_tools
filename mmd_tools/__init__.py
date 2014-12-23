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
    self.layout.operator(operators.ImportPmx.bl_idname, text="MikuMikuDance Model (.pmd, .pmx)")
    self.layout.operator(operators.ImportVmd.bl_idname, text="MikuMikuDance Motion (.vmd)")

def menu_func_export(self, context):
    self.layout.operator(operators.ExportPmx.bl_idname, text="MikuMikuDance model (.pmx)")

def menu_func_armature(self, context):
    self.layout.operator(operators.CreateMMDModelRoot.bl_idname, text='Create MMD Model')

_custom_props = {
    bpy.types.Object: [
        ('mmd_type', bpy.props.EnumProperty(
                name='Type',
                default='NONE',
                items=[
                    ('NONE', 'None', '', 1),
                    ('ROOT', 'Root', '', 2),
                    ('RIGID_GRP_OBJ', 'Rigid Body Grp Empty', '', 3),
                    ('JOINT_GRP_OBJ', 'Joint Grp Empty', '', 4),
                    ('TEMPORARY_GRP_OBJ', 'Temporary Grp Empty', '', 5),

                    ('CAMERA', 'Camera', '', 21),
                    ('JOINT', 'Joint', '', 22),
                    ('RIGID_BODY', 'Rigid body', '', 23),
                    ('LIGHT', 'Light', '', 24),

                    ('TRACK_TARGET', 'Track Target', '', 51),
                    ('NON_COLLISION_CONSTRAINT', 'Non Collision Constraint', '', 52),
                    ('SPRING_CONSTRAINT', 'Spring Constraint', '', 53),
                    ('SPRING_GOAL', 'Spring Goal', '', 54),
                    ]
                )
         ),
        ('is_mmd_lamp', bpy.props.BoolProperty(name='is_mmd_lamp', default=False)),
        ('is_mmd_rigid_track_target', bpy.props.BoolProperty(name='is_mmd_rigid_track_target', default=False)),
        ('is_mmd_glsl_light', bpy.props.BoolProperty(name='is_mmd_glsl_light', default=False)),
        ('pmx_import_scale', bpy.props.FloatProperty(name='pmx_import_scale')),
        ],
    bpy.types.PoseBone: [
        ('is_mmd_shadow_bone', bpy.props.BoolProperty(name='is_mmd_shadow_bone', default=False)),
        ('mmd_shadow_bone_type', bpy.props.StringProperty(name='mmd_shadow_bone_type')),
    ],
}

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    bpy.types.INFO_MT_armature_add.append(menu_func_armature)

    properties.register()

    for typ, props in _custom_props.items():
        for attr, prop in props:
            setattr(typ, attr, prop)

def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

    properties.unregister()

    for t in _custom_props:
        for (n, v) in _custom_props[t]:
            delattr(t, n)

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
