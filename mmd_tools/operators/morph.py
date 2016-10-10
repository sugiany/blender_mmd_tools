# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
from mathutils import Vector, Quaternion

import mmd_tools.core.model as mmd_model
from mmd_tools import bpyutils
from mmd_tools.core.material import FnMaterial
from mmd_tools.core.exceptions import MaterialNotFoundError, DivisionError
from mmd_tools import utils

#Util functions
def divide_vector_components(vec1, vec2):
    if len(vec1) != len(vec2):
        raise ValueError("Vectors should have the same number of components")
    result = []
    for v1, v2 in zip(vec1, vec2):
        if v2 == 0:
            if v1 == 0:
                v2 = 1 #If we have a 0/0 case we change the divisor to 1
            else:
                raise DivisionError("Invalid Input: a non-zero value can't be divided by zero")
        result.append(v1/v2)
    return result

def multiply_vector_components(vec1, vec2):
    if len(vec1) != len(vec2):
        raise ValueError("Vectors should have the same number of components")
    result = []
    for v1, v2 in zip(vec1, vec2):
        result.append(v1*v2)
    return result

def special_division(n1, n2):
    """This function returns 0 in case of 0/0. If non-zero divided by zero case is found, an Exception is raised
    """
    if n2 == 0:
        if n1 == 0:
            n2 = 1
        else:
            raise DivisionError("Invalid Input: a non-zero value can't be divided by zero")
    return n1/n2

class _AddMorphBase(object):
    name_j = bpy.props.StringProperty(
        name='Name',
        description='Japanese Name',
        default='Morph',
        )
    name_e = bpy.props.StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='Morph_e',
        )
    category = bpy.props.EnumProperty(
        name='Category',
        description='Select category',
        items = [
            ('SYSTEM', 'Hidden', '', 0),
            ('EYEBROW', 'Eye Brow', '', 1),
            ('EYE', 'Eye', '', 2),
            ('MOUTH', 'Mouth', '', 3),
            ('OTHER', 'Other', '', 4),
            ],
        default='OTHER',
        )

    def _addMorph(self, mmd_root):
        #morph_type = mmd_root.active_morph_type
        morph_type = '%ss'%self.bl_rna.identifier[17:]
        #assert(self.bl_rna.identifier.startswith('MMD_TOOLS_OT_add_'))
        #print('_addMorph:', self.bl_rna.identifier, morph_type)

        morphs = getattr(mmd_root, morph_type)
        m = morphs.add()
        m.name = self.name_j
        m.name_e = self.name_e
        m.category = self.category
        if morph_type == mmd_root.active_morph_type:
            mmd_root.active_morph = len(morphs)-1
        self.name_j = m.name # remember current name

        frame = mmd_root.display_item_frames[u'表情']
        items = frame.items
        i = items.add()
        i.type = 'MORPH'
        i.name = m.name
        i.morph_type = morph_type
        frame.active_item = len(items)-1
        return m

    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)

class MoveUpMorph(Operator):
    bl_idname = 'mmd_tools.move_up_morph'
    bl_label = 'Move Up Morph'
    bl_description = 'Move active morph item up in the list'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        if mmd_root.active_morph > 0:
            getattr(mmd_root, mmd_root.active_morph_type).move(mmd_root.active_morph, mmd_root.active_morph-1)
            mmd_root.active_morph -= 1
            
        return {'FINISHED'}
    
class MoveDownMorph(Operator):
    bl_idname = 'mmd_tools.move_down_morph'
    bl_label = 'Move Down Morph'
    bl_description = 'Move active morph item down in the list'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        items = getattr(mmd_root, mmd_root.active_morph_type)
        if mmd_root.active_morph+1 < len(items):             
            items.move(mmd_root.active_morph, mmd_root.active_morph+1)
            mmd_root.active_morph += 1
            
        return {'FINISHED'}

