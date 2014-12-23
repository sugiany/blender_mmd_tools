# -*- coding: utf-8 -*-

import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty, FloatVectorProperty


def _updateMMDBoneAdditionalTransform(prop, context):
    prop.is_additional_transform_dirty = True

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

    enabled_local_axes = BoolProperty(
        name='Use Local Axes',
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
        default='',
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
