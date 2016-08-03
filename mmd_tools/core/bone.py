# -*- coding: utf-8 -*-

import bpy
from bpy.types import PoseBone
import mathutils

from mmd_tools import bpyutils


def remove_constraint(constraints, name):
    c = constraints.get(name, None)
    if c:
        constraints.remove(c)
        return True
    return False

def remove_edit_bones(edit_bones, bone_names):
    for name in bone_names:
        b = edit_bones.get(name, None)
        if b:
            edit_bones.remove(b)


class FnBone(object):

    def __init__(self, pose_bone=None):
        if pose_bone is not None and not isinstance(pose_bone, PoseBone):
            raise ValueError
        self.__bone = pose_bone

    @classmethod
    def from_bone_id(cls, armature, bone_id):
        for bone in armature.pose.bones:
            if bone.mmd_bone.bone_id == bone_id:
                return cls(bone)
        return None

    @property
    def bone_id(self):
        mmd_bone = self.__bone.mmd_bone
        if mmd_bone.bone_id < 0:
            max_id = -1
            for bone in self.__bone.id_data.pose.bones:
                max_id = max(max_id, bone.mmd_bone.bone_id)
            mmd_bone.bone_id = max_id + 1
        return mmd_bone.bone_id

    def __get_pose_bone(self):
        return self.__bone

    def __set_pose_bone(self, pose_bone):
        if not isinstance(pose_bone, bpy.types.PoseBone):
            raise ValueError
        self.__bone = pose_bone

    pose_bone = property(__get_pose_bone, __set_pose_bone)

    @classmethod
    def clean_additional_transformation(cls, armature):
        # clean shadow bones
        shadow_bone_types = {
            'DUMMY',
            'SHADOW',
            'ADDITIONAL_TRANSFORM',
            'ADDITIONAL_TRANSFORM_INVERT',
        }
        def __is_at_shadow_bone(b):
            return b.is_mmd_shadow_bone and b.mmd_shadow_bone_type in shadow_bone_types
        shadow_bone_names = [b.name for b in armature.pose.bones if __is_at_shadow_bone(b)]

        if len(shadow_bone_names) > 0:
            with bpyutils.edit_object(armature) as data:
                remove_edit_bones(data.edit_bones, shadow_bone_names)

        # clean constraints
        for p_bone in armature.pose.bones:
            p_bone.mmd_bone.is_additional_transform_dirty = True
            constraints = p_bone.constraints
            remove_constraint(constraints, 'mmd_additional_rotation')
            remove_constraint(constraints, 'mmd_additional_location')
            if remove_constraint(constraints, 'mmd_additional_parent'):
                p_bone.bone.use_inherit_rotation = True

    @classmethod
    def apply_additional_transformation(cls, armature):

        def __is_dirty_bone(b):
            return not b.is_mmd_shadow_bone and b.mmd_bone.is_additional_transform_dirty
        dirty_bones = [b for b in armature.pose.bones if __is_dirty_bone(b)]

        # setup constraints
        shadow_bone_pool = []
        for p_bone in dirty_bones:
            sb = cls.__setup_constraints(p_bone)
            if sb:
                shadow_bone_pool.append(sb)

        # setup shadow bones
        need_mode_change = armature.mode == 'EDIT'
        with bpyutils.edit_object(armature) as data:
            edit_bones = data.edit_bones
            for sb in shadow_bone_pool:
                sb.update_edit_bones(edit_bones)

            if need_mode_change:
                bpy.ops.object.mode_set(mode='OBJECT')

        pose_bones = armature.pose.bones
        for sb in shadow_bone_pool:
            sb.update_pose_bones(pose_bones)

        # finish
        for p_bone in dirty_bones:
            p_bone.mmd_bone.is_additional_transform_dirty = False

    @classmethod
    def __setup_constraints(cls, p_bone):
        bone_name = p_bone.name
        mmd_bone = p_bone.mmd_bone
        influence = mmd_bone.additional_transform_influence
        target_bone = mmd_bone.additional_transform_bone
        mute_rotation = not mmd_bone.has_additional_rotation
        mute_location = not mmd_bone.has_additional_location

        constraints = p_bone.constraints
        if not target_bone or (mute_rotation and mute_location) or influence == 0:
            rot = remove_constraint(constraints, 'mmd_additional_rotation')
            loc = remove_constraint(constraints, 'mmd_additional_location')
            if rot or loc:
                return _AT_ShadowBoneRemove(bone_name)
            return None

        invert = influence < 0
        influence = abs(influence)
        shadow_bone = _AT_ShadowBoneCreate(bone_name, target_bone)

        c = constraints.get('mmd_additional_rotation', None)
        if mute_rotation:
            if c:
                constraints.remove(c)
        else:
            if c and c.type != 'COPY_ROTATION':
                constraints.remove(c)
                c = None
            if c is None:
                c = constraints.new('COPY_ROTATION')
                c.name = 'mmd_additional_rotation'
            c.use_offset = True
            c.influence = influence
            c.target = p_bone.id_data
            c.target_space = 'LOCAL'
            c.owner_space = 'LOCAL'
            c.invert_x = invert
            c.invert_y = invert
            c.invert_z = invert
            shadow_bone.add_constraint(c)

        c = constraints.get('mmd_additional_location', None)
        if mute_location:
            if c:
                constraints.remove(c)
        else:
            if c and c.type != 'COPY_LOCATION':
                constraints.remove(c)
                c = None
            if c is None:
                c = constraints.new('COPY_LOCATION')
                c.name = 'mmd_additional_location'
            c.use_offset = True
            c.influence = influence
            c.target = p_bone.id_data
            c.target_space = 'LOCAL'
            c.owner_space = 'LOCAL'
            c.invert_x = invert
            c.invert_y = invert
            c.invert_z = invert
            shadow_bone.add_constraint(c)

        return shadow_bone


