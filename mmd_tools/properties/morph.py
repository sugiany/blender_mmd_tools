# -*- coding: utf-8 -*-

import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from bpy.props import IntProperty
from bpy.props import FloatVectorProperty
from bpy.props import FloatProperty
from bpy.props import CollectionProperty
from bpy.props import EnumProperty

from mmd_tools.core.model import Model as FnModel
from mmd_tools.core.bone import FnBone
from mmd_tools.core.material import FnMaterial


def _get_bone(prop):
    bone_id = prop.get('bone_id', -1)
    if bone_id < 0:
        return ''
    root = prop.id_data
    fnModel = FnModel(root)
    arm = fnModel.armature()
    fnBone = FnBone.from_bone_id(arm, bone_id)
    if not fnBone:
        return ''
    return fnBone.pose_bone.name

def _set_bone(prop, value):
    root = prop.id_data
    fnModel = FnModel(root)
    arm = fnModel.armature()
    if value not in arm.pose.bones.keys():
        prop['bone_id'] = -1
        return
    pose_bone = arm.pose.bones[value]
    fnBone = FnBone(pose_bone)
    prop['bone_id'] = fnBone.bone_id
    
class BoneMorphData(PropertyGroup):
    """
    """
    bone = StringProperty(
        name='Bone',
        set=_set_bone,
        get=_get_bone,
        )

    bone_id = IntProperty(
        name='Bone ID',
        )

    location = FloatVectorProperty(
        name='Location',
        subtype='TRANSLATION',
        size=3,
        )

    rotation = FloatVectorProperty(
        name='Rotation',
        subtype='QUATERNION',
        size=4,
        )

class BoneMorph(PropertyGroup):
    """Bone Morph
    """
    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='',
        )

    category = EnumProperty(
        name='Category',
        items = [
            ('SYSTEM', 'System', '', 0),
            ('EYEBROW', 'Eye Brow', '', 1),
            ('EYE', 'Eye', '', 2),
            ('MOUTH', 'Mouth', '', 3),
            ('OTHER', 'Other', '', 4),
            ],
        default='OTHER',
        )

    data = CollectionProperty(
        name='Morph Data',
        type=BoneMorphData,
        )
    active_bone_data = IntProperty(
        name='Active Bone Data',
        default=0,
        )

def _get_material(prop):
    mat_id = prop.get('material_id')
    if mat_id < 0:
        return ''
    fnMat = FnMaterial.from_material_id(mat_id)
    if not fnMat:
        return ''
    return fnMat.material.name

def _set_material(prop, value):
    if value not in bpy.data.materials.keys():
        prop['material_id'] = -1
        return
    mat = bpy.data.materials[value]
    fnMat = FnMaterial(mat)
    prop['material_id'] = fnMat.material_id

    
class MaterialMorphData(PropertyGroup):
    """
    """
    offset_type = EnumProperty(
        name='Offset Type',
        items=[
            ('MULT', 'Multiply', '', 0),
            ('ADD', 'Add', '', 1)
            ],
        default='ADD'
        )
    material = StringProperty(
        name='Material',
        get=_get_material,
        set=_set_material,
        )

    material_id = IntProperty(
        name='Material ID',
        )

    diffuse_color = FloatVectorProperty(
        name='Diffuse Color',
        subtype='COLOR',
        size=4,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0, 1],
        )

    specular_color = FloatVectorProperty(
        name='Specular Color',
        subtype='COLOR',
        size=4,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0, 1],
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
        default=0,
        )

    texture_factor = FloatVectorProperty(
        name='Texture factor',
        subtype='COLOR',
        size=4,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0, 1],
        )

    sphere_texture_factor = FloatVectorProperty(
        name='Sphere Texture factor',
        subtype='COLOR',
        size=4,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0, 1],
        )
    
    toon_texture_factor = FloatVectorProperty(
        name='Toon Texture factor',
        subtype='COLOR',
        size=4,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0, 1],
        )

class MaterialMorph(PropertyGroup):
    """ Material Morph
    """
    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='',
        )

    category = EnumProperty(
        name='Category',
        items = [
            ('SYSTEM', 'System', '', 0),
            ('EYEBROW', 'Eye Brow', '', 1),
            ('EYE', 'Eye', '', 2),
            ('MOUTH', 'Mouth', '', 3),
            ('OTHER', 'Other', '', 4),
            ],
        default='OTHER',
        )

    data = CollectionProperty(
        name='Morph Data',
        type=MaterialMorphData,
        )
    active_material_data = IntProperty(
        name='Active Material Data',
        default=0,
        )
class VertexMorph(PropertyGroup):
    """Vertex Morph
    """
    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default=''        
        )
    category = EnumProperty(
        name='Category',
        items = [
            ('SYSTEM', 'System', '', 0),
            ('EYEBROW', 'Eye Brow', '', 1),
            ('EYE', 'Eye', '', 2),
            ('MOUTH', 'Mouth', '', 3),
            ('OTHER', 'Other', '', 4),
            ],
        default='OTHER',
        )
