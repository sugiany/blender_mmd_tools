# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator

from mmd_tools import utils
from mmd_tools.core import model as mmd_model
from mmd_tools.core.morph import FnMorph


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
        utils.separateByMaterials(obj)
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
            # return { 'CANCELLED' }
        # Join selected meshes
        bpy.ops.object.select_all(action='DESELECT')
        for mesh in meshes_list:
            mesh.hide = False
            mesh.select = True
        bpy.context.scene.objects.active = active_mesh
        bpy.ops.object.join()
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
        return mmd_model.Model.findRoot(obj) is not None

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
            
        