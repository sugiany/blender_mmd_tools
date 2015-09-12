# -*- coding: utf-8 -*-

from bpy.types import Operator

from mmd_tools import utils


class SeparateByMaterials(Operator):
    bl_idname = 'mmd_tools.separate_by_materials'
    bl_label = 'Separate by materials'
    bl_description = 'Separate by materials'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        utils.separateByMaterials(context.active_object)
        return {'FINISHED'}
