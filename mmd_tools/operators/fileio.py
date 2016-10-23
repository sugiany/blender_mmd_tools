# -*- coding: utf-8 -*-

import logging
import re
import traceback
import os
import time

import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper

from mmd_tools import auto_scene_setup
from mmd_tools.utils import selectAObject
from mmd_tools.utils import makePmxBoneMap
from mmd_tools.core.camera import MMDCamera
from mmd_tools.core.lamp import MMDLamp

import mmd_tools.core.pmd.importer as pmd_importer
import mmd_tools.core.pmx.importer as pmx_importer
import mmd_tools.core.pmx.exporter as pmx_exporter
import mmd_tools.core.vmd.importer as vmd_importer
import mmd_tools.core.vmd.exporter as vmd_exporter
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


def _update_types(cls, prop):
    types = cls.types.copy()

    if 'PHYSICS' in types:
        types.add('ARMATURE')
    if 'DISPLAY' in types:
        types.add('ARMATURE')
    if 'MORPHS' in types:
        types.add('ARMATURE')
        types.add('MESH')

    if types != cls.types:
        cls.types = types # trigger update


class ImportPmx(Operator, ImportHelper):
    bl_idname = 'mmd_tools.import_model'
    bl_label = 'Import Model file (.pmd, .pmx)'
    bl_description = 'Import a Model file (.pmd, .pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx;*.pmd', options={'HIDDEN'})

    types = bpy.props.EnumProperty(
        name='Types',
        description='Select which parts will be imported',
        options={'ENUM_FLAG'},
        items = [
            ('MESH', 'Mesh', 'Mesh', 1),
            ('ARMATURE', 'Armature', 'Armature', 2),
            ('PHYSICS', 'Physics', 'Rigidbodies and joints (include Armature)', 4),
            ('DISPLAY', 'Display', 'Display frames (include Armature)', 8),
            ('MORPHS', 'Morphs', 'Morphs (include Armature and Mesh)', 16),
            ],
        default={'MESH', 'ARMATURE', 'PHYSICS', 'DISPLAY', 'MORPHS',},
        update=_update_types,
        )
    scale = bpy.props.FloatProperty(
        name='Scale',
        description='Scaling factor for importing the model',
        default=0.2,
        )
    clean_model = bpy.props.BoolProperty(
        name='Clean Model',
        description='Remove unused vertices and duplicated/invalid faces',
        default=True,
        )
    rename_bones = bpy.props.BoolProperty(
        name='Rename Bones - L / R Suffix',
        description='Use Blender naming conventions for Left / Right paired bones',
        default=True,
        )
    use_underscore = bpy.props.BoolProperty(
        name="Rename Bones - Use Underscore",
        description='Will not use dot, e.g. if renaming bones, will use _R instead of .R',
        default=False,
        )
    translate_to_english = bpy.props.BoolProperty(
        name="Rename Bones To English",
        description='Translate bone names from Japanese to English',
        default=False,
        )    
    use_mipmap = bpy.props.BoolProperty(
        name='use MIP maps for UV textures',
        description='Specify if mipmaps will be generated',
        default=True,
        )
    sph_blend_factor = bpy.props.FloatProperty(
        name='influence of .sph textures',
        description='The diffuse color factor of texture slot for .sph textures',
        default=1.0,
        )
    spa_blend_factor = bpy.props.FloatProperty(
        name='influence of .spa textures',
        description='The diffuse color factor of texture slot for .spa textures',
        default=1.0,
        )
    log_level = bpy.props.EnumProperty(
        name='Log level',
        description='Select log level',
        items=LOG_LEVEL_ITEMS,
        default='DEBUG',
        )
    save_log = bpy.props.BoolProperty(
        name='Create a log file',
        description='Create a log file',
        default=False,
        )

    def execute(self, context):
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.import.log')
            logger.addHandler(handler)
        try:
            importer_cls = pmx_importer.PMXImporter
            if re.search('\.pmd$', self.filepath, flags=re.I):
                importer_cls = pmd_importer.PMDImporter

            importer_cls().execute(
                filepath=self.filepath,
                types=self.types,
                scale=self.scale,
                clean_model=self.clean_model,
                rename_LR_bones=self.rename_bones,
                use_underscore=self.use_underscore,
                translate_to_english=self.translate_to_english,
                use_mipmap=self.use_mipmap,
                sph_blend_factor=self.sph_blend_factor,
                spa_blend_factor=self.spa_blend_factor,
                )
        except Exception as e:
            err_msg = traceback.format_exc()
            logging.error(err_msg)
            self.report({'ERROR'}, err_msg)
        finally:
            if self.save_log:
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

    scale = bpy.props.FloatProperty(
        name='Scale',
        description='Scaling factor for importing the motion',
        default=0.2,
        )
    margin = bpy.props.IntProperty(
        name='Margin',
        description='How many frames added before motion starting',
        min=0,
        default=5,
        )
    bone_mapper = bpy.props.EnumProperty(
        name='Bone Mapper',
        description='Select bone mapper',
        items=[
            ('BLENDER', 'Blender', 'Use blender bone name', 0),
            ('PMX', 'PMX', 'Use japanese name of MMD bone', 1),
            ('RENAMED_BONES', 'Renamed bones', 'Rename the bone of motion data to be blender suitable', 2),
            ],
        default='PMX',
        )
    rename_bones = bpy.props.BoolProperty(
        name='Rename Bones - L / R Suffix',
        description='Use Blender naming conventions for Left / Right paired bones',
        default=True,
        )
    use_underscore = bpy.props.BoolProperty(
        name="Rename Bones - Use Underscore",
        description='Will not use dot, e.g. if renaming bones, will use _R instead of .R',
        default=False,
        )
    translate_to_english = bpy.props.BoolProperty(
        name="Rename Bones To English",
        description='Translate bone names from Japanese to English',
        default=False,
        )
    update_scene_settings = bpy.props.BoolProperty(
        name='Update scene settings',
        description='Update frame range and frame rate (30 fps)',
        default=True,
        )

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'scale')
        layout.prop(self, 'margin')

        layout.prop(self, 'bone_mapper')
        if self.bone_mapper == 'RENAMED_BONES':
            layout.prop(self, 'rename_bones')
            layout.prop(self, 'use_underscore')
            layout.prop(self, 'translate_to_english')

        layout.prop(self, 'update_scene_settings')

    def execute(self, context):
        active_object = context.active_object
        hidden_obj = []
        for i in context.selected_objects:
            root = mmd_model.Model.findRoot(i)
            if root == i:
                rig = mmd_model.Model(root)
                arm = rig.armature()
                if arm.hide:
                    arm.hide = False
                    hidden_obj.append(arm)
                arm.select = True
                for m in rig.meshes():
                    if m.hide:
                        m.hide = False
                        hidden_obj.append(m)
                    m.select = True

        bone_mapper = None
        if self.bone_mapper == 'PMX':
            bone_mapper = makePmxBoneMap
        elif self.bone_mapper == 'RENAMED_BONES':
            bone_mapper = vmd_importer.RenamedBoneMapper(
                rename_LR_bones=self.rename_bones,
                use_underscore=self.use_underscore,
                translate_to_english=self.translate_to_english,
                ).init

        start_time = time.time()
        importer = vmd_importer.VMDImporter(
            filepath=self.filepath,
            scale=self.scale,
            bone_mapper=bone_mapper,
            frame_margin=self.margin,
            )

        for i in context.selected_objects:
            importer.assign(i)
        logging.info(' Finished importing motion in %f seconds.', time.time() - start_time)

        if self.update_scene_settings:
            auto_scene_setup.setupFrameRanges()
            auto_scene_setup.setupFps()

        for i in hidden_obj:
            i.select = False
            i.hide = True

        active_object.select = True
        context.scene.objects.active = active_object
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class ExportPmx(Operator, ExportHelper):
    bl_idname = 'mmd_tools.export_pmx'
    bl_label = 'Export PMX file (.pmx)'
    bl_description = 'Export a PMX file (.pmx)'
    bl_options = {'PRESET'}

    filename_ext = '.pmx'
    filter_glob = bpy.props.StringProperty(default='*.pmx', options={'HIDDEN'})

    copy_textures = bpy.props.BoolProperty(
        name='Copy textures',
        description='Copy textures',
        default=True,
        )
    sort_materials = bpy.props.BoolProperty(
        name='Sort Materials',
        description=('Sort materials for alpha blending. '
                     'WARNING: Will not work if you have ' +
                     'transparent meshes inside the model. ' +
                     'E.g. blush meshes'),
        default=False,
        )
    sort_vertices = bpy.props.EnumProperty(
        name='Sort Vertices',
        description='Choose the method to sort vertices',
        items=[
            ('NONE', 'None', 'No sorting', 0),
            ('BLENDER', 'Blender', 'Use blender\'s internal vertex order', 1),
            ('CUSTOM', 'Custom', 'Use custom vertex weight of vertex group "mmd_vertex_order"', 2),
            ],
        default='NONE',
        )

    log_level = bpy.props.EnumProperty(
        name='Log level',
        description='Select log level',
        items=LOG_LEVEL_ITEMS,
        default='DEBUG',
        )
    save_log = bpy.props.BoolProperty(
        name='Create a log file',
        description='Create a log file',
        default=False,
        )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and mmd_model.Model.findRoot(obj)

    def execute(self, context):
        active_object = context.active_object
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        if self.save_log:
            handler = log_handler(self.log_level, filepath=self.filepath + '.mmd_tools.export.log')
            logger.addHandler(handler)

        root = mmd_model.Model.findRoot(context.active_object)
        if root.mmd_root.editing_morphs > 0:
            # We have two options here: 
            # 1- report it to the user
            # 2- clear the active morphs (user will loose any changes to temp materials and UV) 
            bpy.ops.mmd_tools.clear_temp_materials()
            bpy.ops.mmd_tools.clear_uv_morph_view()        
            self.report({ 'WARNING' }, "Active editing morphs were cleared")
            # return { 'CANCELLED' }
        rig = mmd_model.Model(root)
        arm = rig.armature()
        orig_pose_position = None
        if arm: # use 'REST' pose before exporting
            orig_pose_position = arm.data.pose_position
            arm.data.pose_position = 'REST'
        rig.clean()
        try:
            pmx_exporter.export(
                filepath=self.filepath,
                scale=root.mmd_root.scale,
                root=rig.rootObject(),
                armature=rig.armature(),
                meshes=rig.meshes(),
                rigid_bodies=rig.rigidBodies(),
                joints=rig.joints(),
                copy_textures=self.copy_textures,
                sort_materials=self.sort_materials,
                sort_vertices=self.sort_vertices,
                )
        except Exception as e:
            err_msg = traceback.format_exc()
            logging.error(err_msg)
            self.report({'ERROR'}, err_msg)
        finally:
            if orig_pose_position:
                arm.data.pose_position = orig_pose_position
            if self.save_log:
                logger.removeHandler(handler)

        active_object.select = True
        context.scene.objects.active = active_object
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ExportVmd(Operator, ExportHelper):
    bl_idname = 'mmd_tools.export_vmd'
    bl_label = 'Export VMD file (.vmd)'
    bl_description = 'Export motion data of active object to a VMD file (.vmd)'
    bl_options = {'PRESET'}

    filename_ext = '.vmd'
    filter_glob = bpy.props.StringProperty(default='*.vmd', options={'HIDDEN'})

    scale = bpy.props.FloatProperty(
        name='Scale',
        description='Scaling factor of the model',
        default=0.2,
        )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None:
            return False

        if obj.mmd_type == 'ROOT':
            return True
        if obj.mmd_type == 'NONE' and obj.type in {'MESH', 'ARMATURE'}:
            return True
        if MMDCamera.isMMDCamera(obj) or MMDLamp.isMMDLamp(obj):
            return True

        return False

    def execute(self, context):
        obj = context.active_object
        params = {
            'filepath':self.filepath,
            'scale':self.scale,
            }

        if obj.mmd_type == 'ROOT':
            rig = mmd_model.Model(obj)
            params['mesh'] = rig.firstMesh()
            params['armature'] = rig.armature()
            params['model_name'] = obj.mmd_root.name
        elif obj.type == 'MESH':
            params['mesh'] = obj
            params['model_name'] = obj.name
        elif obj.type == 'ARMATURE':
            params['armature'] = obj
            params['model_name'] = obj.name
        else:
            for i in context.selected_objects:
                if MMDCamera.isMMDCamera(i):
                    params['camera'] = i
                elif MMDCamera.isMMDLamp(i):
                    params['lamp'] = i

        try:
            start_time = time.time()
            vmd_exporter.VMDExporter().export(**params)
            logging.info(' Finished exporting motion in %f seconds.', time.time() - start_time)
        except Exception as e:
            err_msg = traceback.format_exc()
            logging.error(err_msg)
            self.report({'ERROR'}, err_msg)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

