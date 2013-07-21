# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
import mathutils

from . import pmx
from . import bpyutils

import re
import math
import logging
import time


#####################
# Rigging Oparators #
#####################
class ShowRigidBodies(Operator):
    bl_idname = 'mmd_tools.show_rigid_bodies'
    bl_label = 'Show Rigid Bodies'
    bl_description = 'Show Rigid bodies'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in findRididBodyObjects():
            i.hide = False
        return {'FINISHED'}

class HideRigidBodies(Operator):
    bl_idname = 'mmd_tools.hide_rigid_bodies'
    bl_label = 'Hide Rigid Bodies'
    bl_description = 'Hide Rigid bodies'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in findRididBodyObjects():
            i.hide = True
        return {'FINISHED'}

class ShowJoints(Operator):
    bl_idname = 'mmd_tools.show_joints'
    bl_label = 'Show joints'
    bl_description = 'Show joints'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in findJointObjects():
            i.hide = False
        return {'FINISHED'}

class HideJoints(Operator):
    bl_idname = 'mmd_tools.hide_joints'
    bl_label = 'Hide joints'
    bl_description = 'Hide joints'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in findJointObjects():
            i.hide = True
        return {'FINISHED'}

class ShowTemporaryObjects(Operator):
    bl_idname = 'mmd_tools.show_temporary_objects'
    bl_label = 'Show temporary objects'
    bl_description = 'Show temporary objects'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in findTemporaryObjects():
            i.hide = False
        return {'FINISHED'}

class HideTemporaryObjects(Operator):
    bl_idname = 'mmd_tools.hide_temporary_objects'
    bl_label = 'Hide temporary objects'
    bl_description = 'Hide temporary objects'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in findTemporaryObjects():
            i.hide = True
        return {'FINISHED'}

class CleanRiggingObjects(Operator):
    bl_idname = 'mmd_tools.clean_rigging_objects'
    bl_label = 'Clean'
    bl_description = 'Clean temporary objects of rigging'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in findTemporaryObjects():
            context.scene.objects.unlink(i)
        return {'FINISHED'}

class BuildRig(Operator):
    bl_idname = 'mmd_tools.build_rig'
    bl_label = 'Build'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in findTemporaryObjects():
            context.scene.objects.unlink(i)
        buildRigids(context.scene.objects)
        buildJoints(context.scene.objects)
        return {'FINISHED'}

def isRigidBodyObject(obj):
    return obj.is_mmd_rigid and not (obj.is_mmd_rigid_track_target or obj.is_mmd_spring_goal or obj.is_mmd_spring_joint)

def isJointObject(obj):
    return obj.is_mmd_joint

def isTemporaryObject(obj):
    return obj.is_mmd_rigid_track_target or obj.is_mmd_spring_goal or obj.is_mmd_spring_joint or obj.is_mmd_non_collision_constraint

def findRididBodyObjects():
    return filter(isRigidBodyObject, bpy.context.scene.objects)

def findJointObjects():
    return filter(isJointObject, bpy.context.scene.objects)

def findTemporaryObjects(objects=None):
    if objects is None:
        objects = bpy.context.scene.objects
    return filter(isTemporaryObject, objects)