class AddVertexMorph(Operator, _AddMorphBase):
    bl_idname = 'mmd_tools.add_vertex_morph'
    bl_label = 'Add Vertex Morph'
    bl_description = 'Add a vertex morph item, and a shape key to the mesh (a "Exp" display item will be added automatically)'
    bl_options = {'PRESET'}

    #XXX Fix for draw order
    name_j = _AddMorphBase.name_j
    name_e = _AddMorphBase.name_e
    category = _AddMorphBase.category
    on_active_mesh = bpy.props.BoolProperty(name='On Active Mesh', default=False,
                                            description='This will create a shape key on the active mesh') 

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root
        meshObj = None
        if self.on_active_mesh:
            if obj.type == 'MESH' and obj.mmd_type == 'NONE':
                meshObj = obj
            else:
                self.report({ 'ERROR' }, "The active object is not a valid mesh")
                return { 'CANCELLED' }

        meshObj = meshObj or rig.firstMesh()        
        if meshObj is None:
            self.report({ 'ERROR' }, "The model mesh can't be found")
            return { 'CANCELLED' }
        with bpyutils.select_object(meshObj) as data:     
            if meshObj.data.shape_keys is None:
                bpy.ops.object.shape_key_add()                
            data.shape_key_add(self.name_j)
        idx = len(meshObj.data.shape_keys.key_blocks)-1
        meshObj.active_shape_key_index = idx
        self.name_j = meshObj.active_shape_key.name
        self._addMorph(mmd_root)
        meshObj.active_shape_key.name = self.name_j
        return { 'FINISHED' }

class AddMaterialMorph(Operator, _AddMorphBase):
    bl_idname = 'mmd_tools.add_material_morph'
    bl_label = 'Add Material Morph'
    bl_description = 'Add a material morph item to the list (a "Exp" display item will be added automatically)'
    bl_options = {'PRESET'}

    #XXX Fix for draw order
    name_j = _AddMorphBase.name_j
    name_e = _AddMorphBase.name_e
    category = _AddMorphBase.category

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        self._addMorph(mmd_root)
        return { 'FINISHED' }

class AddMaterialOffset(Operator):
    bl_idname = 'mmd_tools.add_material_morph_offset'
    bl_label = 'Add Material Offset'
    bl_description = 'Add a material offset item to the list'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        return mmd_model.Model.findRoot(context.active_object)

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root
        meshObj = rig.firstMesh()
        # if mmd_root.advanced_mode:
        if obj.type == 'MESH' and obj.mmd_type == 'NONE':
            meshObj = obj
        else:
            self.report({ 'WARNING' }, "The active object is not a valid mesh. The first mesh was used instead")

        # Let's create a temporary material to edit the offset
        orig_mat = meshObj.active_material
        if orig_mat is None or "_temp" in orig_mat.name:
            self.report({ 'ERROR' }, 'This material is not valid as a base material')
            return { 'CANCELLED' }
        if orig_mat.name+"_temp" in meshObj.data.materials.keys():
            self.report({ 'ERROR' }, 'Another offset is using this Material, apply it first')
            return { 'CANCELLED' }
        copy_mat = orig_mat.copy()
        copy_mat.name = orig_mat.name+"_temp"
        meshObj.data.materials.append(copy_mat)
        FnMaterial.swap_materials(meshObj, orig_mat.name, copy_mat.name)
        morph = mmd_root.material_morphs[mmd_root.active_morph]
        mat_data = morph.data.add()
        mat_data.related_mesh = meshObj.data.name
        mat_data.material = orig_mat.name
        morph.active_material_data = len(morph.data)-1
        mmd_root.editing_morphs += 1
        return { 'FINISHED' }
    
class RemoveMaterialOffset(Operator):
    bl_idname = 'mmd_tools.remove_material_morph_offset'
    bl_label = 'Remove Material Offset'
    bl_description = 'Remove active material offset item from the list'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        return mmd_model.Model.findRoot(context.active_object)

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root

        morph = mmd_root.material_morphs[mmd_root.active_morph]
        if len(morph.data) == 0:
            return { 'FINISHED' }
        mat_data = morph.data[morph.active_material_data]
        meshObj = rig.findMesh(mat_data.related_mesh)
        if meshObj is None:
            self.report({ 'ERROR' }, "The model mesh can't be found")
            return { 'CANCELLED' }

        work_mat_name = mat_data.material+"_temp"
        base_mat = None
        try:
            copy_mat, base_mat = FnMaterial.swap_materials(meshObj, work_mat_name,
                                                           mat_data.material)
        except MaterialNotFoundError:
            # if the temp material is not found it can be safely ignored
            # if the base material is not found we should report it
            if base_mat is None:
                self.report({ 'WARNING' }, 'Material not found')
        else:
            # Only remove the temp material if it has been successfully replaced with the base
            copy_idx = meshObj.data.materials.find(copy_mat.name)
            mat = meshObj.data.materials.pop(index=copy_idx)
            bpy.data.materials.remove(mat)

        morph.data.remove(morph.active_material_data)
        morph.active_material_data = max(0, morph.active_material_data-1)
        mmd_root.editing_morphs -= 1

        return { 'FINISHED' }
        
