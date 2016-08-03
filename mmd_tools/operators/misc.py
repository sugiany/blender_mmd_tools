# -*- coding: utf-8 -*-

import re

import bpy
from bpy.types import Operator

from mmd_tools import utils
from mmd_tools.core import model as mmd_model
from mmd_tools.core.morph import FnMorph
from mmd_tools.core.material import FnMaterial

PREFIX_PATT = r'(?P<prefix>[0-9A-Z]{3}_)(?P<name>.*)'

class SeparateByMaterials(Operator):
    bl_idname = 'mmd_tools.separate_by_materials'
    bl_label = 'Separate by materials'
    bl_description = 'Separate by materials'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        if root and root.mmd_root.editing_morphs > 0:    
            bpy.ops.mmd_tools.clear_temp_materials()
            bpy.ops.mmd_tools.clear_uv_morph_view()        
            self.report({ 'WARNING' }, "Active editing morphs were cleared")
            # return { 'CANCELLED' }
        if root:
            # Store the current material names
            rig = mmd_model.Model(root)
            mat_names = [mat.name for mat in rig.materials()]
        utils.separateByMaterials(obj)
        if root:
            rig = mmd_model.Model(root)
            # The material morphs store the name of the mesh, not of the object.
            # So they will not be out of sync
            for mesh in rig.meshes():
                if len(mesh.data.materials) == 1:
                    mat = mesh.data.materials[0]
                    idx = mat_names.index(mat.name)
                    prefix = utils.int2base(idx, 36)
                    prefix = '0'*(3 - len(prefix)) + prefix + '_'
                    ma = re.match(PREFIX_PATT, mesh.name)
                    if ma:
                        mesh.name = prefix + ma.group('name')
                    else:
                        mesh.name = prefix + mesh.name
                        
        if root and len(root.mmd_root.material_morphs) > 0:
            for morph in root.mmd_root.material_morphs:
                mo = FnMorph(morph, mmd_model.Model(root))
                mo.update_mat_related_mesh()
        utils.clearUnusedMeshes()
        return {'FINISHED'}

class JoinMeshes(Operator):
    bl_idname = 'mmd_tool.join_meshes'
    bl_label = 'Join Meshes'
    bl_description = 'Join the Model meshes into a single one'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        if root is None:
            self.report({ 'ERROR' }, 'Select a MMD model') 
            return { 'CANCELLED' }
        
        # Find all the meshes in mmd_root
        rig = mmd_model.Model(root)
        meshes_list = rig.meshes()
        active_mesh = rig.firstMesh()

        if root.mmd_root.editing_morphs > 0:            
            bpy.ops.mmd_tools.clear_temp_materials()
            bpy.ops.mmd_tools.clear_uv_morph_view()        
            self.report({ 'WARNING' }, "Active editing morphs were cleared")

        # Store the current order of the materials
        material_names = [mat.name for mat in rig.materials()]
        # Join selected meshes
        bpy.ops.object.select_all(action='DESELECT')
        for mesh in meshes_list:
            mesh.hide = False
            mesh.select = True
        bpy.context.scene.objects.active = active_mesh
        bpy.ops.object.join()
        # Restore the material order
        FnMaterial.fixMaterialOrder(rig.firstMesh(), material_names)
        if len(root.mmd_root.material_morphs) > 0:
            for morph in root.mmd_root.material_morphs:
                mo = FnMorph(morph, rig)
                mo.update_mat_related_mesh(rig.firstMesh())

        utils.clearUnusedMeshes()
        return { 'FINISHED' }

