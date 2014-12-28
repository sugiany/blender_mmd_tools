# -*- coding: utf-8 -*-

import bpy

SPHERE_MODE_OFF    = 0
SPHERE_MODE_MULT   = 1
SPHERE_MODE_ADD    = 2
SPHERE_MODE_SUBTEX = 3

def create_texture(material, filepath):
    """ create a texture slot for textures of MMD models.

    Args:
        material: the material object to add a texture_slot
        filepath: the file path to texture.

    Returns:
        bpy.types.MaterialTextureSlot object
    """
    texture_slot = material.texture_slots.create(0)
    texture_slot.use_map_alpha = True
    texture_slot.texture_coords = 'UV'
    texture_slot.blend_type = 'MULTIPLY'
    texture_slot.texture = bpy.data.textures.new(name=material.name, type='IMAGE')
    texture_slot.texture.image = bpy.data.images.load(filepath)
    return texture_slot


def remove_texture(material):
    material.texture_slots.clear(0)


def create_sphere_texture(material, filepath):
    """ create a texture slot for environment mapping textures of MMD models.

    Args:
        material: the material object to add a texture_slot
        filepath: the file path to environment mapping texture.

    Returns:
        bpy.types.MaterialTextureSlot object
    """
    texture_slot = material.texture_slots.create(1)
    texture_slot.texture_coords = 'NORMAL'
    texture_slot.texture = bpy.data.textures.new(name=material.name + '_sph', type='IMAGE')
    texture_slot.texture.image = bpy.data.images.load(filepath)
    return texture_slot


def remove_sphere_texture(material):
    material.texture_slots.clear(1)