def createRigid(**kwargs):
    ''' Create a object for MMD rigid body dynamics.
    ### Parameters ###
     @param shape_type the shape type.
     @param location location of the rigid body object.
     @param rotation rotation of the rigid body object.
     @param size
     @param dynamics_type the type of dynamics mode. (STATIC / DYNAMIC / DYNAMIC2)
     @param collision_group_number
     @param collision_group_mask list of boolean values. (length:16)
     @param name Object name (Optional)
     @param name_e English object name (Optional)
     @param arm_obj
     @param bone
    '''

    shape_type = kwargs['shape_type']
    location = kwargs['location']
    rotation = kwargs['rotation']
    size = kwargs['size']
    dynamics_type = kwargs['dynamics_type']
    collision_group_number = kwargs.get('collision_group_number')
    collision_group_mask = kwargs.get('collision_group_mask')
    name = kwargs.get('name')
    name_e = kwargs.get('name_e')
    arm_obj = kwargs.get('arm_obj')
    bone = kwargs.get('bone')

    friction = kwargs.get('friction')
    mass = kwargs.get('mass')
    angular_damping = kwargs.get('angular_damping')
    linear_damping = kwargs.get('linear_damping')
    bounce = kwargs.get('bounce')

    if shape_type == pmx.Rigid.TYPE_SPHERE:
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=16,
            ring_count=8,
            size=1,
            view_align=False,
            enter_editmode=False
            )
        size = mathutils.Vector([1,1,1]) * size[0]
        rigid_type = 'SPHERE'
        bpy.ops.object.shade_smooth()
    elif shape_type == pmx.Rigid.TYPE_BOX:
        bpy.ops.mesh.primitive_cube_add(
            view_align=False,
            enter_editmode=False
            )
        size = mathutils.Vector(size)
        rigid_type = 'BOX'
    elif shape_type == pmx.Rigid.TYPE_CAPSULE:
        obj = bpyutils.makeCapsule(radius=size[0], height=size[1])
        size = mathutils.Vector([1,1,1])
        rigid_type = 'CAPSULE'
        bpyutils.select_object(obj)
        bpy.ops.object.shade_smooth()
    else:
        raise ValueError('Unknown shape type: %s'%(str(shape_type)))

    obj = bpy.context.active_object
    bpy.ops.rigidbody.object_add(type='ACTIVE')
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = size
    obj.hide_render = True
    obj.is_mmd_rigid = True

    obj.mmd_rigid.shape = rigid_type
    obj.mmd_rigid.type = str(dynamics_type)

    if collision_group_number is not None:
        obj.mmd_rigid.collision_group_number = collision_group_number
    if collision_group_mask is not None:
        obj.mmd_rigid.collision_group_mask = collision_group_mask
    if name is not None:
        obj.name = name
        obj.mmd_rigid.name = name
    if name_e is not None:
        obj.mmd_rigid.name_e = name_e

    # utils.selectAObject(obj)
    # bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    obj.rigid_body.collision_shape = rigid_type
    rb = obj.rigid_body
    if friction is not None:
        rb.friction = friction
    if mass is not None:
        rb.mass = mass
    if angular_damping is not None:
        rb.angular_damping = angular_damping
    if linear_damping is not None:
        rb.linear_damping = linear_damping
    if bounce:
        rb.restitution = bounce

    constraint = obj.constraints.new('CHILD_OF')
    if arm_obj is not None:
        constraint.target = arm_obj
    if bone != '':
        constraint.subtarget = bone
    constraint.name = 'mmd_tools_rigid_parent'
    constraint.mute = True
    
    return obj

def createJoint(**kwargs):
    ''' Create a joint object for MMD rigid body dynamics.
    ### Parameters ###
     @param shape_type the shape type.
     @param location location of the rigid body object.
     @param rotation rotation of the rigid body object.
     @param size
     @param dynamics_type the type of dynamics mode. (STATIC / DYNAMIC / DYNAMIC2)
     @param collision_group_number
     @param collision_group_mask list of boolean values. (length:16)
     @param name Object name
     @param name_e English object name (Optional)
     @param arm_obj
     @param bone
    '''

    location = kwargs['location']
    rotation = kwargs['rotation']
    size = kwargs['size']

    rigid_a = kwargs['rigid_a']
    rigid_b = kwargs['rigid_b']

    max_loc = kwargs['maximum_location']
    min_loc = kwargs['minimum_location']
    max_rot = kwargs['maximum_rotation']
    min_rot = kwargs['minimum_rotation']
    spring_angular = kwargs['spring_angular']
    spring_linear = kwargs['spring_linear']

    name = kwargs['name']
    name_e = kwargs.get('name_e')
    arm_obj = kwargs.get('arm_obj')

    obj = bpy.data.objects.new(
        'J.'+name,
        None)
    bpy.context.scene.objects.link(obj)
    obj.is_mmd_joint = True
    obj.mmd_joint.name_j = name
    if name_e is not None:
        obj.mmd_joint.name_e = name_e

    obj.location = location
    obj.rotation_euler = rotation
    obj.empty_draw_size = size
    obj.empty_draw_type = 'ARROWS'
    obj.hide_render = True
    if arm_obj is not None:
        obj.parent = arm_obj

    bpyutils.select_object(obj)
    bpy.ops.rigidbody.constraint_add(type='GENERIC_SPRING')
    rbc = obj.rigid_body_constraint

    rbc.object1 = rigid_a
    rbc.object2 = rigid_b

    # if not self.__ignoreNonCollisionGroups:
    #     pass
    #     non_collision_joint = self.__nonCollisionJointTable.get(frozenset((rigid1, rigid2)), None)
    #     if non_collision_joint is None:
    #         rbc.disable_collisions = False
    #     else:
    #         utils.selectAObject(non_collision_joint)
    #         bpy.ops.object.delete(use_global=False)
    #         rbc.disable_collisions = True
    # elif rigid1.rigid_body.kinematic and not rigid2.rigid_body.kinematic or not rigid1.rigid_body.kinematic and rigid2.rigid_body.kinematic:

    rbc.disable_collisions = False
    rbc.use_limit_ang_x = True
    rbc.use_limit_ang_y = True
    rbc.use_limit_ang_z = True
    rbc.use_limit_lin_x = True
    rbc.use_limit_lin_y = True
    rbc.use_limit_lin_z = True
    rbc.use_spring_x = True
    rbc.use_spring_y = True
    rbc.use_spring_z = True

    rbc.limit_lin_x_upper = max_loc[0]
    rbc.limit_lin_y_upper = max_loc[1]
    rbc.limit_lin_z_upper = max_loc[2]

    rbc.limit_lin_x_lower = min_loc[0]
    rbc.limit_lin_y_lower = min_loc[1]
    rbc.limit_lin_z_lower = min_loc[2]

    rbc.limit_ang_x_upper = min_rot[0]
    rbc.limit_ang_y_upper = min_rot[1]
    rbc.limit_ang_z_upper = min_rot[2]

    rbc.limit_ang_x_lower = max_rot[0]
    rbc.limit_ang_y_lower = max_rot[1]
    rbc.limit_ang_z_lower = max_rot[2]

    obj.mmd_joint.spring_linear = spring_linear
    obj.mmd_joint.spring_angular = spring_angular

    # bpy.ops.object.select_all(action='DESELECT')
    # obj.select = True
    # bpy.context.scene.objects.active = self.__armObj
    # bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)
    return obj


