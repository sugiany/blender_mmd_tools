# -*- coding: utf-8 -*-

import bpy

from . import properties
from . import operators
from . import panels

bl_info= {
    "name": "mmd_tools",
    "author": "sugiany",
    "version": (0, 4, 3),
    "blender": (2, 67, 0),
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

def register():
    bpy.utils.register_class(properties.MMDRoot)
    bpy.utils.register_class(properties.MMDMaterial)
    bpy.utils.register_class(properties.MMDCamera)
    bpy.utils.register_class(properties.MMDBone)
    bpy.utils.register_class(properties.MMDRigid)
    bpy.utils.register_class(properties.MMDJoint)
    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


    #bpy.types.Object.is_mmd_root = bpy.props.BoolProperty(name='is_mmd_root', default=False)

    #bpy.types.Object.is_mmd_camera = bpy.props.BoolProperty(name='is_mmd_camera', default=False)
    bpy.types.Object.mmd_camera = bpy.props.PointerProperty(type=properties.MMDCamera)
    bpy.types.Object.mmd_root = bpy.props.PointerProperty(type=properties.MMDRoot)

    # Material custom properties
    bpy.types.Material.mmd_material = bpy.props.PointerProperty(type=properties.MMDMaterial)

    bpy.types.Object.mmd_type = bpy.props.EnumProperty(
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

    bpy.types.Object.is_mmd_lamp = bpy.props.BoolProperty(name='is_mmd_lamp', default=False)

    # bpy.types.Object.is_mmd_rigid = bpy.props.BoolProperty(name='is_mmd_rigid', default=False)
    bpy.types.Object.mmd_rigid = bpy.props.PointerProperty(type=properties.MMDRigid)


    # bpy.types.Object.is_mmd_joint = bpy.props.BoolProperty(name='is_mmd_joint', default=False)
    bpy.types.Object.mmd_joint = bpy.props.PointerProperty(type=properties.MMDJoint)

    bpy.types.Object.is_mmd_rigid_track_target = bpy.props.BoolProperty(name='is_mmd_rigid_track_target', default=False)
    #bpy.types.Object.is_mmd_non_collision_constraint = bpy.props.BoolProperty(name='is_mmd_non_collision_constraint', default=False)
    #bpy.types.Object.is_mmd_spring_joint = bpy.props.BoolProperty(name='is_mmd_spring_joint', default=False)
    #bpy.types.Object.is_mmd_spring_goal = bpy.props.BoolProperty(name='is_mmd_spring_goal', default=False)

    bpy.types.PoseBone.mmd_bone = bpy.props.PointerProperty(type=properties.MMDBone)

    bpy.types.PoseBone.is_mmd_shadow_bone = bpy.props.BoolProperty(name='is_mmd_shadow_bone', default=False)
    bpy.types.PoseBone.mmd_shadow_bone_type = bpy.props.StringProperty(name='mmd_shadow_bone_type')

    bpy.types.Object.is_mmd_glsl_light = bpy.props.BoolProperty(name='is_mmd_glsl_light', default=False)


    bpy.utils.register_module(__name__)

def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

    del bpy.types.Object.is_mmd_camera
    del bpy.types.Object.mmd_camera

    del bpy.types.Object.is_mmd_lamp

    del bpy.types.Object.is_mmd_rigid
    del bpy.types.Object.mmd_rigid

    del bpy.types.Object.is_mmd_joint
    del bpy.types.Object.mmd_joint

    del bpy.types.Object.is_mmd_rigid_track_target
    del bpy.types.Object.is_mmd_non_collision_constraint
    del bpy.types.Object.is_mmd_spring_joint
    del bpy.types.Object.is_mmd_spring_goal

    del bpy.types.PoseBone.mmd_bone
    del bpy.types.Material.mmd_material

    del bpy.types.PoseBone.is_mmd_shadow_bone
    del bpy.types.Object.is_mmd_glsl_light

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
