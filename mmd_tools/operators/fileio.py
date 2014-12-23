# -*- coding: utf-8 -*-

import logging
import re
import traceback

import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from mmd_tools import import_pmd, import_pmx, export_pmx, import_vmd, auto_scene_setup
import mmd_tools.core.model as mmd_model



LOG_LEVEL_ITEMS = [
    ('DEBUG', '4. DEBUG', '', 1),
    ('INFO', '3. INFO', '', 2),
    ('WARNING', '2. WARNING', '', 3),
    ('ERROR', '1. ERROR', '', 4),
    ]

def log_handler(log_level, filepath=None):
    if filepath is None:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(filepath, mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    return handler


class ImportPmx(Operator, ImportHelper):
    bl_idname = 'mmd_tools.import_model'
    bl_label = 'Import Model file (.pmd, .pmx)'
    bl_description = 'Import a Model file (.pmd, .pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx;*.pmd', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name='Scale', default=0.2)
    renameBones = bpy.props.BoolProperty(name='Rename bones', default=True)
    hide_rigids = bpy.props.BoolProperty(name='Hide rigid bodies and joints', default=True)
    only_collisions = bpy.props.BoolProperty(name='Ignore rigid bodies', default=False)
    ignore_non_collision_groups = bpy.props.BoolProperty(name='Ignore  non collision groups', default=False)
    distance_of_ignore_collisions = bpy.props.FloatProperty(name='Distance of ignore collisions', default=1.5)
    use_mipmap = bpy.props.BoolProperty(name='use MIP maps for UV textures', default=True)
    sph_blend_factor = bpy.props.FloatProperty(name='influence of .sph textures', default=1.0)
    spa_blend_factor = bpy.props.FloatProperty(name='influence of .spa textures', default=1.0)
    log_level = bpy.props.EnumProperty(items=LOG_LEVEL_ITEMS, name='Log level', default='DEBUG')
    save_log = bpy.props.BoolProperty(name='Create a log file', default=False)

    def execute(self, context):
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.import.log')
        else:
            handler = log_handler(self.log_level)
        logger.addHandler(handler)
        try:
            if re.search('\.pmd', self.filepath, flags=re.I):
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


class ImportVmd(Operator, ImportHelper):
    bl_idname = 'mmd_tools.import_vmd'
    bl_label = 'Import VMD file (.vmd)'
    bl_description = 'Import a VMD file (.vmd)'
    bl_options = {'PRESET'}

    filename_ext = '.vmd'
    filter_glob = bpy.props.StringProperty(default='*.vmd', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name='Scale', default=0.2)
    margin = bpy.props.IntProperty(name='Margin', default=5, min=0)
    update_scene_settings = bpy.props.BoolProperty(name='Update scene settings', default=True)

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


class ImportVmdToMMDModel(Operator, ImportHelper):
    bl_idname = 'mmd_tools.import_vmd_to_mmd_model'
    bl_label = 'Import VMD file To MMD Model'
    bl_description = 'Import a VMD file (.vmd)'
    bl_options = {'PRESET'}

    filename_ext = '.vmd'
    filter_glob = bpy.props.StringProperty(default='*.vmd', options={'HIDDEN'})

    margin = bpy.props.IntProperty(name='Margin', default=5, min=0)
    update_scene_settings = bpy.props.BoolProperty(name='Update scene settings', default=True)

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Rig.findRoot(obj)
        rig = mmd_model.Rig(root)
        importer = import_vmd.VMDImporter(filepath=self.filepath, scale=root.mmd_root.scale, frame_margin=self.margin)
        arm = rig.armature()
        t = arm.hide
        arm.hide = False
        importer.assign(arm)
        arm.hide = t
        for i in rig.meshes():
            t = i.hide
            i.hide = False
            importer.assign(i)
            i.hide = t
        if self.update_scene_settings:
            auto_scene_setup.setupFrameRanges()
            auto_scene_setup.setupFps()

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ExportPmx(Operator, ImportHelper):
    bl_idname = 'mmd_tools.export_pmx'
    bl_label = 'Export PMX file (.pmx)'
    bl_description = 'Export a PMX file (.pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx', options={'HIDDEN'})

    # scale = bpy.props.FloatProperty(name='Scale', default=0.2)
    copy_textures = bpy.props.BoolProperty(name='Copy textures', default=False)

    log_level = bpy.props.EnumProperty(items=LOG_LEVEL_ITEMS, name='Log level', default='DEBUG')
    save_log = bpy.props.BoolProperty(name='Create a log file', default=False)

    def execute(self, context):
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.export.log')
        else:
            handler = log_handler(self.log_level)
        logger.addHandler(handler)

        root = mmd_model.Rig.findRoot(context.active_object)
        rig = mmd_model.Rig(root)
        rig.clean()
        try:
            export_pmx.export(
                filepath=self.filepath,
                scale=root.mmd_root.scale,
                root=rig.rootObject(),
                armature=rig.armature(),
                meshes=rig.meshes(),
                rigid_bodies=rig.rigidBodies(),
                joints=rig.joints(),
                copy_textures=self.copy_textures,
                )
        finally:
            logger.removeHandler(handler)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}
