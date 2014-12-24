# -*- coding: utf-8 -*-

from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolVectorProperty, EnumProperty, FloatVectorProperty

from mmd_tools.core import rigid_body

class MMDRigidBody(PropertyGroup):
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

    collision_group_number = IntProperty(
        name='Collision Group',
        min=0,
        max=16,
        default=1,
        )

    collision_group_mask = BoolVectorProperty(
        name='Collision Group Mask',
        size=16,
        subtype='LAYER',
        )

    type = EnumProperty(
        name='Rigid Type',
        items = [
            (str(rigid_body.MODE_STATIC), 'Static', '', 1),
            (str(rigid_body.MODE_DYNAMIC), 'Dynamic', '', 2),
            (str(rigid_body.MODE_DYNAMIC_BONE), 'Dynamic&BoneTrack', '', 3),
            ],
        )

    shape = EnumProperty(
        name='Shape',
        items = [
            ('SPHERE', 'Sphere', '', 1),
            ('BOX', 'Box', '', 2),
            ('CAPSULE', 'Capsule', '', 3),
            ],
        )

    bone = StringProperty(
        name='Bone',
        description='',
        default='',
        )

class MMDJoint(PropertyGroup):
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

    spring_linear = FloatVectorProperty(
        name='Spring(Linear)',
        size=3,
        min=0,
        step=0.1,
        )

    spring_angular = FloatVectorProperty(
        name='Spring(Angular)',
        size=3,
        min=0,
        step=0.1,
        )
