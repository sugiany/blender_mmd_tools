# -*- coding: utf-8 -*-

from bpy.types import Operator

import mmd_tools.core.camera as mmd_camera

class ConvertToMMDCamera(Operator):
    bl_idname = 'mmd_tools.convert_to_mmd_camera'
    bl_label = 'Convert to MMD Camera'
    bl_description = 'create a camera rig for mmd.'
    bl_options = {'PRESET'}

    def execute(self, context):
        mmd_camera.MMDCamera.convertToMMDCamera(context.active_object)
        return {'FINISHED'}
