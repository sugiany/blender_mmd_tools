# -*- coding: utf-8 -*-

from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty, FloatVectorProperty

from mmd_tools.core.bone import FnBone

def _updateMMDBoneAdditionalTransform(prop, context):
    prop['is_additional_transform_dirty'] = True

def _getAdditionalTransformBone(prop):
    arm = prop.id_data
    bone_id = prop.get('additional_transform_bone_id', -1)
    if bone_id < 0:
        return ''
    fnBone = FnBone.from_bone_id(arm, bone_id)
    if not fnBone:
        return ''
    return fnBone.pose_bone.name

def _setAdditionalTransformBone(prop, value):
    arm = prop.id_data
    prop['is_additional_transform_dirty'] = True
    if value not in arm.pose.bones.keys():
        prop['additional_transform_bone_id'] = -1
        return
    pose_bone = arm.pose.bones[value]
    bone = FnBone(pose_bone)
    prop['additional_transform_bone_id'] = bone.bone_id

class MMDBone(PropertyGroup):
    name_j = StringProperty(
        name='Name',
        description='Japanese Name',
        default='',
        )

    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='',
        )

    bone_id = IntProperty(
        name='Bone ID',
        default=-1,
        )

    transform_order = IntProperty(
        name='Transform Order',
        min=0,
        max=100,
        )

    is_visible = BoolProperty(
        name='Visible',
        default=True,
        )

    is_controllable = BoolProperty(
        name='Controllable',
        default=True,
        )

    transform_after_dynamics = BoolProperty(
        name='After Dynamics',
        default=False,
        )

    use_tail_location = BoolProperty(
        name='Use Tail',
        default=False,
        )

    enabled_fixed_axis = BoolProperty(
        name='Fixed Axis',
        default=False,
        )

    fixed_axis = FloatVectorProperty(
        name='Fixed Axis',
        size=3,
        default=[0, 0, 0],
        )

    enabled_local_axes = BoolProperty(
        name='Local Axes',
        default=False,
        )

    local_axis_x = FloatVectorProperty(
        name='Local X-Axis',
        size=3,
        default=[1, 0, 0],
        )

    local_axis_z = FloatVectorProperty(
        name='Local Z-Axis',
        size=3,
        default=[0, 0, 1],
        )

    is_tip = BoolProperty(
        name='Tip Bone',
        default=False,
        )

    has_additional_rotation = BoolProperty(
        name='Additional Rotation',
        default=False,
        update=_updateMMDBoneAdditionalTransform,
        )

    has_additional_location = BoolProperty(
        name='Additional Location',
        default=False,
        update=_updateMMDBoneAdditionalTransform,
        )

    additional_transform_bone = StringProperty(
        name='Additional Transform Bone',
        set=_setAdditionalTransformBone,
        get=_getAdditionalTransformBone
        )

    additional_transform_bone_id = IntProperty(
        name='Additional Transform Bone ID',
        default=-1,
        update=_updateMMDBoneAdditionalTransform,
        )

    additional_transform_influence = FloatProperty(
        name='Additional Transform Influence',
        default=1,
        update=_updateMMDBoneAdditionalTransform,
        )

    is_additional_transform_dirty = BoolProperty(
        name='',
        default=True
        )