class ApplyMaterialOffset(Operator):
    bl_idname = 'mmd_tools.apply_material_morph_offset'
    bl_label = 'Apply Material Offset'
    bl_description = 'Calculates the offsets and apply them, then the temporary material is removed'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        return mmd_model.Model.findRoot(context.active_object)

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root
        morph = mmd_root.material_morphs[mmd_root.active_morph]
        mat_data = morph.data[morph.active_material_data]

        meshObj = rig.findMesh(mat_data.related_mesh)
        if meshObj is None:
            self.report({ 'ERROR' }, "The model mesh can't be found")
            return { 'CANCELLED' }
        try:
            work_mat_name = mat_data.material + '_temp'
            work_mat, base_mat = FnMaterial.swap_materials(meshObj, work_mat_name,
                                                           mat_data.material)
        except MaterialNotFoundError:
            self.report({ 'ERROR' }, "Material not found")
            return { 'CANCELLED' }

        copy_idx = meshObj.data.materials.find(work_mat.name)
        base_mmd_mat = base_mat.mmd_material
        work_mmd_mat = work_mat.mmd_material

        if mat_data.offset_type == "MULT":
                
            try:
                diffuse_offset = divide_vector_components(work_mmd_mat.diffuse_color, base_mmd_mat.diffuse_color) + [special_division(work_mmd_mat.alpha, base_mmd_mat.alpha)]
                specular_offset = divide_vector_components(work_mmd_mat.specular_color, base_mmd_mat.specular_color)
                edge_offset = divide_vector_components(work_mmd_mat.edge_color, base_mmd_mat.edge_color)
                mat_data.diffuse_color = diffuse_offset
                mat_data.specular_color = specular_offset
                mat_data.shininess = special_division(work_mmd_mat.shininess, base_mmd_mat.shininess)
                mat_data.ambient_color = divide_vector_components(work_mmd_mat.ambient_color, base_mmd_mat.ambient_color)
                mat_data.edge_color = edge_offset
                mat_data.edge_weight = special_division(work_mmd_mat.edge_weight, base_mmd_mat.edge_weight)

            except DivisionError:
                mat_data.offset_type = "ADD" # If there is any 0 division we automatically switch it to type ADD
            except ValueError:
                self.report({ 'ERROR' }, 'An unexpected error happened')
                # We should stop on our tracks and re-raise the exception
                raise

        if mat_data.offset_type =="ADD":        
            diffuse_offset = list(work_mmd_mat.diffuse_color - base_mmd_mat.diffuse_color) + [work_mmd_mat.alpha - base_mmd_mat.alpha]
            specular_offset = list(work_mmd_mat.specular_color - base_mmd_mat.specular_color)
            edge_offset = Vector(work_mmd_mat.edge_color) - Vector(base_mmd_mat.edge_color)
            mat_data.diffuse_color = diffuse_offset
            mat_data.specular_color = specular_offset
            mat_data.shininess = work_mmd_mat.shininess - base_mmd_mat.shininess
            mat_data.ambient_color = work_mmd_mat.ambient_color - base_mmd_mat.ambient_color
            mat_data.edge_color = list(edge_offset)
            mat_data.edge_weight = work_mmd_mat.edge_weight - base_mmd_mat.edge_weight

        mat = meshObj.data.materials.pop(index=copy_idx)
        bpy.data.materials.remove(mat)
        mmd_root.editing_morphs -= 1
        return { 'FINISHED' }
    
