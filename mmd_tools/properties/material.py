# -*- coding: utf-8 -*-

import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, StringProperty

from mmd_tools.core import material
from mmd_tools.core.material import FnMaterial
from mmd_tools.core.model import Model
from mmd_tools import utils


def _updateAmbientColor(prop, context):
    FnMaterial(prop.id_data).update_ambient_color()

def _updateDiffuseColor(prop, context):
    FnMaterial(prop.id_data).update_diffuse_color()

def _updateAlpha(prop, context):
    FnMaterial(prop.id_data).update_alpha()

def _updateSpecularColor(prop, context):
    FnMaterial(prop.id_data).update_specular_color()

def _updateShininess(prop, context):
    FnMaterial(prop.id_data).update_shininess()

def _updateIsDoubleSided(prop, context):
    FnMaterial(prop.id_data).update_is_double_sided()

def _updateSphereMapType(prop, context):
    FnMaterial(prop.id_data).update_sphere_texture_type()

def _updateToonTexture(prop, context):
    FnMaterial(prop.id_data).update_toon_texture()

def _updateDropShadow(prop, context):
    FnMaterial(prop.id_data).update_drop_shadow()

def _updateSelfShadowMap(prop, context):
    FnMaterial(prop.id_data).update_self_shadow_map()

def _updateSelfShadow(prop, context):
    FnMaterial(prop.id_data).update_self_shadow()

def _updateEnabledToonEdge(prop, context):
    FnMaterial(prop.id_data).update_enabled_toon_edge()

def _updateEdgeColor(prop, context):
    FnMaterial(prop.id_data).update_edge_color()

def _updateEdgeWeight(prop, context):
    FnMaterial(prop.id_data).update_edge_weight()

def _getNameJ(prop):
    return prop.get('name_j', '')

def _setNameJ(prop, value):  
    old_value = prop.get('name_j')  
    prop_value = value
    if prop_value and prop_value != old_value:
        root = Model.findRoot(bpy.context.active_object)
        if root:
            rig = Model(root)
            prop_value = utils.uniqueName(value, [mat.mmd_material.name_j for mat in rig.materials()])
        else:
            prop_value = utils.uniqueName(value, [mat.mmd_material.name_j for mat in bpy.data.materials])

    prop['name_j'] = prop_value

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
        set=_setNameJ,
        get=_getNameJ,
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
        name='Ambient Color',
        subtype='COLOR',
        size=3,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0.4, 0.4, 0.4],
        update=_updateAmbientColor,
        )

    diffuse_color = FloatVectorProperty(
        name='Diffuse Color',
        subtype='COLOR',
        size=3,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0.8, 0.8, 0.8],
        update=_updateDiffuseColor,
        )

    alpha = FloatProperty(
        name='Alpha',
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=1.0,
        update=_updateAlpha,
        )

    specular_color = FloatVectorProperty(
        name='Specular Color',
        subtype='COLOR',
        size=3,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[1.0, 1.0, 1.0],
        update=_updateSpecularColor,
        )

    shininess = FloatProperty(
        name='Shininess',
        min=0,
        soft_max=512,
        step=100.0,
        default=50.0,
        update=_updateShininess,
        )

    is_double_sided = BoolProperty(
        name='Double Sided',
        description='',
        default=True,
        update=_updateIsDoubleSided,
        )

    enabled_drop_shadow = BoolProperty(
        name='Drop Shadow',
        description='',
        default=True,
        update=_updateDropShadow,
        )

    enabled_self_shadow_map = BoolProperty(
        name='Self Shadow Map',
        description='',
        default=True,
        update=_updateSelfShadowMap,
        )

    enabled_self_shadow = BoolProperty(
        name='Self Shadow',
        description='',
        default=True,
        update=_updateSelfShadow,
        )

    enabled_toon_edge = BoolProperty(
        name='Toon Edge',
        description='',
        default=False,
        update=_updateEnabledToonEdge,
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
        update=_updateEdgeColor,
        )

    edge_weight = FloatProperty(
        name='Edge Weight',
        min=0,
        max=100,
        soft_max=2,
        step=1.0,
        default=0.5,
        update=_updateEdgeWeight,
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
        update=_updateSphereMapType,
        )

    is_shared_toon_texture = BoolProperty(
        name='Use Shared Toon Texture',
        description='',
        default=False,
        update=_updateToonTexture,
        )

    toon_texture = StringProperty(
        name='Toon Texture',
        subtype='FILE_PATH',
        description='',
        default='',
        update=_updateToonTexture,
        )

    shared_toon_texture = IntProperty(
        name='Shared Toon Texture',
        description='',
        default=0,
        min=0,
        max=9,
        update=_updateToonTexture,
        )

    comment = StringProperty(
        name='Comment',
        )

