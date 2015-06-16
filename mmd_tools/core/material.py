# -*- coding: utf-8 -*-

import logging
import os

import bpy

SPHERE_MODE_OFF    = 0
SPHERE_MODE_MULT   = 1
SPHERE_MODE_ADD    = 2
SPHERE_MODE_SUBTEX = 3

class FnMaterial(object):
    BASE_TEX_SLOT = 0
    TOON_TEX_SLOT = 1
    SPHERE_TEX_SLOT = 2

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


    def __load_image(self, filepath):
        for i in bpy.data.images:
            if i.filepath == filepath:
                return i

        try:
            return bpy.data.images.load(filepath)
        except:
            logging.warning('Cannot create a texture for %s. No such file.', filepath)

        img = bpy.data.images.new(os.path.basename(filepath), 1, 1)
        img.source = 'FILE'
        img.filepath = filepath
        return img


    def create_texture(self, filepath):
        """ create a texture slot for textures of MMD models.

        Args:
            material: the material object to add a texture_slot
            filepath: the file path to texture.

        Returns:
            bpy.types.MaterialTextureSlot object
        """
        texture_slot = self.__material.texture_slots.create(self.BASE_TEX_SLOT)
        texture_slot.use_map_alpha = True
        texture_slot.texture_coords = 'UV'
        texture_slot.blend_type = 'MULTIPLY'
        texture_slot.texture = bpy.data.textures.new(name=self.__material.name, type='IMAGE')
        texture_slot.texture.image = self.__load_image(filepath)
        return texture_slot


    def remove_texture(self, index=BASE_TEX_SLOT):
        texture_slot = self.__material.texture_slots[index]
        if texture_slot:
            self.__material.texture_slots.clear(index)
            if texture_slot.texture and texture_slot.texture.users < 1:
                texture_slot.texture.image = None
                bpy.data.textures.remove(texture_slot.texture)


    def create_sphere_texture(self, filepath):
        """ create a texture slot for environment mapping textures of MMD models.

        Args:
            material: the material object to add a texture_slot
            filepath: the file path to environment mapping texture.

        Returns:
            bpy.types.MaterialTextureSlot object
        """
        texture_slot = self.__material.texture_slots.create(self.SPHERE_TEX_SLOT)
        texture_slot.texture_coords = 'NORMAL'
        texture_slot.texture = bpy.data.textures.new(name=self.__material.name + '_sph', type='IMAGE')
        texture_slot.texture.image = self.__load_image(filepath)
        self.update_sphere_texture_type()
        return texture_slot

    def update_sphere_texture_type(self):
        texture_slot = self.__material.texture_slots[self.SPHERE_TEX_SLOT]
        if not texture_slot:
            return
        sphere_texture_type = int(self.__material.mmd_material.sphere_texture_type)
        if sphere_texture_type not in (1, 2, 3):
            texture_slot.use = False
        else:
            texture_slot.use = True
            texture_slot.blend_type = ('MULTIPLY', 'ADD', 'SUBTRACT')[sphere_texture_type-1]

    def remove_sphere_texture(self):
        self.remove_texture(self.SPHERE_TEX_SLOT)


    def create_toon_texture(self, filepath):
        """ create a texture slot for toon textures of MMD models.

        Args:
            material: the material object to add a texture_slot
            filepath: the file path to toon texture.

        Returns:
            bpy.types.MaterialTextureSlot object
        """
        try:
            texture_slot = self.__material.texture_slots[self.TOON_TEX_SLOT]
            if texture_slot.texture.image.filepath != filepath:
                texture_slot.texture.image = self.__load_image(filepath)
                texture_slot.texture.image.use_alpha = False
            return texture_slot
        except:
            pass

        texture_slot = self.__material.texture_slots.create(self.TOON_TEX_SLOT)
        texture_slot.texture_coords = 'NORMAL'
        texture_slot.blend_type = 'MULTIPLY'
        texture_slot.texture = bpy.data.textures.new(name=self.__material.name + '_toon', type='IMAGE')
        texture_slot.texture.image = self.__load_image(filepath)
        texture_slot.texture.image.use_alpha = False
        texture_slot.texture.extension = 'EXTEND'
        return texture_slot

    def remove_toon_texture(self):
        self.remove_texture(self.TOON_TEX_SLOT)