class CreateWorkMaterial(Operator):
    bl_idname = 'mmd_tools.create_work_material'
    bl_label = 'Create Work Material'
    bl_description = 'Creates a temporary material to edit this offset'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        return mmd_model.Model.findRoot(context.active_object)

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root
        morph = mmd_root.material_morphs[mmd_root.active_morph]
        mat_data = morph.data[morph.active_material_data]

        meshObj = rig.findMesh(mat_data.related_mesh)
        if meshObj is None:
            self.report({ 'ERROR' }, "The model mesh can't be found")
            return { 'CANCELLED' }
        base_mat = meshObj.data.materials[mat_data.material]
        work_mat = base_mat.copy()
        work_mat.name = base_mat.name+"_temp"     
        meshObj.data.materials.append(work_mat)
        FnMaterial.swap_materials(meshObj, base_mat.name, work_mat.name)
        base_mmd_mat = base_mat.mmd_material
        work_mmd_mat = work_mat.mmd_material

        # Apply the offsets
        if mat_data.offset_type == "MULT":
            diffuse_offset = multiply_vector_components(base_mmd_mat.diffuse_color, mat_data.diffuse_color[0:3])
            specular_offset = multiply_vector_components(base_mmd_mat.specular_color, mat_data.specular_color)
            edge_offset = multiply_vector_components(base_mmd_mat.edge_color, mat_data.edge_color)
            ambient_offset = multiply_vector_components(base_mmd_mat.ambient_color, mat_data.ambient_color)
            work_mmd_mat.diffuse_color = diffuse_offset
            work_mmd_mat.alpha *= mat_data.diffuse_color[3]
            work_mmd_mat.specular_color = specular_offset
            work_mmd_mat.shininess *= mat_data.shininess
            work_mmd_mat.ambient_color = ambient_offset
            work_mmd_mat.edge_color = edge_offset
            work_mmd_mat.edge_weight *= mat_data.edge_weight
        elif mat_data.offset_type == "ADD":
            diffuse_offset = Vector(base_mmd_mat.diffuse_color) + Vector(mat_data.diffuse_color[0:3])
            specular_offset = Vector(base_mmd_mat.specular_color) + Vector(mat_data.specular_color)
            edge_offset = Vector(base_mmd_mat.edge_color) + Vector(mat_data.edge_color)
            ambient_offset = Vector(base_mmd_mat.ambient_color) + Vector(mat_data.ambient_color)
            work_mmd_mat.diffuse_color = list(diffuse_offset)
            work_mmd_mat.alpha += mat_data.diffuse_color[3]
            work_mmd_mat.specular_color = list(specular_offset)
            work_mmd_mat.shininess += mat_data.shininess
            work_mmd_mat.ambient_color = list(ambient_offset)
            work_mmd_mat.edge_color = list(edge_offset)
            work_mmd_mat.edge_weight += mat_data.edge_weight

        mmd_root.editing_morphs += 1
        return { 'FINISHED' }

class ClearTempMaterials(Operator):
    bl_idname = 'mmd_tools.clear_temp_materials'
    bl_label = 'Clear Temp Materials'
    bl_description = 'Clears all the temporary materials'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        return mmd_model.Model.findRoot(context.active_object)

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root) 
        for meshObj in rig.meshes():
            mats_to_delete = []
            for mat in meshObj.data.materials:
                if mat and "_temp" in mat.name:
                    mats_to_delete.append(mat)
            for temp_mat in reversed(mats_to_delete):
                base_mat_name=temp_mat.name[0:-1*len("_temp")]
                try:
                    FnMaterial.swap_materials(meshObj, temp_mat.name, base_mat_name)
                except MaterialNotFoundError:
                    self.report({ 'WARNING' } ,'Base material for %s was not found'%temp_mat.name)
                else:
                    temp_idx = meshObj.data.materials.find(temp_mat.name)
                    mat = meshObj.data.materials.pop(index=temp_idx)
                    bpy.data.materials.remove(mat)
                    root.mmd_root.editing_morphs -= 1

        return { 'FINISHED' }
    
