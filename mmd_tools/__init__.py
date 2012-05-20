# -*- coding: utf-8 -*-

import bpy
import bpy_extras.io_utils

import import_pmx
import import_vmd
import mmd_camera
import utils

bl_info= {
    "name": "MMD Tools",
    "author": "sugiany",
    "version": (0, 1, 0),
    "blender": (2, 6, 2),
    "location": "View3D > Tool Shelf > MMD Tools Panel",
    "description": "Utility tools for MMD model editing.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"}

## Import-Export
class ImportPmx_Op(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mmd_tools.import_pmx'
    bl_label = 'Import PMX file (.pmx)'
    bl_description = 'Import a PMX file (.pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name='scale', default=0.2)
    renameBones = bpy.props.BoolProperty(name='rename bones', default=True)
    deleteTipBones = bpy.props.BoolProperty(name='delete tip bones', default=True)

    def execute(self, context):
        importer = import_pmx.PMXImporter()
        importer.execute(
            filepath=self.filepath,
            scale=self.scale,
            rename_LR_bones=self.renameBones,
            delete_tip_bones=self.deleteTipBones
            )
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportVmd_Op(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mmd_tools.import_vmd'
    bl_label = 'Import VMD file (.vmd)'
    bl_description = 'Import a VMD file (.vmd)'
    bl_options = {'PRESET'}

    filename_ext = '.vmd'
    filter_glob = bpy.props.StringProperty(default='*.vmd', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name='scale', default=0.2)

    def execute(self, context):
        importer = import_vmd.VMDImporter(filepath=self.filepath, scale=self.scale)
        for i in context.selected_objects:
            importer.assign(i)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


## Others
class SeparateByMaterials_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.separate_by_materials'
    bl_label = 'Separate by materials'
    bl_description = 'Separate by materials'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            return {'FINISHED'}

        utils.separateByMaterials(obj)
        return {'FINISHED'}


## Main Panel
class MMDToolsObjectPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_object'
    bl_label = 'MMD Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = ''

    def draw(self, context):
        active_obj = context.active_object

        sub = self.layout.column(True)
        sub.label('Import-Export:')
        sub.operator('mmd_tools.import_pmx', text='import pmx')
        sub.operator('mmd_tools.import_vmd', text='import vmd')
        self.layout.separator()
        if active_obj is not None and active_obj.type == 'MESH':
            self.layout.operator('mmd_tools.separate_by_materials', text='separate by materials')
        

def register():
    bpy.utils.register_module(__name__)

    bpy.types.Object.is_mmd_camera = bpy.props.BoolProperty(name='is_mmd_camera', default=False)
    bpy.types.Object.mmd_camera_location = bpy.props.FloatVectorProperty(name='mmd_camera_location')
    bpy.types.Object.mmd_camera_rotation = bpy.props.FloatVectorProperty(name='mmd_camera_rotation')
    bpy.types.Object.mmd_camera_distance = bpy.props.FloatProperty(name='mmd_camera_distance')
    bpy.types.Object.mmd_camera_angle = bpy.props.FloatProperty(name='mmd_camera_angle')
    bpy.types.Object.mmd_camera_persp = bpy.props.BoolProperty(name='mmd_camera_persp')

def unregister():
    del bpy.types.Object.is_mmd_camera
    del bpy.types.Object.mmd_camera_location
    del bpy.types.Object.mmd_camera_rotation
    del bpy.types.Object.mmd_camera_distance
    del bpy.types.Object.mmd_camera_angle
    del bpy.types.Object.mmd_camera_persp

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
