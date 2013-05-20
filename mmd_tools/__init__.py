# -*- coding: utf-8 -*-

import bpy
import bpy_extras.io_utils

from . import import_pmx
from . import import_vmd
from . import mmd_camera
from . import utils
from . import cycles_converter
from . import test
from . import auto_scene_setup

bl_info= {
    "name": "mmd_tools",
    "author": "sugiany",
    "version": (0, 3, 0),
    "blender": (2, 6, 6),
    "location": "View3D > Tool Shelf > mmd_tools Panel",
    "description": "Utility tools for MMD model editing.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Object"}

if "bpy" in locals():
    import imp
    if "import_pmx" in locals():
        imp.reload(import_pmx)
    if "import_vmd" in locals():
        imp.reload(import_vmd)
    if "mmd_camera" in locals():
        imp.reload(mmd_camera)
    if "utils" in locals():
        imp.reload(utils)
    if "cycles_converter" in locals():
        imp.reload(cycles_converter)
    if "auto_scene_setup" in locals():
        imp.reload(auto_scene_setup)
    if "test" in locals():
        imp.reload(test)

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
    deleteTipBones = bpy.props.BoolProperty(name='delete tip bones', default=False)
    hide_rigids = bpy.props.BoolProperty(name='hide rigid bodies and joints', default=True)
    only_collisions = bpy.props.BoolProperty(name='import only non dynamics rigid bodies', default=False)
    ignore_non_collision_groups = bpy.props.BoolProperty(name='ignore  non collision groups', default=False)
    distance_of_ignore_collisions = bpy.props.FloatProperty(name='distance of ignore collisions', default=5.0)

    def execute(self, context):
        importer = import_pmx.PMXImporter()
        importer.execute(
            filepath=self.filepath,
            scale=self.scale,
            rename_LR_bones=self.renameBones,
            delete_tip_bones=self.deleteTipBones,
            hide_rigids=self.hide_rigids,
            only_collisions=self.only_collisions,
            ignore_non_collision_groups=self.ignore_non_collision_groups,
            distance_of_ignore_collisions=self.distance_of_ignore_collisions
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
    margin = bpy.props.IntProperty(name='margin', default=5, min=0)
    update_scene_settings = bpy.props.BoolProperty(name='update scene settings', default=True)

    def execute(self, context):
        importer = import_vmd.VMDImporter(filepath=self.filepath, scale=self.scale, frame_margin=self.margin)
        for i in context.selected_objects:
            importer.assign(i)
        if self.update_scene_settings:
            auto_scene_setup.setupFrameRanges()
            auto_scene_setup.setupFps()

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

class ConvertToCyclesShader_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.convert_to_cycles_shader'
    bl_label = 'to cycles shader'
    bl_description = 'Convert blender render shader to Cycles shader'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            return {'FINISHED'}

        cycles_converter.convertToCyclesShader(obj)
        return {'FINISHED'}

class AutoSceneSetup_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.auto_scene_setup'
    bl_label = 'auto setup'
    bl_description = 'set basic parameters for test renderings.'
    bl_options = {'PRESET'}

    def execute(self, context):
        auto_scene_setup.setupFrameRanges()
        auto_scene_setup.setupLighting()
        auto_scene_setup.setupFps()
        return {'FINISHED'}


## Main Panel
class MMDToolsObjectPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_object'
    bl_label = 'mmd_tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = ''

    def draw(self, context):
        active_obj = context.active_object

        layout = self.layout

        col = layout.column(align=True)
        col.label('Import-Export:')
        c = col.column()
        c.operator('mmd_tools.import_pmx', text='import pmx')
        c.operator('mmd_tools.import_vmd', text='import vmd')

        col = layout.column(align=True)
        col.label('Scene:')
        c = col.column(align=True)
        c.operator('mmd_tools.auto_scene_setup', text='auto scene setup')

        if active_obj is not None and active_obj.type == 'MESH':
            col = layout.column(align=True)
            col.label('Mesh:')
            c = col.column()
            c.operator('mmd_tools.separate_by_materials', text='separate by materials')
        if active_obj is not None and active_obj.type == 'MESH':
            col = layout.column(align=True)
            col.label('Material:')
            c = col.column()
            c.operator('mmd_tools.convert_to_cycles_shader', text='to cycles')


def register():
    bpy.utils.register_module(__name__)

    bpy.types.Object.is_mmd_camera = bpy.props.BoolProperty(name='is_mmd_camera', default=False)
    bpy.types.Object.mmd_camera_location = bpy.props.FloatVectorProperty(name='mmd_camera_location')
    bpy.types.Object.mmd_camera_rotation = bpy.props.FloatVectorProperty(name='mmd_camera_rotation')
    bpy.types.Object.mmd_camera_distance = bpy.props.FloatProperty(name='mmd_camera_distance')
    bpy.types.Object.mmd_camera_angle = bpy.props.FloatProperty(name='mmd_camera_angle')
    bpy.types.Object.mmd_camera_persp = bpy.props.BoolProperty(name='mmd_camera_persp')
    bpy.types.Object.is_mmd_lamp = bpy.props.BoolProperty(name='is_mmd_lamp', default=False)
    bpy.types.Object.is_mmd_rigid = bpy.props.BoolProperty(name='is_mmd_rigid', default=False)
    bpy.types.Object.is_mmd_joint = bpy.props.BoolProperty(name='is_mmd_joint', default=False)
    bpy.types.Object.is_mmd_non_collision_joint = bpy.props.BoolProperty(name='is_mmd_non_collision_joint', default=False)
    bpy.types.Object.is_mmd_spring_joint = bpy.props.BoolProperty(name='is_mmd_spring_joint', default=False)
    bpy.types.Object.is_mmd_spring_goal = bpy.props.BoolProperty(name='is_mmd_spring_goal', default=False)
    bpy.types.PoseBone.mmd_enabled_local_axis = bpy.props.BoolProperty(name='mmd_enabled_local_axis', default=False)
    bpy.types.PoseBone.mmd_local_axis_x = bpy.props.FloatVectorProperty(name='mmd_local_axis_x')
    bpy.types.PoseBone.mmd_local_axis_z = bpy.props.FloatVectorProperty(name='mmd_local_axis_z')

def unregister():
    del bpy.types.Object.is_mmd_camera
    del bpy.types.Object.mmd_camera_location
    del bpy.types.Object.mmd_camera_rotation
    del bpy.types.Object.mmd_camera_distance
    del bpy.types.Object.mmd_camera_angle
    del bpy.types.Object.mmd_camera_persp
    del bpy.types.Object.is_mmd_lamp
    del bpy.types.Object.is_mmd_rigid
    del bpy.types.Object.is_mmd_joint
    del bpy.types.Object.is_mmd_non_collision_joint
    del bpy.types.Object.is_mmd_spring_joint
    del bpy.types.Object.is_mmd_spring_goal
    del bpy.types.PoseBone.mmd_enabled_local_axis
    del bpy.types.PoseBone.mmd_local_axis_x
    del bpy.types.PoseBone.mmd_local_axis_z

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
