# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty

from mmd_tools.core import material

class _OpenTextureBase(object):
    """ Create a texture for mmd model material.
    """
    bl_options = {'PRESET'}

    filepath = StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
        )

    use_filter_image = BoolProperty(
        default=True,
        options={'HIDDEN'},
        )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class OpenTexture(Operator, _OpenTextureBase):
    bl_idname = 'mmd_tools.material_open_texture'
    bl_label = 'Open Texture'
    bl_description = ''
    
    def execute(self, context):
        mat = context.active_object.active_material
        material.create_texture(mat, self.filepath)
        return {'FINISHED'}


class RemoveTexture(Operator):
    """ Create a texture for mmd model material.
    """
    bl_idname = 'mmd_tools.material_remove_texture'
    bl_label = 'Remove Texture'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        mat = context.active_object.active_material
        material.remove_texture(mat)
        return {'FINISHED'}

class OpenSphereTextureSlot(Operator, _OpenTextureBase):
    """ Create a texture for mmd model material.
    """
    bl_idname = 'mmd_tools.material_open_sphere_texture'
    bl_label = 'Open Sphere Texture'
    bl_description = ''

    def execute(self, context):
        mat = context.active_object.active_material
        material.create_sphere_texture(mat, self.filepath)
        return {'FINISHED'}


class RemoveSphereTexture(Operator):
    """ Create a texture for mmd model material.
    """
    bl_idname = 'mmd_tools.material_remove_sphere_texture'
    bl_label = 'Remove texture'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        mat = context.active_object.active_material
        material.remove_sphere_texture(mat)
        return {'FINISHED'}