class InvalidRigidSettingException(ValueError):
    pass

def updateRigid(rigid_obj):
    if not rigid_obj.is_mmd_rigid:
        raise TypeError('rigid_obj must be a mmd_rigid object')

    rigid = rigid_obj.mmd_rigid
    relation = rigid_obj.constraints['mmd_tools_rigid_parent']
    arm = relation.target
    bone_name = relation.subtarget
    target_bone = None
    if arm is not None and bone_name != '':
        target_bone = arm.pose.bones[bone_name]

    if target_bone is not None:
        for i in target_bone.constraints:
            if i.name == 'mmd_tools_rigid_track':
                target_bone.constraints.remove(i)

    if int(rigid.type) == pmx.Rigid.MODE_STATIC:
        rigid_obj.rigid_body.kinematic = True
    else:
        rigid_obj.rigid_body.kinematic = False

    if int(rigid.type) == pmx.Rigid.MODE_STATIC:
        if arm is not None and bone_name != '':
            relation.mute = False
            relation.inverse_matrix = mathutils.Matrix(target_bone.matrix).inverted()
        else:
            relation.mute = True
    else:
        relation.mute = True

    if int(rigid.type) in [pmx.Rigid.MODE_DYNAMIC, pmx.Rigid.MODE_DYNAMIC_BONE] and arm is not None and target_bone is not None:
        empty = bpy.data.objects.new(
            'mmd_bonetrack',
            None)
        bpy.context.scene.objects.link(empty)
        empty.location = target_bone.tail
        empty.empty_draw_size = 0.1
        empty.empty_draw_type = 'ARROWS'
        empty.is_mmd_rigid_track_target = True

        bpyutils.setParent(empty, rigid_obj)
        empty.hide = True


        for i in target_bone.constraints:
            if i.type == 'IK':
                i.influence = 0
        const = target_bone.constraints.new('DAMPED_TRACK')
        const.name='mmd_tools_rigid_track'
        const.target = empty

    rigid_obj.rigid_body.collision_shape = rigid.shape

def __getRigidRange(obj):
    return (mathutils.Vector(obj.bound_box[0]) - mathutils.Vector(obj.bound_box[6])).length
    
def __makeNonCollisionConstraint(obj_a, obj_b, cnt=0):
    if obj_a == obj_b:
        return
    t = bpy.data.objects.new(
        'ncc.%d'%cnt,
        None)
    bpy.context.scene.objects.link(t)
    t.location = [0, 0, 0]
    t.empty_draw_size = 0.5
    t.empty_draw_type = 'ARROWS'
    t.is_mmd_non_collision_constraint = True
    t.hide_render = True
    # t.parent = self.__root
    bpyutils.select_object(t)
    bpy.ops.rigidbody.constraint_add(type='GENERIC')
    rb = t.rigid_body_constraint
    rb.disable_collisions = True
    rb.object1 = obj_a
    rb.object2 = obj_b
    # self.__nonCollisionConstraints.append(t)
    # self.__nonCollisionJointTable[frozenset((obj_a, obj_b))] = t
    # self.__tempObjGroup.objects.link(t)

