# -*- coding: utf-8 -*-

import bpy
import math
import mathutils


from bpy.types import Operator

import mmd_tools.core.model as mmd_model
from mmd_tools.core import rigid_body
from mmd_tools import utils

class AddRigidBody(Operator):
    bl_idname = 'mmd_tools.add_rigid_body'
    bl_label = 'Add Rigid Body'
    bl_description = 'Adds a Rigid Body'
    bl_options = {'PRESET'}
    
    name_j = bpy.props.StringProperty(name='Name', default='Rigid')
    name_e = bpy.props.StringProperty(name='Name(Eng)', default='Rigid_e')
    
    rigid_type = bpy.props.EnumProperty(
        name='Rigid Type',
        items = [
            (str(rigid_body.MODE_STATIC), 'Static', '', 1),
            (str(rigid_body.MODE_DYNAMIC), 'Dynamic', '', 2),
            (str(rigid_body.MODE_DYNAMIC_BONE), 'Dynamic&BoneTrack', '', 3),
            ],
        )
    rigid_shape = bpy.props.EnumProperty(
        name='Shape',
        items = [
            ('SPHERE', 'Sphere', '', 1),
            ('BOX', 'Box', '', 2),
            ('CAPSULE', 'Capsule', '', 3),
            ],
        )
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root) 
        mmd_root = rig.rootObject().mmd_root
        rigid_shape_list = ['SPHERE', 'BOX', 'CAPSULE']
        arm = rig.armature()
        loc = (0.0, 0.0, 0.0)
        rot = (0.0, 0.0, 0.0)
        bone = None
        bpy.ops.object.mode_set(mode='OBJECT')
        target_bone = context.active_bone
        if target_bone:
            if type(target_bone) is not bpy.types.Bone:
                target_bone = obj.data.bones[target_bone.name]
        elif arm is not None and len(arm.data.bones) > 0:
            target_bone = arm.data.bones[0]

        if target_bone: # bpy.types.Bone
            loc = (target_bone.head_local+target_bone.tail_local)/2
            rot = target_bone.matrix_local.to_euler('YXZ')
            rot.rotate_axis('X', math.pi/2)
            bone = target_bone.name

        rigid = rig.createRigidBody(
                name = self.name_j,
                name_e = self.name_e,
                shape_type = rigid_shape_list.index(self.rigid_shape),
                dynamics_type = int(self.rigid_type),
                location = loc,
                rotation = rot,
                size = mathutils.Vector([2, 2, 2]) * mmd_root.scale,
                collision_group_number = 0,
                collision_group_mask = [False for i in range(16)],
                arm_obj = arm,
                mass=1,
                friction = 0.0,
                angular_damping = 0.5,
                linear_damping = 0.5,
                bounce = 0.5,
                bone = bone,
                )
        if not mmd_root.show_rigid_bodies:
            mmd_root.show_rigid_bodies = True
        utils.selectAObject(rigid)

        return { 'FINISHED' }
        
    def invoke(self, context, event):
        bone = context.active_pose_bone or context.active_bone
        if type(bone) is not bpy.types.PoseBone:
            root = mmd_model.Model.findRoot(context.active_object)
            arm = mmd_model.Model(root).armature()
            if arm is not None and len(arm.pose.bones) > 0:
                if bone is None:
                    bone = arm.pose.bones[0]
                elif bone.name in arm.pose.bones:
                    bone = arm.pose.bones[bone.name]
            else:
                self.name_j = 'Rigid'
                self.name_e = 'Rigid_e'
        if bone:
            self.name_j = bone.name
            if type(bone) is bpy.types.PoseBone:
                mmd_bone = bone.mmd_bone
                if len(mmd_bone.name_j) > 0:
                    self.name_j = mmd_bone.name_j
                if len(mmd_bone.name_e) > 0:
                    self.name_e = mmd_bone.name_e
        vm = context.window_manager
        return vm.invoke_props_dialog(self) 

class RemoveRigidBody(Operator):
    bl_idname = 'mmd_tools.remove_rigid_body'
    bl_label = 'Remove Rigid Body'
    bl_description = 'Deletes the currently selected Rigid Body'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        if obj.mmd_type != 'RIGID_BODY':
            self.report({ 'ERROR' }, "Select the Rigid Body to be deleted")
            return { 'CANCELLED' }
        root = mmd_model.Model.findRoot(obj)
        utils.selectAObject(obj) #ensure this is the only one object select
        bpy.ops.object.delete(use_global=True)
        if root:
            utils.selectAObject(root)
        return { 'FINISHED' } 

class AddJoint(Operator): 
    bl_idname = 'mmd_tools.add_joint'
    bl_label = 'Add Joint'
    bl_options = {'PRESET'} 
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root) 
        mmd_root = rig.rootObject().mmd_root
        name = 'Joint'
        name_e = 'Joint_e'
        loc = (0.0, 0.0, 0.0)
        rigid_a = None
        rigid_b = None
        if mmd_model.isRigidBodyObject(obj):
            if len(context.selected_objects) == 2:
                if obj == context.selected_objects[0]:
                    rigid_a = context.selected_objects[1]
                else:
                    rigid_a = context.selected_objects[0]
            name = obj.name
            name_e = obj.mmd_rigid.name_e
            rigid_b = obj
            relation = rigid_b.constraints['mmd_tools_rigid_parent']
            arm = relation.target
            bone_name = relation.subtarget
            if arm is not None and bone_name in arm.data.bones:
                loc = arm.data.bones[bone_name].head_local
            else:
                loc = rigid_b.location if rigid_a is None else (rigid_a.location+rigid_b.location)/2

        if context.scene.rigidbody_world is None:
            bpy.ops.rigidbody.world_add()

        joint = rig.createJoint(
                name = name,
                name_e = name_e,
                location = loc,
                rotation = [0, 0, 0],
                size = 0.5 * mmd_root.scale,
                rigid_a = rigid_a,
                rigid_b = rigid_b,
                maximum_location = [0, 0, 0],
                minimum_location = [0, 0, 0],
                maximum_rotation = [math.pi/4]*3,
                minimum_rotation = [-math.pi/4]*3,
                spring_linear = [0, 0, 0],
                spring_angular = [0, 0, 0],
                )
        if not mmd_root.show_joints:
            mmd_root.show_joints = True
        utils.selectAObject(joint)

        return { 'FINISHED' }
    
class RemoveJoint(Operator):
    bl_idname = 'mmd_tools.remove_joint'
    bl_label = 'Remove Joint'
    bl_description = 'Deletes the currently selected Joint'
    bl_options = {'PRESET'}  
    
    def execute(self, context):
        obj = context.active_object
        if obj.mmd_type != 'JOINT':
            self.report({ 'ERROR' }, "Select the Joint to be deleted")
            return { 'CANCELLED' }
        root = mmd_model.Model.findRoot(obj)
        utils.selectAObject(obj) #ensure this is the only one object select
        bpy.ops.object.delete(use_global=True)
        if root:
            utils.selectAObject(root)
        return { 'FINISHED' }
