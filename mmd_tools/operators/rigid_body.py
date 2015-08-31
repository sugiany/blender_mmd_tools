# -*- coding: utf-8 -*-

import bpy
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
        if context.active_pose_bone is not None:
            loc = context.active_pose_bone.location
            bone = context.active_pose_bone.name
        elif context.active_bone is not None:
            loc = context.active_bone.head
            bone = context.active_bone.name
        elif arm is not None and len(arm.pose.bones) > 0:
            loc = arm.pose.bones[0].location
            bone = arm.pose.bones[0].name
            
        bpy.ops.object.mode_set(mode='OBJECT')
                    
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
        if mmd_root.show_rigid_bodies:
            rigid.hide = False
            utils.selectAObject(rigid)
        else:
            rigid.hide = True
            utils.selectAObject(obj)
            
        if 'mmd_tools.'+mmd_root.name+'_all' in bpy.data.groups.keys(): # Add Rigid to allObjectsGroup
            bpy.data.groups['mmd_tools.'+mmd_root.name+'_all'].objects.link(rigid)
        if 'mmd_tools.'+mmd_root.name+'_rigids' in bpy.data.groups.keys(): # Add Rigid to RigidsGroup
            bpy.data.groups['mmd_tools.'+mmd_root.name+'_rigids'].objects.link(rigid)
            
        return { 'FINISHED' }
        
    def invoke(self, context, event):
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
        utils.selectAObject(obj) #ensure this is the only one object select
        bpy.ops.object.delete(use_global=True)
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
        joint = rig.createJoint(
                name = 'Joint',
                name_e = 'Joint_e',
                location = [0, 0, 0],
                rotation = [0, 0, 0],
                size = 0.5 * mmd_root.scale,
                rigid_a = None,
                rigid_b = None,
                maximum_location = [0, 0, 0],
                minimum_location = [0, 0, 0],
                maximum_rotation = [0, 0, 0],
                minimum_rotation = [0, 0, 0],
                spring_linear = [0, 0, 0],
                spring_angular = [0, 0, 0],
                )
        if mmd_root.show_joints:
            joint.hide = False
            utils.selectAObject(joint)
        else:
            joint.hide = True
            utils.selectAObject(obj)
            
        if 'mmd_tools.'+mmd_root.name+'_all' in bpy.data.groups.keys(): # Add Joint to allGroup
            bpy.data.groups['mmd_tools.'+mmd_root.name+'_all'].link(joint)
        if 'mmd_tools.'+mmd_root.name+'_joints' in bpy.data.groups.keys(): # Add Joint to joints group
            bpy.data.groups['mmd_tools.'+mmd_root.name+'_joints'].link(joint)
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
        utils.selectAObject(obj) #ensure this is the only one object select
        bpy.ops.object.delete(use_global=True)
        return { 'FINISHED' }