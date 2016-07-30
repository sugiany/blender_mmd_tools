# -*- coding: utf-8 -*-

import bpy
from bpy.types import PoseBone
import mathutils

from mmd_tools import bpyutils

class FnBone(object):
    AT_DUMMY_CONSTRAINT_NAME = 'mmd_tools_at_dummy'
    AT_ROTATION_CONSTRAINT_NAME = 'mmd_additional_rotation'
    AT_LOCATION_CONSTRAINT_NAME = 'mmd_additional_location'
    AT_PARENT_CONSTRAINT_NAME = 'mmd_additional_parent'

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
    def __remove_bones(cls, armature, bone_names):
        if len(bone_names) < 1:
            return
        with bpyutils.edit_object(armature) as data:
            for name in bone_names:
                b = data.edit_bones.get(name, None)
                if b:
                    data.edit_bones.remove(b)

    @classmethod
    def __remove_constraint(cls, constraints, name):
        c = constraints.get(name, None)
        if c:
            constraints.remove(c)
            return True
        return False

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
        cls.__remove_bones(armature, shadow_bone_names)

        # clean constraints
        for p_bone in armature.pose.bones:
            p_bone.mmd_bone.is_additional_transform_dirty = True
            constraints = p_bone.constraints
            cls.__remove_constraint(constraints, cls.AT_ROTATION_CONSTRAINT_NAME)
            cls.__remove_constraint(constraints, cls.AT_LOCATION_CONSTRAINT_NAME)
            if cls.__remove_constraint(constraints, cls.AT_PARENT_CONSTRAINT_NAME):
                p_bone.bone.use_inherit_rotation = True

    #****************************************
    # Methods for additional transformation
    #****************************************
    def apply_additional_transformation(self):
        """ create or update constaints to apply additional transformation
        """
        p_bone = self.__bone
        if p_bone.is_mmd_shadow_bone:
            return

        arm = p_bone.id_data
        mmd_bone = p_bone.mmd_bone
        if not mmd_bone.is_additional_transform_dirty:
            return

        influence = mmd_bone.additional_transform_influence
        source_bone = mmd_bone.additional_transform_bone
        mute_rotation = not mmd_bone.has_additional_rotation
        mute_location = not mmd_bone.has_additional_location

        constraints = p_bone.constraints
        if not source_bone or (mute_rotation and mute_location) or influence == 0:
            rot = self.__remove_constraint(constraints, self.AT_ROTATION_CONSTRAINT_NAME)
            loc = self.__remove_constraint(constraints, self.AT_LOCATION_CONSTRAINT_NAME)
            if rot or loc:
                bone_name = p_bone.name
                self.__remove_bones(arm, ['_dummy.' + bone_name, '_shadow.' + bone_name])
            mmd_bone.is_additional_transform_dirty = False
            return

        invert = influence < 0
        influence = abs(influence)

        shadow_bone = self.__get_at_shadow_bone_v2(arm, source_bone)

        c = constraints.get(self.AT_ROTATION_CONSTRAINT_NAME, None)
        if mute_rotation:
            if c:
                constraints.remove(c)
        else:
            if c and c.type != 'COPY_ROTATION':
                constraints.remove(c)
                c = None
            if c is None:
                c = constraints.new('COPY_ROTATION')
                c.name = self.AT_ROTATION_CONSTRAINT_NAME
            c.use_offset = True
            c.influence = influence
            c.target = arm
            c.subtarget = shadow_bone
            c.target_space = 'LOCAL'
            c.owner_space = 'LOCAL'
            c.invert_x = invert
            c.invert_y = invert
            c.invert_z = invert

        c = constraints.get(self.AT_LOCATION_CONSTRAINT_NAME, None)
        if mute_location:
            if c:
                constraints.remove(c)
        else:
            if c and c.type != 'COPY_LOCATION':
                constraints.remove(c)
                c = None
            if c is None:
                c = constraints.new('COPY_LOCATION')
                c.name = self.AT_LOCATION_CONSTRAINT_NAME
            c.use_offset = True
            c.influence = influence
            c.target = arm
            c.subtarget = shadow_bone
            c.target_space = 'LOCAL'
            c.owner_space = 'LOCAL'
            c.invert_x = invert
            c.invert_y = invert
            c.invert_z = invert

        mmd_bone.is_additional_transform_dirty = False

    def __get_at_shadow_bone_v2(self, arm, source_bone_name):
        bone_name = self.__bone.name

        with bpyutils.edit_object(arm) as data:
            src_bone = data.edit_bones[source_bone_name]
            bone = data.edit_bones[bone_name]

            dummy_bone_name = '_dummy.' + bone_name
            dummy = data.edit_bones.get(dummy_bone_name, None)
            if dummy is None:
                dummy = data.edit_bones.new(name=dummy_bone_name)
                dummy.layers = [x == 9 for x in range(len(dummy.layers))]
                dummy.use_deform = False
            dummy.parent = src_bone
            dummy.head = src_bone.head
            dummy.tail = dummy.head + bone.tail - bone.head
            dummy.align_roll(bone.z_axis)

            shadow_bone_name = '_shadow.' + bone_name
            shadow = data.edit_bones.get(shadow_bone_name, None)
            if shadow is None:
                shadow = data.edit_bones.new(name=shadow_bone_name)
                shadow.layers = [x == 8 for x in range(len(shadow.layers))]
                shadow.use_deform = False
            shadow.parent = src_bone.parent
            shadow.head = dummy.head
            shadow.tail = dummy.tail
            shadow.align_roll(bone.z_axis)

        dummy_p_bone = arm.pose.bones[dummy_bone_name]
        dummy_p_bone.is_mmd_shadow_bone = True
        dummy_p_bone.mmd_shadow_bone_type = 'DUMMY'

        shadow_p_bone = arm.pose.bones[shadow_bone_name]
        shadow_p_bone.is_mmd_shadow_bone = True
        shadow_p_bone.mmd_shadow_bone_type = 'SHADOW'

        if self.AT_DUMMY_CONSTRAINT_NAME not in shadow_p_bone.constraints:
            c = shadow_p_bone.constraints.new('COPY_TRANSFORMS')
            c.name = self.AT_DUMMY_CONSTRAINT_NAME
            c.target = arm
            c.subtarget = dummy_bone_name
            c.target_space = 'POSE'
            c.owner_space = 'POSE'

        return shadow_bone_name