def __updateRigids(objects):
    rigid_objects = []
    for i in objects:
        rigid_objects += __updateRigids(i.children)
        if i.is_mmd_rigid:
            updateRigid(i)
            rigid_objects.append(i)

    return list(set(rigid_objects))
    

def buildRigids(objects, distance_of_ignore_collisions=1.5):
    start_time = time.time()
    non_collision_constraint_cnt = 0
    rigid_objects = __updateRigids(objects)
    rigid_object_groups = [[] for i in range(16)]
    for i in rigid_objects:
        rigid_object_groups[i.mmd_rigid.collision_group_number].append(i)

    jointMap = {}
    for joint in findJointObjects():
        rbc = joint.rigid_body_constraint
        rbc.disable_collisions = False
        jointMap[frozenset((rbc.object1, rbc.object2))] = joint
        jointMap[frozenset((rbc.object2, rbc.object1))] = joint

    non_collision_pairs = set()
    for obj_a in rigid_objects:
        for n, ignore in enumerate(obj_a.mmd_rigid.collision_group_mask):
            if not ignore:
                continue
            for obj_b in rigid_object_groups[n]:
                pair = frozenset((obj_a, obj_b))
                if pair in non_collision_pairs:
                    continue
                if pair in jointMap:
                    joint = jointMap[pair]
                    joint.rigid_body_constraint.disable_collisions = True
                else:
                    distance = (mathutils.Vector(obj_a.location) - mathutils.Vector(obj_b.location)).length
                    if distance < distance_of_ignore_collisions * (__getRigidRange(obj_a) + __getRigidRange(obj_b)):
                        __makeNonCollisionConstraint(obj_a, obj_b, non_collision_constraint_cnt)
                        non_collision_constraint_cnt += 1
                non_collision_pairs.add(pair)
                non_collision_pairs.add(frozenset((obj_b, obj_a)))
    return rigid_objects

def __makeSpring(target, base_obj, spring_stiffness):
    bpyutils.select_object(target)
    bpy.ops.object.duplicate()
    spring_target = bpy.context.scene.objects.active
    spring_target.constraints.remove(spring_target.constraints['mmd_tools_rigid_parent'])
    spring_target.is_mmd_spring_goal = True
    spring_target.is_mmd_rigid = False
    spring_target.rigid_body.kinematic = True
    spring_target.rigid_body.collision_groups = (False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True)
    bpy.context.scene.objects.active = base_obj
    bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)
    # self.__rigidObjGroup.objects.unlink(spring_target)
    # self.__tempObjGroup.objects.link(spring_target)

    obj = bpy.data.objects.new(
        'S.'+target.name,
        None)
    bpy.context.scene.objects.link(obj)
    obj.location = target.location
    obj.empty_draw_size = 0.1
    obj.empty_draw_type = 'ARROWS'
    obj.hide_render = True
    obj.is_mmd_spring_joint = True
    # obj.parent = self.__root
    # self.__tempObjGroup.objects.link(obj)
    bpyutils.select_object(obj)
    bpy.ops.rigidbody.constraint_add(type='GENERIC_SPRING')
    rbc = obj.rigid_body_constraint
    rbc.object1 = target
    rbc.object2 = spring_target

    rbc.use_spring_x = True
    rbc.use_spring_y = True
    rbc.use_spring_z = True

    rbc.spring_stiffness_x = spring_stiffness[0]
    rbc.spring_stiffness_y = spring_stiffness[1]
    rbc.spring_stiffness_z = spring_stiffness[2]

def updateJoint(joint_obj):
    rbc = joint_obj.rigid_body_constraint
    if rbc.object1.rigid_body.kinematic:
        __makeSpring(rbc.object2, rbc.object1, joint_obj.mmd_joint.spring_angular)
    if rbc.object2.rigid_body.kinematic:
        __makeSpring(rbc.object1, rbc.object2, joint_obj.mmd_joint.spring_angular)

def buildJoints(objects):
    joints = []
    for joint in objects:
        joints += buildJoints(joint.children)
        if joint.is_mmd_joint:
            updateJoint(joint)
            joints.append(joint)

    return list(set(joints))