class AddBoneMorph(Operator, _AddMorphBase):
    bl_idname = 'mmd_tools.add_bone_morph'
    bl_label = 'Add Bone Morph'
    bl_description = 'Add a bone morph item to the list (a "Exp" display item will be added automatically)'
    bl_options = {'PRESET'}

    #XXX Fix for draw order
    name_j = _AddMorphBase.name_j
    name_e = _AddMorphBase.name_e
    category = _AddMorphBase.category

    create_from_pose = bpy.props.BoolProperty(
        name='Create From Pose',
        description='Also create bone morph offsets from current pose if enabled',
        default=False,
        )
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        bone_morph = self._addMorph(mmd_root)

        if self.create_from_pose:
            armature = mmd_model.Model(root).armature()
            if armature is None:
                return { 'FINISHED' }
            def_loc = Vector((0,0,0))
            def_rot = Quaternion((1,0,0,0))
            for p_bone in armature.pose.bones:
                if p_bone.location != def_loc or p_bone.rotation_quaternion != def_rot:
                    morph_data = bone_morph.data.add()
                    morph_data.bone = p_bone.name
                    morph_data.location = p_bone.location
                    morph_data.rotation = p_bone.rotation_quaternion
                    p_bone.bone.select = True
                else:
                    p_bone.bone.select = False
        return { 'FINISHED' }

class ViewBoneMorph(Operator):
    bl_idname = 'mmd_tools.view_bone_morph'
    bl_label = 'View Bone Morph'
    bl_description = 'View the result of active bone morph'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root=root.mmd_root
        rig = mmd_model.Model(root)
        armature = rig.armature()
        utils.selectSingleBone(context, armature, None, True)
        morph = mmd_root.bone_morphs[mmd_root.active_morph]
        for morph_data in morph.data:
            p_bone = armature.pose.bones.get(morph_data.bone, None)
            if p_bone:
                p_bone.bone.select = True
                p_bone.location = morph_data.location
                p_bone.rotation_quaternion = morph_data.rotation
        return { 'FINISHED' }

class AddBoneMorphOffset(Operator):
    bl_idname = 'mmd_tools.add_bone_morph_offset'
    bl_label = 'Add Bone Morph Offset'
    bl_description = 'Add a bone morph offset item to the list'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        morph = mmd_root.bone_morphs[mmd_root.active_morph]
        if context.selected_pose_bones is None or len(context.selected_pose_bones) == 0:
            bone = context.active_bone or context.active_pose_bone
            morph_data = morph.data.add()
            if bone:
                morph_data.bone = bone.name
        else:
            for p_bone in context.selected_pose_bones:
                morph_data = morph.data.add()
                morph_data.bone = p_bone.name
                morph_data.location = p_bone.location
                morph_data.rotation = p_bone.rotation_quaternion
        morph.active_bone_data = len(morph.data)-1
        return { 'FINISHED' }
    
    
class RemoveBoneMorphOffset(Operator):
    bl_idname = 'mmd_tools.remove_bone_morph_offset'
    bl_label = 'Remove Bone Morph Offset'
    bl_description = 'Remove active bone morph offset item from the list'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        morph = mmd_root.bone_morphs[mmd_root.active_morph]
        if len(morph.data) == 0:
            return { 'FINISHED' }
        morph.data.remove(morph.active_bone_data)
        morph.active_bone_data = max(0, morph.active_bone_data-1)
        
        return { 'FINISHED' }
        
        

class SelectRelatedBone(Operator):
    bl_idname = 'mmd_tools.select_bone_morph_offset_bone'
    bl_label = 'Select Related Bone'
    bl_description = 'Select the bone assigned to this offset in the armature'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root=root.mmd_root
        rig = mmd_model.Model(root)
        armature = rig.armature()
        morph = mmd_root.bone_morphs[mmd_root.active_morph]
        morph_data = morph.data[morph.active_bone_data]
        utils.selectSingleBone(context, armature, morph_data.bone)
        
        return { 'FINISHED' }

class AssignBoneToOffset(Operator):
    bl_idname = 'mmd_tools.assign_bone_morph_offset_bone'
    bl_label = 'Assign Related Bone'
    bl_description = 'Assign the selected bone to this offset'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        bone = context.active_bone
        return bone and bone.name in context.object.pose.bones

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root=root.mmd_root    
        bone = context.active_bone
        morph = mmd_root.bone_morphs[mmd_root.active_morph]
        morph_data = morph.data[morph.active_bone_data]
        morph_data.bone = bone.name
        
        return { 'FINISHED' }
    
     
class EditBoneOffset(Operator): 
    bl_idname = 'mmd_tools.edit_bone_morph_offset'
    bl_label = 'Edit Related Bone'
    bl_description = 'Applies the location and rotation of this offset to the bone'
    bl_options = {'PRESET'}    
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root=root.mmd_root  
        rig = mmd_model.Model(root)
        armature = rig.armature()  
        morph = mmd_root.bone_morphs[mmd_root.active_morph]
        morph_data = morph.data[morph.active_bone_data]
        p_bone = armature.pose.bones[morph_data.bone]
        p_bone.location = morph_data.location
        p_bone.rotation_quaternion = morph_data.rotation
        utils.selectSingleBone(context, armature, p_bone.name)
        
        return { 'FINISHED' }   

