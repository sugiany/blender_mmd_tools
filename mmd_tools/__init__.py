# -*- coding: utf-8 -*-

import bpy
import bpy_extras.io_utils

import re
import logging
import logging.handlers
import traceback

from . import import_pmx
from . import import_pmd
from . import import_vmd
from . import mmd_camera
from . import utils
from . import cycles_converter
from . import auto_scene_setup
from . import rigging

bl_info= {
    "name": "mmd_tools",
    "author": "sugiany",
    "version": (0, 4, 5),
    "blender": (2, 67, 0),
    "location": "View3D > Tool Shelf > MMD Tools Panel",
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

def log_handler(log_level, filepath=None):
    if filepath is None:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(filepath, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    return handler


class MMDToolsPropertyGroup(bpy.types.PropertyGroup):
    pass


## Import-Export
class ImportPmx_Op(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mmd_tools.import_model'
    bl_label = 'Import PMX File (.pmx)'
    bl_description = 'Import a Model File (.pmd, .pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx;*.pmd', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name='Scale', default=0.2)
    renameBones = bpy.props.BoolProperty(name='Rename Bones', default=True)
    hide_rigids = bpy.props.BoolProperty(name='Hide Rigid Bodies and Joints', default=True)
    only_collisions = bpy.props.BoolProperty(name='Import Only Non Dynamics Rigid Bodies', default=False)
    ignore_non_collision_groups = bpy.props.BoolProperty(name='Ignore Non Collision Groups', default=False)
    distance_of_ignore_collisions = bpy.props.FloatProperty(name='Distance of Ignore Collisions', default=1.5)
    use_mipmap = bpy.props.BoolProperty(name='Use MIP Maps for UV Textures', default=True)
    sph_blend_factor = bpy.props.FloatProperty(name='Influence of .sph Textures', default=1.0)
    spa_blend_factor = bpy.props.FloatProperty(name='Influence of .spa Textures', default=1.0)
    save_log = bpy.props.BoolProperty(name='Create a Log File', default=False)
    log_level = bpy.props.EnumProperty(items=[
            ('DEBUG', '4. DEBUG', '', 1),
            ('INFO', '3. INFO', '', 2),
            ('WARNING', '2. WARNING', '', 3),
            ('ERROR', '1. ERROR', '', 4),
            ], name='Log Level', default='INFO')

    def execute(self, context):
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.import.log')
        else:
            handler = log_handler(self.log_level)
        logger.addHandler(handler)
        try:
            if re.search('\.pmd$', self.filepath, flags=re.I):
                import_pmd.import_pmd(
                    filepath=self.filepath,
                    scale=self.scale,
                    rename_LR_bones=self.renameBones,
                    hide_rigids=self.hide_rigids,
                    only_collisions=self.only_collisions,
                    ignore_non_collision_groups=self.ignore_non_collision_groups,
                    distance_of_ignore_collisions=self.distance_of_ignore_collisions,
                    use_mipmap=self.use_mipmap,
                    sph_blend_factor=self.sph_blend_factor,
                    spa_blend_factor=self.spa_blend_factor
                    )
            else:
                importer = import_pmx.PMXImporter()
                importer.execute(
                    filepath=self.filepath,
                    scale=self.scale,
                    rename_LR_bones=self.renameBones,
                    hide_rigids=self.hide_rigids,
                    only_collisions=self.only_collisions,
                    ignore_non_collision_groups=self.ignore_non_collision_groups,
                    distance_of_ignore_collisions=self.distance_of_ignore_collisions,
                    use_mipmap=self.use_mipmap,
                    sph_blend_factor=self.sph_blend_factor,
                    spa_blend_factor=self.spa_blend_factor
                    )
        except Exception as e:
            logging.error(traceback.format_exc())
            self.report({'ERROR'}, str(e))
        finally:
            logger.removeHandler(handler)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ImportVmd_Op(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'mmd_tools.import_vmd'
    bl_label = 'Import VMD File (.vmd)'
    bl_description = 'Import a VMD File (.vmd)'
    bl_options = {'PRESET'}

    filename_ext = '.vmd'
    filter_glob = bpy.props.StringProperty(default='*.vmd', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name='Scale', default=0.2)
    margin = bpy.props.IntProperty(name='Margin', default=5, min=0)
    update_scene_settings = bpy.props.BoolProperty(name='Update Scene Settings', default=True)

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
    bl_label = 'Separate by Materials'
    bl_description = 'Separate by materials'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            return {'FINISHED'}

        utils.separateByMaterials(obj)
        return {'FINISHED'}

class SetFrameRange_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.set_frame_range'
    bl_label = 'Set Range'
    bl_description = 'Set the frame range to best values to play the animation from start to finish. And set the frame rate to 30.0.'
    bl_options = {'PRESET'}

    def execute(self, context):
        auto_scene_setup.setupFrameRanges()
        auto_scene_setup.setupFps()
        return {'FINISHED'}

class SetGLSLShading_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.set_glsl_shading'
    bl_label = 'GLSL View'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        bpy.ops.mmd_tools.reset_shading()
        bpy.context.scene.render.engine = 'BLENDER_RENDER'
        for i in filter(lambda x: x.type == 'MESH', context.scene.objects):
            for s in i.material_slots:
                s.material.use_shadeless = False
        if len(list(filter(lambda x: x.is_mmd_glsl_light, context.scene.objects))) == 0:
            bpy.ops.object.lamp_add(type='HEMI', view_align=False, location=(0, 0, 0), rotation=(0, 0, 0))
            light = context.selected_objects[0]
            light.is_mmd_glsl_light = True
            light.hide = True

        context.area.spaces[0].viewport_shade='TEXTURED'
        bpy.context.scene.game_settings.material_mode = 'GLSL'
        return {'FINISHED'}

class SetShadelessGLSLShading_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.set_shadeless_glsl_shading'
    bl_label = 'Shadeless GLSL View'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        bpy.ops.mmd_tools.reset_shading()
        bpy.context.scene.render.engine = 'BLENDER_RENDER'
        for i in filter(lambda x: x.type == 'MESH', context.scene.objects):
            for s in i.material_slots:
                s.material.use_shadeless = True
        for i in filter(lambda x: x.is_mmd_glsl_light, context.scene.objects):
            context.scene.objects.unlink(i)

        try:
            bpy.context.scene.display_settings.display_device = 'None'
        except TypeError:
            pass # Blender was built without OpenColorIO
        context.area.spaces[0].viewport_shade='TEXTURED'
        bpy.context.scene.game_settings.material_mode = 'GLSL'
        return {'FINISHED'}

class SetCyclesRendering_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.set_cycles_rendering'
    bl_label = 'Cycles'
    bl_description = 'Convert Blender render shader to Cycles shader'
    bl_options = {'PRESET'}

    def execute(self, context):
        bpy.ops.mmd_tools.reset_shading()
        bpy.context.scene.render.engine = 'CYCLES'
        for i in filter(lambda x: x.type == 'MESH', context.scene.objects):
            cycles_converter.convertToCyclesShader(i)
        context.area.spaces[0].viewport_shade='MATERIAL'
        return {'FINISHED'}

class ResetShading_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.reset_shading'
    bl_label = 'Reset View'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        bpy.context.scene.render.engine = 'BLENDER_RENDER'
        for i in filter(lambda x: x.type == 'MESH', context.scene.objects):
            for s in i.material_slots:
                s.material.use_shadeless = False
                s.material.use_nodes = False

        for i in filter(lambda x: x.is_mmd_glsl_light, context.scene.objects):
            context.scene.objects.unlink(i)

        bpy.context.scene.display_settings.display_device = 'sRGB'
        context.area.spaces[0].viewport_shade='SOLID'
        bpy.context.scene.game_settings.material_mode = 'MULTITEXTURE'
        return {'FINISHED'}

class SetShadelessMaterials_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.set_shadeless_materials'
    bl_label = 'GLSL View'
    bl_description = 'set the materials of selected objects to shadeless.'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in context.selected_objects:
            for s in i.material_slots:
                s.material.use_shadeless = True
        return {'FINISHED'}


## Main Panel
class MMDToolsObjectPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_object'
    bl_label = 'MMD Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'MMD'
    bl_context = ''

    def draw(self, context):
        active_obj = context.active_object

        layout = self.layout

        col = layout.column()
        col.label('Import:')
        c = col.column()
        r = c.row(align=True)
        r.operator('mmd_tools.import_model', text='Model')
        r.operator('mmd_tools.import_vmd', text='Motion')

        col = layout.column()
        col.label('View:')
        c = col.column(align=True)
        r = c.row(align=True)
        r.operator('mmd_tools.set_glsl_shading', text='GLSL')
        r.operator('mmd_tools.set_shadeless_glsl_shading', text='Shadeless')
        r = c.row(align=True)
        r.operator('mmd_tools.set_cycles_rendering', text='Cycles')
        r.operator('mmd_tools.reset_shading', text='Reset')

        if active_obj is not None and active_obj.type == 'MESH':
            col = layout.column(align=True)
            col.label('Mesh:')
            c = col.column()
            c.operator('mmd_tools.separate_by_materials', text='Separate by materials')
        if active_obj is not None and active_obj.type == 'MESH':
            col = layout.column(align=True)
            col.label('Material:')
            c = col.column()
            c.operator('mmd_tools.set_shadeless_materials', text='Shadeless')

        col = layout.column(align=True)
        col.label('Scene:')
        c = col.column(align=True)
        c.operator('mmd_tools.set_frame_range', text='Set frame range')


class ShowRigidBodies_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.show_rigid_bodies'
    bl_label = 'Show Rigid Bodies'
    bl_description = 'Show Rigid Bodies'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in rigging.findRididBodyObjects():
            i.hide = False
        return {'FINISHED'}

class HideRigidBodies_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.hide_rigid_bodies'
    bl_label = 'Hide Rigid Bodies'
    bl_description = 'Hide Rigid Bodies'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in rigging.findRididBodyObjects():
            i.hide = True
        return {'FINISHED'}

class ShowJoints_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.show_joints'
    bl_label = 'Show Joints'
    bl_description = 'Show Joints'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in rigging.findJointObjects():
            i.hide = False
        return {'FINISHED'}

class HideJoints_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.hide_joints'
    bl_label = 'Hide Joints'
    bl_description = 'Hide Joints'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in rigging.findJointObjects():
            i.hide = True
        return {'FINISHED'}

class ShowTemporaryObjects_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.show_temporary_objects'
    bl_label = 'Show Temporary Objects'
    bl_description = 'Show Temporary Objects'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in rigging.findTemporaryObjects():
            i.hide = False
        return {'FINISHED'}

class HideTemporaryObjects_Op(bpy.types.Operator):
    bl_idname = 'mmd_tools.hide_temporary_objects'
    bl_label = 'Hide Temporary Objects'
    bl_description = 'Hide Temporary Objects'
    bl_options = {'PRESET'}

    def execute(self, context):
        for i in rigging.findTemporaryObjects():
            i.hide = True
        return {'FINISHED'}

class MMDToolsRiggingPanel(bpy.types.Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_rigging'
    bl_label = 'MMD Rig Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'MMD'
    bl_context = ''


    def draw(self, context):
        col = self.layout.column()
        col.label('Show/Hide:')
        c = col.column()
        r = c.row(align=True)
        r.label('Rigid:')
        r.operator('mmd_tools.show_rigid_bodies', text='Show')
        r.operator('mmd_tools.hide_rigid_bodies', text='Hide')
        r = c.row(align=True)
        r.label('Joint:')
        r.operator('mmd_tools.show_joints', text='Show')
        r.operator('mmd_tools.hide_joints', text='Hide')
        r = c.row(align=True)
        r.label('Temp:')
        r.operator('mmd_tools.show_temporary_objects', text='Show')
        r.operator('mmd_tools.hide_temporary_objects', text='Hide')

def menu_func_import(self, context):
    self.layout.operator(ImportPmx_Op.bl_idname, text="MikuMikuDance Model (.pmd, .pmx)")
    self.layout.operator(ImportVmd_Op.bl_idname, text="MikuMikuDance Motion (.vmd)")


_custom_props = {
    bpy.types.Scene:(
        ('mmd_tools', bpy.props.PointerProperty(type=MMDToolsPropertyGroup)),
    ),
    bpy.types.Object:(
        ('is_mmd_camera', bpy.props.BoolProperty(name='is_mmd_camera', default=False)),
        ('mmd_camera_location', bpy.props.FloatVectorProperty(name='mmd_camera_location')),
        ('mmd_camera_rotation', bpy.props.FloatVectorProperty(name='mmd_camera_rotation')),
        ('mmd_camera_distance', bpy.props.FloatProperty(name='mmd_camera_distance')),
        ('mmd_camera_angle', bpy.props.FloatProperty(name='mmd_camera_angle')),
        ('mmd_camera_persp', bpy.props.BoolProperty(name='mmd_camera_persp')),
        ('is_mmd_lamp', bpy.props.BoolProperty(name='is_mmd_lamp', default=False)),
        ('is_mmd_rigid', bpy.props.BoolProperty(name='is_mmd_rigid', default=False)),
        ('is_mmd_joint', bpy.props.BoolProperty(name='is_mmd_joint', default=False)),
        ('is_mmd_rigid_track_target', bpy.props.BoolProperty(name='is_mmd_rigid_track_target', default=False)),
        ('is_mmd_non_collision_constraint', bpy.props.BoolProperty(name='is_mmd_non_collision_constraint', default=False)),
        ('is_mmd_spring_joint', bpy.props.BoolProperty(name='is_mmd_spring_joint', default=False)),
        ('is_mmd_spring_goal', bpy.props.BoolProperty(name='is_mmd_spring_goal', default=False)),
        ('is_mmd_glsl_light', bpy.props.BoolProperty(name='is_mmd_glsl_light', default=False)),
        ('pmx_import_scale', bpy.props.FloatProperty(name='pmx_import_scale')),
    ),
    bpy.types.PoseBone:(
        ('mmd_enabled_local_axis', bpy.props.BoolProperty(name='mmd_enabled_local_axis', default=False)),
        ('mmd_local_axis_x', bpy.props.FloatVectorProperty(name='mmd_local_axis_x')),
        ('mmd_local_axis_z', bpy.props.FloatVectorProperty(name='mmd_local_axis_z')),
        ('is_mmd_tip_bone', bpy.props.BoolProperty(name='is_mmd_tip_bone', default=False)),
        ('is_mmd_shadow_bone', bpy.props.BoolProperty(name='is_mmd_shadow_bone', default=False)),
        ('mmd_bone_name_j', bpy.props.StringProperty(name='mmd_bone_name_j', description='the bone name in japanese.')),
        ('mmd_bone_name_e', bpy.props.StringProperty(name='mmd_bone_name_e', description='the bone name in english.')),
    ),
    bpy.types.Material:(
        ('ambient_color', bpy.props.FloatVectorProperty(name='ambient color')),
    ),
}

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

    for t in _custom_props:
        for (n, v) in _custom_props[t]:
            setattr(t, n, v)

def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

    for t in _custom_props:
        for (n, v) in _custom_props[t]:
            delattr(t, n)

    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
