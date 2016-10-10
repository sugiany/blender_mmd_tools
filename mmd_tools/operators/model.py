# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator

from mmd_tools import bpyutils
import mmd_tools.core.model as mmd_model


class CleanRiggingObjects(Operator):
    bl_idname = 'mmd_tools.clean_rig'
    bl_label = 'Clean Rig'
    bl_description = 'Delete temporary physics objects of selected object and revert physics to default MMD state'
    bl_options = {'PRESET'}

    def execute(self, context):
        root = mmd_model.Model.findRoot(context.active_object)
        rig = mmd_model.Model(root)
        rig.clean()
        context.scene.objects.active = root
        return {'FINISHED'}

class BuildRig(Operator):
    bl_idname = 'mmd_tools.build_rig'
    bl_label = 'Build Rig'
    bl_description = 'Translate physics of selected object into format usable by Blender'
    bl_options = {'PRESET'}

    def execute(self, context):
        root = mmd_model.Model.findRoot(context.active_object)
        rig = mmd_model.Model(root)
        rig.build()
        context.scene.objects.active = root
        return {'FINISHED'}

class CleanAdditionalTransformConstraints(Operator):
    bl_idname = 'mmd_tools.clean_additioinal_transform'
    bl_label = 'Clean Additional Transform'
    bl_description = 'Delete shadow bones of selected object and revert bones to default MMD state'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        return mmd_model.Model.findRoot(context.active_object)

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        rig.cleanAdditionalTransformConstraints()
        context.scene.objects.active = obj
        return {'FINISHED'}

class ApplyAdditionalTransformConstraints(Operator):
    bl_idname = 'mmd_tools.apply_additioinal_transform'
    bl_label = 'Apply Additional Transform'
    bl_description = 'Translate appended bones of selected object for Blender'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        return mmd_model.Model.findRoot(context.active_object)

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        rig.applyAdditionalTransformConstraints()
        context.scene.objects.active = obj
        return {'FINISHED'}

class CreateMMDModelRoot(Operator):
    bl_idname = 'mmd_tools.create_mmd_model_root_object'
    bl_label = 'Create a MMD Model Root Object'
    bl_description = 'Create a MMD model root object with a basic armature'
    bl_options = {'PRESET'}

    name_j = bpy.props.StringProperty(
        name='Name',
        description='The name of the MMD model',
        default='New MMD Model',
        )
    name_e = bpy.props.StringProperty(
        name='Name(Eng)',
        description='The english name of the MMD model',
        default='New MMD Model',
        )
    scale = bpy.props.FloatProperty(
        name='Scale',
        description='Scale',
        default=0.2,
        )

    def execute(self, context):
        rig = mmd_model.Model.create(self.name_j, self.name_e, self.scale)
        arm = rig.armature()
        with bpyutils.edit_object(arm) as data:
            bone = data.edit_bones.new(name=u'全ての親')
            bone.head = [0.0, 0.0, 0.0]
            bone.tail = [0.0, 0.0, 1.0]
        arm.pose.bones[u'全ての親'].mmd_bone.name_j = u'全ての親'
        arm.pose.bones[u'全ての親'].mmd_bone.name_e = 'Root'

        rig.initialDisplayFrames()
        mmd_root = rig.rootObject().mmd_root
        frame_root = mmd_root.display_item_frames['Root']
        item = frame_root.items.add()
        item.type = 'BONE'
        item.name = arm.data.bones[0].name

        return {'FINISHED'}

    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)
