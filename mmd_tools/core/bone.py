# -*- coding: utf-8 -*-

import bpy
from bpy.types import PoseBone
import mathutils

from mmd_tools import bpyutils

class FnBone(object):
    AT_DUMMY_CONSTRAINT_NAME = 'mmd_tools_at_dummy'
    AT_ROTATION_CONSTRAINT_NAME = 'mmd_tools_at_rotation'
    AT_LOCATION_CONSTRAINT_NAME = 'mmd_tools_at_location'
    AT_PARENT_CONSTRAINT = 'mmd_tools_at_parent'

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

    #****************************************
    # Methods for additional transformation
    #****************************************
    def apply_additional_transformation(self):
        """ create or update constaints to apply additional transformation
        """
        mmd_bone = self.__bone.mmd_bone

        influence = mmd_bone.additional_transform_influence
        source_bone = mmd_bone.additional_transform_bone
        mute_rotation = not mmd_bone.has_additional_rotation
        mute_location = not mmd_bone.has_additional_location

        mmd_bone.is_additional_transform_dirty = False

        if not source_bone or (mute_rotation and mute_location):
            self.__remove_constraints()
            return

        rot_constraint, loc_constraint, parent_constraint = self.__create_constraints()

        self.__bone.bone.use_inherit_rotation = False
        shadow_bone = self.__get_at_shadow_bone(source_bone, influence < 0)

        rot_constraint.subtarget = shadow_bone.name
        rot_constraint.influence = abs(influence)
        rot_constraint.inverse_matrix = mathutils.Matrix(shadow_bone.matrix).inverted()

        loc_constraint.subtarget = shadow_bone.name
        loc_constraint.influence = abs(influence)

        rot_constraint.mute = mute_rotation
        loc_constraint.mute = mute_location

    def __get_shadow_bone(self, bone_name, shadow_bone_type):
        arm = self.__bone.id_data
        for p_bone in arm.pose.bones:
            if p_bone.mmd_shadow_bone_type == shadow_bone_type:
                for c in p_bone.constraints:
                    if c.subtarget == bone_name:
                        return p_bone
        return None

    def __get_at_shadow_bone(self, bone_name, invert=False):
        arm = self.__bone.id_data
        mmd_shadow_bone_type = 'ADDITIONAL_TRANSFORM'
        if invert:
            mmd_shadow_bone_type += '_INVERT'

        shadow_bone = self.__get_shadow_bone(bone_name, mmd_shadow_bone_type)
        if shadow_bone:
            return shadow_bone
        with bpyutils.edit_object(arm) as data:
            src_bone = data.edit_bones[bone_name]
            shadow_bone = data.edit_bones.new(name='%s.shadow'%(bone_name))
            shadow_bone.head = mathutils.Vector([0, 0, 0])
            shadow_bone.tail = src_bone.tail - src_bone.head
            shadow_bone.layers = (
                False, False, False, False, False, False, False, False,
                True , False, False, False, False, False, False, False,
                False, False, False, False, False, False, False, False,
                False, False, False, False, False, False, False, False)
            shadow_bone_name = shadow_bone.name

        shadow_p_bone = arm.pose.bones[shadow_bone_name]
        shadow_p_bone.is_mmd_shadow_bone = True
        shadow_p_bone.mmd_shadow_bone_type = mmd_shadow_bone_type

        c = shadow_p_bone.constraints.new('COPY_ROTATION')
        c.target = arm
        c.subtarget = bone_name
        c.target_space = 'LOCAL'
        c.owner_space = 'LOCAL'
        if invert:
            c.invert_x = True
            c.invert_y = True
            c.invert_z = True

        c = shadow_p_bone.constraints.new('COPY_LOCATION')
        c.target = arm
        c.subtarget = bone_name
        c.target_space = 'LOCAL'
        c.owner_space = 'LOCAL'
        if invert:
            c.invert_x = True
            c.invert_y = True
            c.invert_z = True

        return shadow_p_bone

    def __get_at_constraints(self):
        rot_constraint = None
        loc_constraint = None
        parent_constraint = None
        for c in self.__bone.constraints:
            if c.name == self.AT_ROTATION_CONSTRAINT_NAME:
                rot_constraint = c
            elif c.name == self.AT_LOCATION_CONSTRAINT_NAME:
                loc_constraint = c
            elif c.name == self.AT_PARENT_CONSTRAINT:
                parent_constraint = c
        return (rot_constraint, loc_constraint, parent_constraint)

    def __remove_constraints(self):
        rot_constraint, loc_constraint, parent_constraint = self.__get_at_constraints()
        if rot_constraint:
            self.__bone.constraints.remove(rot_constraint)
        if loc_constraint:
            self.__bone.constraints.remove(loc_constraint)
        if parent_constraint:
            self.__bone.constraints.remove(parent_constraint)
        self.__bone.bone.use_inherit_rotation = True

    def __create_constraints(self):
        arm = self.__bone.id_data
        rot_constraint, loc_constraint, parent_constraint = self.__get_at_constraints()
        if rot_constraint and loc_constraint:
            return (rot_constraint, loc_constraint, parent_constraint)

        if rot_constraint:
            self.__bone.constraints.remove(rot_constraint)

        if loc_constraint:
            self.__bone.constraints.remove(loc_constraint)

        if parent_constraint:
            self.__bone.constraints.remove(parent_constraint)

        rot_constraint = self.__bone.constraints.new('CHILD_OF')
        rot_constraint.mute = True
        rot_constraint.name = 'mmd_additional_rotation'
        rot_constraint.target = arm
        rot_constraint.use_location_x = False
        rot_constraint.use_location_y = False
        rot_constraint.use_location_z = False
        rot_constraint.use_rotation_x = True
        rot_constraint.use_rotation_y = True
        rot_constraint.use_rotation_z = True
        rot_constraint.use_scale_x = False
        rot_constraint.use_scale_y = False
        rot_constraint.use_scale_z = False

        loc_constraint = self.__bone.constraints.new('CHILD_OF')
        loc_constraint.mute = True
        loc_constraint.name = 'mmd_additional_location'
        loc_constraint.target = arm
        loc_constraint.use_location_x = True
        loc_constraint.use_location_y = True
        loc_constraint.use_location_z = True
        loc_constraint.use_rotation_x = False
        loc_constraint.use_rotation_y = False
        loc_constraint.use_rotation_z = False
        loc_constraint.use_scale_x = False
        loc_constraint.use_scale_y = False
        loc_constraint.use_scale_z = False

        parent_constraint = None
        if self.__bone.parent:
            parent_constraint = self.__bone.constraints.new('CHILD_OF')
            parent_constraint.mute = False
            parent_constraint.name = 'mmd_additional_parent'
            parent_constraint.target = arm
            parent_constraint.subtarget = self.__bone.parent.name
            parent_constraint.use_location_x = False
            parent_constraint.use_location_y = False
            parent_constraint.use_location_z = False
            parent_constraint.use_rotation_x = True
            parent_constraint.use_rotation_y = True
            parent_constraint.use_rotation_z = True
            parent_constraint.use_scale_x = False
            parent_constraint.use_scale_y = False
            parent_constraint.use_scale_z = False
            parent_constraint.inverse_matrix = mathutils.Matrix(self.__bone.parent.matrix).inverted()

        return (rot_constraint, loc_constraint, parent_constraint)