class ApplyBoneOffset(Operator):
    bl_idname = 'mmd_tools.apply_bone_morph_offset'
    bl_label = 'Apply Bone Morph Offset'
    bl_description = 'Stores the current bone location and rotation into this offset'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root=root.mmd_root  
        rig = mmd_model.Model(root)
        armature = rig.armature()        
        morph = mmd_root.bone_morphs[mmd_root.active_morph]
        morph_data = morph.data[morph.active_bone_data]
        p_bone = armature.pose.bones[morph_data.bone]
        morph_data.location = p_bone.location
        morph_data.rotation = p_bone.rotation_quaternion
        
        return { 'FINISHED' }  

class AddUVMorph(Operator, _AddMorphBase):
    bl_idname = 'mmd_tools.add_uv_morph'
    bl_label = 'Add UV Morph'
    bl_description = 'Add a UV morph item to the list (a "Exp" display item will be added automatically)'
    bl_options = {'PRESET'}

    #XXX Fix for draw order
    name_j = _AddMorphBase.name_j
    name_e = _AddMorphBase.name_e
    category = _AddMorphBase.category

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        self._addMorph(mmd_root)
        return { 'FINISHED' }

class ViewUVMorph(Operator):
    bl_idname = 'mmd_tools.view_uv_morph'
    bl_label = 'View UV Morph'
    bl_description = 'View the result of active UV morph'
    bl_options = {'PRESET'}

    with_animation = bpy.props.BoolProperty(
        name='With Animation',
        description='View the effect using Timeline window from frame 0 to frame 100 if enabled',
        default=False,
        )

    def invoke(self, context, event):
        vm = context.window_manager
        return vm.invoke_props_dialog(self)

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root
        meshObj = rig.firstMesh()
        if meshObj is None:
            self.report({ 'ERROR' }, "The model mesh can't be found")
            return { 'CANCELLED' }

        bpy.ops.mmd_tools.clear_uv_morph_view()

        selected = meshObj.select
        with bpyutils.select_object(meshObj) as data:
            morph = mmd_root.uv_morphs[mmd_root.active_morph]
            mesh = meshObj.data
            uv_textures = mesh.uv_textures
            if morph.uv_index >= len(uv_textures):
                self.report({ 'ERROR' }, "Invalid uv index: %d"%morph.uv_index)
                return { 'CANCELLED' }

            uv_textures.active_index = morph.uv_index
            uv_tex = uv_textures.new(name='__uv.%s'%uv_textures.active.name)
            if uv_tex is None:
                self.report({ 'ERROR' }, "Failed to create a temporary uv layer")
                return { 'CANCELLED' }

            if len(morph.data) > 0:
                uv_id_map = dict([(i, []) for i in range(len(mesh.vertices))])
                #uv_id = 0
                #for f in mesh.polygons:
                #    for vertex_id in f.vertices:
                #        uv_id_map[vertex_id].append(uv_id)
                #        uv_id += 1
                for uv_id, l in enumerate(mesh.loops):
                    uv_id_map[l.vertex_index].append(uv_id)

                base_uv_data = mesh.uv_layers.active.data
                temp_uv_data = mesh.uv_layers[uv_tex.name].data

                if self.with_animation:
                    morph_name = '__uv.%s'%morph.name
                    a = mesh.animation_data_create()
                    act = bpy.data.actions.new(name=morph_name)
                    old_act = a.action
                    a.action = act

                    for data in morph.data:
                        offset = Vector(data.offset[:2]) # only use dx, dy
                        for i in uv_id_map.get(data.index, []):
                            t = temp_uv_data[i]
                            t.keyframe_insert('uv', frame=0, group=morph_name)
                            t.uv = base_uv_data[i].uv + offset
                            t.keyframe_insert('uv', frame=100, group=morph_name)

                    for fcurve in act.fcurves:
                        for kp in fcurve.keyframe_points:
                            kp.interpolation = 'LINEAR'
                        fcurve.lock = True

                    nla = a.nla_tracks.new()
                    nla.name = morph_name
                    nla.strips.new(name=morph_name, start=0, action=act)
                    a.action = old_act
                    context.scene.frame_current = 100
                else:
                    for data in morph.data:
                        offset = Vector(data.offset[:2]) # only use dx, dy
                        for i in uv_id_map.get(data.index, []):
                            temp_uv_data[i].uv = base_uv_data[i].uv + offset

            uv_textures.active = uv_tex
            uv_tex.active_render = True
        meshObj.hide = False
        meshObj.select = selected
        root.mmd_root.editing_morphs += 1
        return { 'FINISHED' }

