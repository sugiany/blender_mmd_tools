# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator

from mmd_tools import bpyutils
import mmd_tools.core.model as mmd_model


class CreateMMDModelRoot(Operator):
    bl_idname = 'mmd_tools.create_mmd_model_root_object'
    bl_label = 'Create a MMD Model Root Object'
    bl_description = ''
    bl_options = {'PRESET'}

    scale = bpy.props.FloatProperty(name='Scale', default=0.2)

    def execute(self, context):
        rig = mmd_model.Rig.create('New MMD Model', 'New MMD Model', self.scale)
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
