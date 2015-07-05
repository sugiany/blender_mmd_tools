# -*- coding: utf-8 -*-

import bpy
from mmd_tools import bpyutils
from bpy.types import Operator
from mathutils import Vector

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
        with bpyutils.select_object(obj) as data:     
            if bpy.data.meshes[obj.name].shape_keys is None:
                bpy.ops.object.shape_key_add()                
            data.shape_key_add(self.name_j)
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
    
class AddMaterialOffset(Operator):
    bl_idname = 'mmd_tools.add_material_morph_offset'
    bl_label = 'Add Material Offset'
    bl_description = ''
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        # Let's create a temporary material to edit the offset
        orig_mat = obj.active_material
        if "_temp" in orig_mat.name:
            self.report({ 'ERROR' }, 'This material is not valid as a base material')
            return { 'CANCELLED' }
        if orig_mat.name+"_temp" in obj.data.materials.keys():
            self.report({ 'ERROR' }, 'Another offset is using this Material, apply it first')
            return { 'CANCELLED' }                    
        copy_mat = orig_mat.copy()
        copy_mat.name = orig_mat.name+"_temp"
        obj.data.materials.append(copy_mat)
        orig_idx = obj.active_material_index
        copy_idx = obj.data.materials.find(copy_mat.name)
        
        for poly in obj.data.polygons:
            if poly.material_index == orig_idx:
                poly.material_index = copy_idx
            
        morph = mmd_root.material_morphs[mmd_root.active_morph]
        mat_data = morph.data.add()
        mat_data.material = orig_mat.name
        return { 'FINISHED' }
    
class RemoveMaterialOffset(Operator):
    bl_idname = 'mmd_tools.remove_material_morph_offset'
    bl_label = 'Remove Material Offset'
    bl_description = ''
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        morph = mmd_root.material_morphs[mmd_root.active_morph]
        mat_data = morph.data[morph.active_material_data]
        base_mat = obj.data.materials[mat_data.material]
        work_mat_name = base_mat.name+"_temp"
        if work_mat_name in obj.data.materials.keys():
            work_mat = obj.data.materials[work_mat_name]
            base_idx = obj.data.materials.find(base_mat.name)
            copy_idx = obj.data.materials.find(work_mat.name)
            
            for poly in obj.data.polygons:
                if poly.material_index == copy_idx:
                    poly.material_index = base_idx
            
            mat = obj.data.materials.pop(index=copy_idx)
            bpy.data.materials.remove(mat)
        morph.data.remove(morph.active_material_data)
        morph.active_material_data -= 1
        return { 'FINISHED' }
        
class ApplyMaterialOffset(Operator):
    bl_idname = 'mmd_tools.apply_material_morph_offset'
    bl_label = 'Apply Material Offset'
    bl_description = 'Calculates the offsets and apply them, then the temporary material is removed'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        morph = mmd_root.material_morphs[mmd_root.active_morph]
        mat_data = morph.data[morph.active_material_data]
        base_mat = obj.data.materials[mat_data.material]
        work_mat = obj.data.materials[base_mat.name+"_temp"]
        base_idx = obj.data.materials.find(base_mat.name)
        copy_idx = obj.data.materials.find(work_mat.name)
        
        for poly in obj.data.polygons:
            if poly.material_index == copy_idx:
                poly.material_index = base_idx
                
        diffuse_offset = list(work_mat.diffuse_color - base_mat.diffuse_color) + [work_mat.alpha - base_mat.alpha]
        specular_offset = list(work_mat.specular_color - base_mat.specular_color) + [work_mat.specular_alpha - base_mat.specular_alpha]
        edge_offset = Vector(work_mat.mmd_material.edge_color) - Vector(base_mat.mmd_material.edge_color)
        mat_data.diffuse_color = diffuse_offset
        mat_data.specular_color = specular_offset
        mat_data.ambient_color = work_mat.mmd_material.ambient_color - base_mat.mmd_material.ambient_color
        mat_data.edge_color = list(edge_offset)
        mat_data.edge_weight = work_mat.mmd_material.edge_weight - base_mat.mmd_material.edge_weight
        
        mat = obj.data.materials.pop(index=copy_idx)
        bpy.data.materials.remove(mat)
        return { 'FINISHED' }
    
class CreateWorkMaterial(Operator):
    bl_idname = 'mmd_tools.create_work_material'
    bl_label = 'Create Work Material'
    bl_description = 'Creates a temporary material to edit this offset'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        morph = mmd_root.material_morphs[mmd_root.active_morph]
        mat_data = morph.data[morph.active_material_data]
        if mat_data.offset_type == "MULT":
            self.report({ 'ERROR' }, 'Multiply offset type is not supported yet')
            return { 'CANCELLED' }
        base_mat = obj.data.materials[mat_data.material]
        work_mat = base_mat.copy()
        work_mat.name = base_mat.name+"_temp"     
        obj.data.materials.append(work_mat)   
        base_idx = obj.data.materials.find(base_mat.name)
        copy_idx = obj.data.materials.find(work_mat.name)
                
        for poly in obj.data.polygons:
            if poly.material_index == base_idx:
                poly.material_index = copy_idx
                
        # Apply the offsets
        diffuse_offset = Vector(base_mat.diffuse_color) + Vector(mat_data.diffuse_color[0:3])
        specular_offset = Vector(base_mat.specular_color) + Vector(mat_data.specular_color[0:3])
        edge_offset = Vector(base_mat.mmd_material.edge_color) + Vector(mat_data.edge_color)
        ambient_offset = Vector(base_mat.mmd_material.ambient_color) + Vector(mat_data.ambient_color)
        work_mat.diffuse_color = list(diffuse_offset)
        work_mat.alpha += mat_data.diffuse_color[3]
        work_mat.specular_color = list(specular_offset)
        work_mat.specular_alpha += mat_data.specular_color[3]
        work_mat.mmd_material.ambient_color = list(ambient_offset)
        work_mat.mmd_material.edge_color = list(edge_offset)
        work_mat.mmd_material.edge_weight += mat_data.edge_weight
        
        return { 'FINISHED' }
class ClearTempMaterials(Operator):
    bl_idname = 'mmd_tools.clear_temp_materials'
    bl_label = 'Clear Temp Materials'
    bl_description = 'Clears all the temporary materials'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        mats_to_delete = []
        for mat in obj.data.materials:
            if "_temp" in mat.name:
                mats_to_delete.append(mat)
        for temp_mat in mats_to_delete:            
            base_mat_name=temp_mat.name[0:-1*len("_temp")]
            base_idx = obj.data.materials.find(base_mat_name)
            temp_idx = obj.data.materials.find(temp_mat.name)
            for poly in obj.data.polygons:
                if poly.material_index == temp_idx:
                    if base_idx == -1:
                        self.report({ 'ERROR' } ,'Warning! base material for %s was not found'%temp_mat.name)
                    else:
                        poly.material_index = base_idx
            if base_idx != -1:
                mat = obj.data.materials.pop(index=temp_idx)
                bpy.data.materials.remove(mat)
                
        return { 'FINISHED' }
    
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
                
            facial_frame = mmd_root.display_item_frames[u'表情']
            idx = facial_frame.items.find(active_morph.name)  
            if facial_frame.active_item == idx:
                facial_frame.active_item -= 1
            facial_frame.items.remove(idx) 
            items.remove(mmd_root.active_morph)
            mmd_root.active_morph -= 1     
                
            
        return { 'FINISHED' }
    