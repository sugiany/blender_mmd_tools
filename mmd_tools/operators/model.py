# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator

from mmd_tools import bpyutils
import mmd_tools.core.model as mmd_model


class CleanRiggingObjects(Operator):
    bl_idname = 'mmd_tools.clean_rig'
    bl_label = 'Clean'
    bl_description = 'Clean temporary objects of rigging'
    bl_options = {'PRESET'}

    def execute(self, context):
        root = mmd_model.Model.findRoot(context.active_object)
        rig = mmd_model.Model(root)
        rig.clean()
        return {'FINISHED'}

class BuildRig(Operator):
    bl_idname = 'mmd_tools.build_rig'
    bl_label = 'Build'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(context.active_object)
        rig = mmd_model.Model(root)
        rig.build()
        context.scene.objects.active = obj
        return {'FINISHED'}

class ApplyAdditionalTransformConstraints(Operator):
    bl_idname = 'mmd_tools.apply_additioinal_transform'
    bl_label = 'Apply Additional Transform'
    bl_description = ''
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        return mmd_model.Model.findRoot(context.active_object)

    def execute(self, context):
        root = mmd_model.Model.findRoot(context.active_object)
        mmd_model.Model(root)
        #context.scene.objects.active = obj
        return {'FINISHED'}

class CreateMMDModelRoot(Operator):
    bl_idname = 'mmd_tools.create_mmd_model_root_object'
    bl_label = 'Create a MMD Model Root Object'
    bl_description = ''
    bl_options = {'PRESET'}

    scale = bpy.props.FloatProperty(name='Scale', default=0.2)

    def execute(self, context):
        rig = mmd_model.Model.create('New MMD Model', 'New MMD Model', self.scale)
        arm = rig.armature()
        with bpyutils.edit_object(arm) as data:
            bone = data.edit_bones.new(name=u'全ての親')
            bone.head = [0.0, 0.0, 0.0]
            bone.tail = [0.0, 0.0, 1.0*self.scale]
        mmd_root = rig.rootObject().mmd_root
        frame_root = mmd_root.display_item_frames.add()
        frame_root.name = 'Root'
        frame_root.is_special = True
        frame_facial = mmd_root.display_item_frames.add()
        frame_facial.name = u'表情'
        frame_facial.is_special = True

        return {'FINISHED'}

    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)