class _AT_ShadowBoneRemove:
    def __init__(self, bone_name):
        self.__shadow_bone_names = ('_dummy.' + bone_name, '_shadow.' + bone_name)

    def update_edit_bones(self, edit_bones):
        remove_edit_bones(edit_bones, self.__shadow_bone_names)

    def update_pose_bones(self, pose_bones):
        pass

class _AT_ShadowBoneCreate:
    def __init__(self, bone_name, target_bone_name):
        self.__dummy_bone_name = '_dummy.' + bone_name
        self.__shadow_bone_name = '_shadow.' + bone_name
        self.__bone_name = bone_name
        self.__target_bone_name = target_bone_name
        self.__constraint_pool = []

    def __update_constraints(self):
        subtarget = self.__shadow_bone_name
        for c in self.__constraint_pool:
            c.subtarget = subtarget

    def add_constraint(self, constraint):
        self.__constraint_pool.append(constraint)

    def update_edit_bones(self, edit_bones):
        bone = edit_bones[self.__bone_name]
        target_bone = edit_bones[self.__target_bone_name]

        dummy_bone_name = self.__dummy_bone_name
        dummy = edit_bones.get(dummy_bone_name, None)
        if dummy is None:
            dummy = edit_bones.new(name=dummy_bone_name)
            dummy.layers = [x == 9 for x in range(len(dummy.layers))]
            dummy.use_deform = False
        dummy.parent = target_bone
        dummy.head = target_bone.head
        dummy.tail = dummy.head + bone.tail - bone.head
        dummy.align_roll(bone.z_axis)

        shadow_bone_name = self.__shadow_bone_name
        shadow = edit_bones.get(shadow_bone_name, None)
        if shadow is None:
            shadow = edit_bones.new(name=shadow_bone_name)
            shadow.layers = [x == 8 for x in range(len(shadow.layers))]
            shadow.use_deform = False
        shadow.parent = target_bone.parent
        shadow.head = dummy.head
        shadow.tail = dummy.tail
        shadow.align_roll(bone.z_axis)

    def update_pose_bones(self, pose_bones):
        dummy_p_bone = pose_bones[self.__dummy_bone_name]
        dummy_p_bone.is_mmd_shadow_bone = True
        dummy_p_bone.mmd_shadow_bone_type = 'DUMMY'

        shadow_p_bone = pose_bones[self.__shadow_bone_name]
        shadow_p_bone.is_mmd_shadow_bone = True
        shadow_p_bone.mmd_shadow_bone_type = 'SHADOW'

        if 'mmd_tools_at_dummy' not in shadow_p_bone.constraints:
            c = shadow_p_bone.constraints.new('COPY_TRANSFORMS')
            c.name = 'mmd_tools_at_dummy'
            c.target = dummy_p_bone.id_data
            c.subtarget = dummy_p_bone.name
            c.target_space = 'POSE'
            c.owner_space = 'POSE'

        self.__update_constraints()