class ClearUVMorphView(Operator):
    bl_idname = 'mmd_tools.clear_uv_morph_view'
    bl_label = 'Clear UV Morph View'
    bl_description = 'Clear all temporary data of UV morphs'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        for m in rig.meshes():
            mesh = m.data
            uv_textures = mesh.uv_textures
            for t in uv_textures:
                if t.name.startswith('__uv.'):
                    uv_textures.remove(t)
            if len(uv_textures) > 0:
                uv_textures[0].active_render = True

            animation_data = mesh.animation_data
            if animation_data:
                nla_tracks = animation_data.nla_tracks
                for t in nla_tracks:
                    if t.name.startswith('__uv.'):
                        nla_tracks.remove(t)
                if animation_data.action and animation_data.action.name.startswith('__uv.'):
                    animation_data.action = None
                if animation_data.action is None and len(nla_tracks) == 0:
                    mesh.animation_data_clear()

        for act in bpy.data.actions:
            if act.name.startswith('__uv.') and act.users < 1:
                bpy.data.actions.remove(act)
        bpy.ops.screen.frame_jump(end=False)
        root.mmd_root.editing_morphs -= 1
        return { 'FINISHED' }

class EditUVMorph(Operator):
    bl_idname = 'mmd_tools.edit_uv_morph'
    bl_label = 'Edit UV Morph'
    bl_description = 'Edit UV morph on a temporary UV layer (use UV Editor to edit the result)'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj.type != 'MESH':
            return False
        uv_textures = obj.data.uv_textures
        return uv_textures.active and uv_textures.active.name.startswith('__uv.')

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root
        meshObj = rig.firstMesh()
        if meshObj != obj:
            self.report({ 'ERROR' }, "The model mesh can't be found")
            return { 'CANCELLED' }

        #bpy.ops.mmd_tools.view_uv_morph()

        selected = meshObj.select
        with bpyutils.select_object(meshObj) as data:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT', action='ENABLE')
            bpy.ops.mesh.reveal() # unhide all vertices
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            vertices = meshObj.data.vertices
            morph = mmd_root.uv_morphs[mmd_root.active_morph]
            for data in morph.data:
                if 0 <= data.index < len(vertices):
                    vertices[data.index].select = True
            bpy.ops.object.mode_set(mode='EDIT')
        meshObj.select = selected
        return { 'FINISHED' }

