# -*- coding: utf-8 -*-

import logging
import os

import bpy

SPHERE_MODE_OFF    = 0
SPHERE_MODE_MULT   = 1
SPHERE_MODE_ADD    = 2
SPHERE_MODE_SUBTEX = 3

class FnMaterial(object):
    def __init__(self, material=None):
        self.__material = material

    @classmethod
    def from_material_id(cls, material_id):
        for material in bpy.data.materials:
            if material.mmd_material.material_id == material_id:
                return cls(material)
        return None

    @property
    def material_id(self):
        mmd_mat = self.__material.mmd_material
        if mmd_mat.material_id < 0:
            max_id = -1
            for mat in bpy.data.materials:
                max_id = max(max_id, mat.mmd_material.material_id)
            mmd_mat.material_id = max_id + 1
        return mmd_mat.material_id

    @property
    def material(self):
        return self.__material

    def create_texture(self, filepath):
        """ create a texture slot for textures of MMD models.

        Args:
            material: the material object to add a texture_slot
            filepath: the file path to texture.

        Returns:
            bpy.types.MaterialTextureSlot object
        """
        texture_slot = self.__material.texture_slots.create(0)
        texture_slot.use_map_alpha = True
        texture_slot.texture_coords = 'UV'
        texture_slot.blend_type = 'MULTIPLY'
        texture_slot.texture = bpy.data.textures.new(name=self.__material.name, type='IMAGE')
        if os.path.isfile(filepath):
            texture_slot.texture.image = bpy.data.images.load(filepath)
        else:
            logging.warning('Cannot create a texture for %s. No such file.', filepath)
        return texture_slot


    def remove_texture(self):
        self.__material.texture_slots.clear(0)


    def create_sphere_texture(self, filepath):
        """ create a texture slot for environment mapping textures of MMD models.

        Args:
            material: the material object to add a texture_slot
            filepath: the file path to environment mapping texture.

        Returns:
            bpy.types.MaterialTextureSlot object
        """
        texture_slot = self.__material.texture_slots.create(1)
        texture_slot.texture_coords = 'NORMAL'
        texture_slot.texture = bpy.data.textures.new(name=self.__material.name + '_sph', type='IMAGE')
        if os.path.isfile(filepath):
            texture_slot.texture.image = bpy.data.images.load(filepath)
        else:
            logging.warning('Cannot create a texture for %s. No such file.', filepath)
        return texture_slot


    def remove_sphere_texture(self):
        self.__material.texture_slots.clear(1)
