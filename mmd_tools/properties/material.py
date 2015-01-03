# -*- coding: utf-8 -*-

import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, StringProperty

from mmd_tools.core import material

#===========================================
# Property classes
#===========================================
class MMDMaterial(PropertyGroup):
    """ マテリアル
    """
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

    material_id = IntProperty(
        name='Material ID',
        default=-1
        )

    ambient_color = FloatVectorProperty(
        name='Ambient',
        subtype='COLOR',
        size=3,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0],
        )

    is_double_sided = BoolProperty(
        name='Double Sided',
        description='',
        default=True,
        )

    enabled_drop_shadow = BoolProperty(
        name='Drop Shadow',
        description='',
        default=True,
        )

    enabled_self_shadow_map = BoolProperty(
        name='Self Shadow Map',
        description='',
        default=True,
        )

    enabled_self_shadow = BoolProperty(
        name='Self Shadow',
        description='',
        default=True,
        )

    enabled_toon_edge = BoolProperty(
        name='Toon Edge',
        description='',
        default=True,
        )

    edge_color = FloatVectorProperty(
        name='Edge Color',
        subtype='COLOR',
        size=4,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0, 1],
        )

    edge_weight = FloatProperty(
        name='Edge Weight',
        min=0,
        max=100,
        step=0.1,
        default=0.5,
        )

    sphere_texture_type = EnumProperty(
        name='Sphere Map Type',
        description='',
        items = [
            (str(material.SPHERE_MODE_OFF),    'Off',        '', 1),
            (str(material.SPHERE_MODE_MULT),   'Multiply',   '', 2),
            (str(material.SPHERE_MODE_ADD),    'Add',        '', 3),
            (str(material.SPHERE_MODE_SUBTEX), 'SubTexture', '', 4),
            ],
        )

    is_shared_toon_texture = BoolProperty(
        name='Use Shared Toon Texture',
        description='',
        default=False,
        )

    toon_texture = StringProperty(
        name='Toon Texture',
        subtype='FILE_PATH',
        description='',
        default='',
        )

    shared_toon_texture = IntProperty(
        name='Shared Toon Texture',
        description='',
        default=0,
        )

    comment = StringProperty(
        name='Comment',
        )