class AttachMeshesToMMD(Operator):
    bl_idname = 'mmd_tools.attach_meshes_to_mmd'
    bl_label = 'Attach Meshes to Model'
    bl_description = 'Finds existing meshes and attaches them to the selected MMD model'
    bl_options = {'PRESET'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and mmd_model.Model.findRoot(obj)

    def execute(self, context):
        root = mmd_model.Model.findRoot(context.active_object)
        rig = mmd_model.Model(root)
        armObj = rig.armature()
        if armObj is None:
            self.report({ 'ERROR' }, 'Model Armature not found')
            return { 'CANCELLED' }
        act_layer = bpy.context.scene.active_layer
        meshes_list = (o for o in bpy.context.scene.objects 
                       if o.layers[act_layer] and o.type == 'MESH' and o.mmd_type == 'NONE')
        for mesh in meshes_list:
            if mmd_model.Model.findRoot(mesh) is not None:
                # Do not attach meshes from other models
                continue
            mesh.parent = armObj
        return { 'FINISHED' }

def _normalize_mesh_names(meshes):
    """
    Helper method that sets a prefix for the mesh objects for sorting
    """    
    for i, m in enumerate(meshes):        
        idx = utils.int2base(i, 36)
        prefix = '0'*(3 - len(idx)) + idx + '_'
        ma = re.match(PREFIX_PATT, m.name)
        if ma:
            m.name = prefix + ma.group('name')
        else:            
            m.name = prefix + m.name

def _swap_prefixes(mesh1, mesh2):
    mesh1_prefix = re.match(PREFIX_PATT, mesh1.name).group('prefix')
    mesh1_name = re.match(PREFIX_PATT, mesh1.name).group('name')
    mesh2_prefix = re.match(PREFIX_PATT, mesh2.name).group('prefix')
    mesh2_name = re.match(PREFIX_PATT, mesh2.name).group('name')
    mesh1.name = mesh2_prefix + mesh1_name
    mesh2.name = mesh1_prefix + mesh2_name

class MoveModelMeshUp(Operator):
    bl_idname = 'mmd_tools.move_mesh_up'
    bl_label = 'Move Model Mesh Up'
    bl_description = 'Moves the selected mesh up'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and mmd_model.Model.findRoot(obj)

    def execute(self, context):
        root = mmd_model.Model.findRoot(context.active_object)
        rig = mmd_model.Model(root)
        # First normalize the mesh names
        _normalize_mesh_names(rig.meshes())
        try:
            current_mesh = context.scene.objects[root.mmd_root.active_mesh_index]
        except Exception:
            self.report({ 'ERROR' }, 'Mesh not found')
            return { 'CANCELLED' }
        # Find the previous mesh
        prefix = re.match(PREFIX_PATT, current_mesh.name).group('prefix')[:-1]
        current_idx = int(prefix, 36)
        prev_mesh = rig.findMeshByIndex(current_idx - 1)
        if current_mesh and prev_mesh and current_mesh != prev_mesh:
            # Swap the prefixes
            _swap_prefixes(current_mesh, prev_mesh)

        return { 'FINISHED' }

class MoveModelMeshDown(Operator):
    bl_idname = 'mmd_tools.move_mesh_down'
    bl_label = 'Move Model Mesh Down'
    bl_description = 'Moves the selected mesh down'
    bl_options = {'PRESET'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and mmd_model.Model.findRoot(obj)

    def execute(self, context):
        root = mmd_model.Model.findRoot(context.active_object)
        rig = mmd_model.Model(root)
        # First normalize the mesh names
        _normalize_mesh_names(rig.meshes())
        try:
            current_mesh = context.scene.objects[root.mmd_root.active_mesh_index]
        except Exception:
            self.report({ 'ERROR' }, 'Mesh not found')
            return { 'CANCELLED' }
        # Find the next mesh
        prefix = re.match(PREFIX_PATT, current_mesh.name).group('prefix')[:-1]
        current_idx = int(prefix, 36)
        next_mesh = rig.findMeshByIndex(current_idx + 1)
        if current_mesh and next_mesh and current_mesh != next_mesh:
            # Swap the prefixes
            _swap_prefixes(current_mesh, next_mesh)

        return { 'FINISHED' }

class ChangeMMDIKLoopFactor(Operator):
    bl_idname = 'mmd_tools.change_mmd_ik_loop_factor'
    bl_label = 'Change MMD IK Loop Factor'
    bl_description = 'Change scaling factor of MMD IK loop and update iteration of IK constraints on active armature'
    bl_options = {'PRESET'}

    mmd_ik_loop_factor = bpy.props.IntProperty(
        name='MMD IK Loop Factor',
        description='Scaling factor of MMD IK loop',
        min=1,
        soft_max=10,
        max=100,
        options={'SKIP_SAVE'},
        )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'

    def invoke(self, context, event):
        arm = context.active_object
        self.mmd_ik_loop_factor = max(arm.get('mmd_ik_loop_factor', 1), 1)
        vm = context.window_manager
        return vm.invoke_props_dialog(self)

    def execute(self, context):
        arm = context.active_object

        if '_RNA_UI' not in arm:
            arm['_RNA_UI'] = {}
        rna_ui = arm['_RNA_UI']
        if 'mmd_ik_loop_factor' not in rna_ui:
            rna_ui['mmd_ik_loop_factor'] = {}
        prop = rna_ui['mmd_ik_loop_factor']
        prop['min'] = 1
        prop['soft_min'] = 1
        prop['soft_max'] = 10
        prop['max'] = 100
        prop['description'] = 'Scaling factor of MMD IK loop'

        old_factor = max(arm.get('mmd_ik_loop_factor', 1), 1)
        new_factor = arm['mmd_ik_loop_factor'] = self.mmd_ik_loop_factor
        for b in arm.pose.bones:
            for c in b.constraints:
                if c.type != 'IK':
                    continue
                iterations = int(c.iterations * new_factor / old_factor)
                self.report({ 'INFO' }, 'Update %s of %s: %d -> %d'%(c.name, b.name, c.iterations, iterations))
                c.iterations = iterations
        return { 'FINISHED' }