class ApplyUVMorph(Operator):
    bl_idname = 'mmd_tools.apply_uv_morph'
    bl_label = 'Apply UV Morph'
    bl_description = 'Calculate the UV offsets of selected vertices and apply to active UV morph'
    bl_options = {'PRESET'}

    #with_animation = bpy.props.BoolProperty(
    #    name='With Animation',
    #    description='View the effect using Timeline window from frame 0 to frame 100 if enabled',
    #    default=False,
    #    )

    #def invoke(self, context, event):
    #    vm = context.window_manager
    #    return vm.invoke_props_dialog(self)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj.type != 'MESH' or obj.mode != 'EDIT':
            return False
        uv_textures = obj.data.uv_textures
        return uv_textures.active and uv_textures.active.name.startswith('__uv.')

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root
        meshObj = rig.firstMesh()
        if meshObj != obj:
            self.report({ 'ERROR' }, "The model mesh can't be found")
            return { 'CANCELLED' }

        selected = meshObj.select
        with bpyutils.select_object(meshObj) as data:
            morph = mmd_root.uv_morphs[mmd_root.active_morph]
            morph.data.clear()
            mesh = meshObj.data

            base_uv_layers = [l for l in mesh.uv_layers if not l.name.startswith('__uv.')]
            if morph.uv_index >= len(base_uv_layers):
                self.report({ 'ERROR' }, "Invalid uv index: %d"%morph.uv_index)
                return { 'CANCELLED' }
            base_uv_data = base_uv_layers[morph.uv_index].data
            temp_uv_data = mesh.uv_layers.active.data

            #uv_vertices = []
            #for f in mesh.polygons:
            #    uv_vertices.extend(f.vertices)
            uv_vertices = [l.vertex_index for l in mesh.loops]

            for bv in mesh.vertices:
                if not bv.select:
                    continue
                # uv_idx = uv_vertices.index(bv.index) #XXX only get the first one
                # uv_indexes = [i for i, v in enumerate(uv_vertices) if v == bv.index]
                for uv_idx, v in enumerate(uv_vertices):
                    # Find the first valid offset
                    if v == bv.index:
                        dx, dy = temp_uv_data[uv_idx].uv - base_uv_data[uv_idx].uv
                        if abs(dx) > 0.0001 or abs(dy) > 0.0001:
                            data = morph.data.add()
                            data.index = bv.index
                            data.offset = (dx, dy, 0, 0)
                            break

        meshObj.select = selected
        # Can't call view_uv_morph here if we want to track the number of editing morphs
        # bpy.ops.mmd_tools.view_uv_morph(with_animation=self.with_animation)
        mmd_root.editing_morphs -= 1
        return { 'FINISHED' }

class AddGroupMorph(Operator, _AddMorphBase):
    bl_idname = 'mmd_tools.add_group_morph'
    bl_label = 'Add Group Morph'
    bl_description = 'Add a group morph item to the list (a "Exp" display item will be added automatically)'
    bl_options = {'PRESET'}

    #XXX Fix for draw order
    name_j = _AddMorphBase.name_j
    name_e = _AddMorphBase.name_e
    category = _AddMorphBase.category

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        self._addMorph(mmd_root)
        return { 'FINISHED' }

class AddGroupMorphOffset(Operator):
    bl_idname = 'mmd_tools.add_group_morph_offset'
    bl_label = 'Add Group Morph Offset'
    bl_description = 'Add a group morph offset item to the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        morph = mmd_root.group_morphs[mmd_root.active_morph]
        data = morph.data.add()
        morph.active_group_data = len(morph.data)-1
        return { 'FINISHED' }

class RemoveGroupMorphOffset(Operator):
    bl_idname = 'mmd_tools.remove_group_morph_offset'
    bl_label = 'Remove Group Morph Offset'
    bl_description = 'Remove active group morph offset item from the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        morph = mmd_root.group_morphs[mmd_root.active_morph]
        if len(morph.data) == 0:
            return { 'FINISHED' }
        morph.data.remove(morph.active_group_data)
        morph.active_group_data = max(0, morph.active_group_data-1)
        return { 'FINISHED' }

class RemoveMorph(Operator):
    bl_idname = 'mmd_tools.remove_morph'
    bl_label = 'Remove Morph'
    bl_description = 'Remove active morph item from the list (the "Exp" display item will be removed automatically if found)'
    bl_options = {'PRESET'}
    
    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root
        attr_name = mmd_root.active_morph_type
        items = getattr(mmd_root, attr_name)
        if mmd_root.active_morph >= 0 and mmd_root.active_morph < len(items):
            active_morph = items[mmd_root.active_morph]
            if attr_name == "vertex_morphs":
                for meshObj in rig.meshes():
                    shape_keys = meshObj.data.shape_keys
                    if shape_keys is None:
                        continue
                    i = shape_keys.key_blocks.find(active_morph.name)
                    if i < 0:
                        continue
                    with bpyutils.select_object(meshObj) as m: 
                        m.active_shape_key_index = i
                        bpy.ops.object.shape_key_remove()
                
            facial_frame = mmd_root.display_item_frames[u'表情']
            for idx, i in enumerate(facial_frame.items):
                if i.name == active_morph.name and i.morph_type == attr_name:
                    if facial_frame.active_item >= idx:
                        facial_frame.active_item = max(0, facial_frame.active_item-1)
                    facial_frame.items.remove(idx)
                    break
            items.remove(mmd_root.active_morph)
            mmd_root.active_morph = max(0, mmd_root.active_morph-1)
                
            
        return { 'FINISHED' }
