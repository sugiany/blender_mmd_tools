# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator

import mmd_tools.core.model as mmd_model

class MoveUpMorph(Operator):
    bl_idname = 'mmd_tools.move_up_morph'
    bl_label = 'Move Up Morph'
    bl_description = ''
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        if mmd_root.active_morph > 0:
            items_map = {"MATMORPH":mmd_root.material_morphs, 
                 "BONEMORPH":mmd_root.bone_morphs, 
                 "VTXMORPH":mmd_root.vertex_morphs} 
            items_map[mmd_root.active_morph_type].move(mmd_root.active_morph, mmd_root.active_morph-1)
            mmd_root.active_morph -= 1
            
        return {'FINISHED'}
    
class MoveDownMorph(Operator):
    bl_idname = 'mmd_tools.move_down_morph'
    bl_label = 'Move Down Morph'
    bl_description = ''
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        items_map = {"MATMORPH":mmd_root.material_morphs, 
                 "BONEMORPH":mmd_root.bone_morphs, 
                 "VTXMORPH":mmd_root.vertex_morphs}
        items = items_map[mmd_root.active_morph_type]
        if mmd_root.active_morph+1 < len(items):             
            items.move(mmd_root.active_morph, mmd_root.active_morph+1)
            mmd_root.active_morph += 1
            
        return {'FINISHED'}
    
class AddVertexMorph(Operator):
    bl_idname = 'mmd_tools.add_vertex_morph'
    bl_label = 'Add Vertex Morph'
    bl_description = ''
    bl_options = {'PRESET'}
    
    name_j = bpy.props.StringProperty(name='Name', default='Morph')
    name_e = bpy.props.StringProperty(name='Name(Eng)', default='Morph_e')
    category = bpy.props.EnumProperty(
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
    
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        category_list = ['SYSTEM', 'EYEBROW', 'EYE', 'MOUTH', 'OTHER']
        if bpy.data.meshes[obj.name].shape_keys is None:
            bpy.ops.object.shape_key_add()
            obj = context.active_object
        obj.shape_key_add(self.name_j)
        idx = len(bpy.data.meshes[obj.name].shape_keys.key_blocks)-1
        obj.active_shape_key_index = idx
        vtx_morph = mmd_root.vertex_morphs.add()
        vtx_morph.name = self.name_j
        vtx_morph.name_e = self.name_e
        vtx_morph.category = category_list.index(self.category)        
        mmd_root.active_morph = len(mmd_root.vertex_morphs)-1
        
        frame = mmd_root.display_item_frames[u'表情']
        item = frame.items.add()
        item.name = vtx_morph.name 
        item.type = 'MORPH'
        item.morph_category = self.category
        
        return { 'FINISHED' }
        
    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)
        
class AddMaterialMorph(Operator):
    bl_idname = 'mmd_tools.add_material_morph'
    bl_label = 'Add Material Morph'
    bl_description = ''
    bl_options = {'PRESET'}
    
    name_j = bpy.props.StringProperty(name='Name', default='Morph')
    name_e = bpy.props.StringProperty(name='Name(Eng)', default='Morph_e')
    category = bpy.props.EnumProperty(
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
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        category_list = ['SYSTEM', 'EYEBROW', 'EYE', 'MOUTH', 'OTHER']
        mat_morph = mmd_root.material_morphs.add()
        mat_morph.name = self.name_j
        mat_morph.name_e = self.name_e
        mat_morph.category = category_list.index(self.category)        
        mmd_root.active_morph = len(mmd_root.material_morphs)-1
        
        frame = mmd_root.display_item_frames[u'表情']
        item = frame.items.add()
        item.name = mat_morph.name 
        item.type = 'MORPH'
        item.morph_category = self.category
        return { 'FINISHED' }
    
    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)
    
class AddBoneMorph(Operator):
    bl_idname = 'mmd_tools.add_bone_morph'
    bl_label = 'Add Bone Morph'
    bl_description = ''
    bl_options = {'PRESET'}
    
    name_j = bpy.props.StringProperty(name='Name', default='Morph')
    name_e = bpy.props.StringProperty(name='Name(Eng)', default='Morph_e')
    category = bpy.props.EnumProperty(
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
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        category_list = ['SYSTEM', 'EYEBROW', 'EYE', 'MOUTH', 'OTHER']
        bone_morph = mmd_root.bone_morphs.add()
        bone_morph.name = self.name_j
        bone_morph.name_e = self.name_e
        bone_morph.category = category_list.index(self.category)        
        mmd_root.active_morph = len(mmd_root.bone_morphs)-1
        
        frame = mmd_root.display_item_frames[u'表情']
        item = frame.items.add()
        item.name = bone_morph.name 
        item.type = 'MORPH'
        item.morph_category = self.category
        return { 'FINISHED' }
    
    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)

class RemoveMorph(Operator):
    bl_idname = 'mmd_tools.remove_morph'
    bl_label = 'Remove Morph'
    bl_description = ''
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        items_map = {"MATMORPH":"material_morphs", 
                 "BONEMORPH":"bone_morphs", 
                 "VTXMORPH":"vertex_morphs"}
        attr_name = items_map[mmd_root.active_morph_type]
        items = getattr(mmd_root, attr_name)
        if mmd_root.active_morph >= 0 and mmd_root.active_morph < len(items):
            active_morph = items[mmd_root.active_morph]
            if attr_name == "vertex_morphs":
                for i, sk in enumerate(bpy.data.meshes[obj.name].shape_keys.key_blocks):
                    if sk.name == active_morph.name:
                        obj.active_shape_key_index = i
                        break
                bpy.ops.object.shape_key_remove()
                
            items.remove(mmd_root.active_morph)
            mmd_root.active_morph -= 1            
            
        return { 'FINISHED' }
    