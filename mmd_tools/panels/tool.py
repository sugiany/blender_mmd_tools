# -*- coding: utf-8 -*-

import bpy
from bpy.types import Panel, UIList

from mmd_tools import operators
import mmd_tools.core.model as mmd_model


class _PanelBase(object):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'mmd_tools'


class MMDToolsObjectPanel(_PanelBase, Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_object'
    bl_label = 'Operator'
    bl_context = ''

    def draw(self, context):
        active_obj = context.active_object

        layout = self.layout

        col = layout.column(align=True)
        col.label('Edit:')
        row = col.row(align=True)
        row.operator(operators.model.CreateMMDModelRoot.bl_idname, text='Create Model')
        row.operator(operators.fileio.ImportPmx.bl_idname, text='Import Model')
        col = layout.column(align=True)
        col.operator(operators.material.ConvertMaterialsForCycles.bl_idname, text='Convert Materials For Cycles')
        col.operator('mmd_tools.separate_by_materials', text='Separate By Materials')

        if active_obj is None:
            return

        root = mmd_model.Model.findRoot(active_obj)
        if root:
            col = self.layout.column(align=True)
            col.label('Rigidbody:')
            row = col.row(align=True)
            row.operator('mmd_tools.build_rig')
            row.operator('mmd_tools.clean_rig')
            if not root.mmd_root.is_built:
                col.label(text='Press the "Build" button before playing the physical animation.', icon='ERROR')

            col.label('Bone Constraints:')
            col.operator('mmd_tools.apply_additioinal_transform')

        col = self.layout.column(align=True)
        col.label('Import/Export:')
        col.operator(operators.fileio.ImportVmd.bl_idname, text='Import Motion')
        col.operator(operators.fileio.ExportPmx.bl_idname, text='Export Model')


class MMD_ROOT_UL_display_item_frames(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mmd_root = data
        frame = item

        if self.layout_type in {'DEFAULT'}:
            row = layout.split(percentage=0.4, align=True)
            if frame.is_special:
                row.label(text=frame.name, translate=False, icon_value=icon)
                row = row.row(align=True)
                row.label(text=frame.name_e, translate=False, icon_value=icon)
                row.label(text='', icon='LOCKED')
            else:
                row.prop(frame, 'name', text='', emboss=False, icon_value=icon)
                row.prop(frame, 'name_e', text='', emboss=True, icon_value=icon)
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class MMD_ROOT_UL_display_items(UIList):
    morph_filter = bpy.props.EnumProperty(
        name="Morph Filter",
        items = [
            ('SYSTEM', 'System', '', 0),
            ('EYEBROW', 'Eye Brow', '', 1),
            ('EYE', 'Eye', '', 2),
            ('MOUTH', 'Mouth', '', 3),
            ('OTHER', 'Other', '', 4),
            ('NONE', 'All', '', 10),
            ],
        default='NONE',
        )

    @staticmethod
    def draw_bone_item(layout, armature, bone_name):
        layout.label(text=bone_name, translate=False, icon='BONE_DATA')
        if armature is None:
            return
        row = layout.row(align=True)
        p_bone = armature.pose.bones.get(bone_name, None)
        if p_bone:
            bone = p_bone.bone
            ic = 'RESTRICT_VIEW_ON' if bone.hide else 'RESTRICT_VIEW_OFF'
            row.prop(bone, 'hide', text='', emboss=p_bone.mmd_bone.is_tip, icon=ic)
            row.active = armature.mode != 'EDIT'
        else:
            row.label() # for alignment only
            row.label(icon='ERROR')

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mmd_root = data

        if self.layout_type in {'DEFAULT'}:
            if item.type == 'BONE':
                MMD_ROOT_UL_display_items.draw_bone_item(layout, mmd_model.Model(item.id_data).armature(), item.name)
            else:
                row = layout.split(percentage=0.6, align=True)
                row.label(text=item.name, translate=False, icon='SHAPEKEY_DATA')
                row = row.row(align=True)
                row.prop(item, 'morph_type', text='', emboss=False, icon_value=icon)
                if item.name not in getattr(item.id_data.mmd_root, item.morph_type):
                    row.label(icon='ERROR')
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


    def filter_items(self, context, data, propname):
        if self.morph_filter == 'NONE' or data.name != u'表情':
            return [], []

        objects = getattr(data, propname)
        flt_flags = [~self.bitflag_filter_item] * len(objects)
        flt_neworder = []

        for i, item in enumerate(objects):
            morph = getattr(item.id_data.mmd_root, item.morph_type).get(item.name, None)
            if morph and morph.category == self.morph_filter:
                flt_flags[i] = self.bitflag_filter_item

        return flt_flags, flt_neworder


    def draw_filter(self, context, layout):
        row = layout.row()
        row.prop(self, 'morph_filter', expand=True)


class MMDDisplayItemsPanel(_PanelBase, Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_display_items'
    bl_label = 'Display Items'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        active_obj = context.active_object
        root = None
        if active_obj:
            root = mmd_model.Model.findRoot(active_obj)
        if root is None:
            c = self.layout.column()
            c.label('Select a MMD Model')
            return

        rig = mmd_model.Model(root)
        root = rig.rootObject()
        mmd_root = root.mmd_root
        col = self.layout.column()
        c = col.column(align=True)
        c.label('Frames')
        row = c.row()
        row.template_list(
            "MMD_ROOT_UL_display_item_frames",
            "",
            mmd_root, "display_item_frames",
            mmd_root, "active_display_item_frame",
            )
        tb = row.column()
        tb1 = tb.column(align=True)
        tb1.operator(operators.display_item.AddDisplayItemFrame.bl_idname, text='', icon='ZOOMIN')
        tb1.operator(operators.display_item.RemoveDisplayItemFrame.bl_idname, text='', icon='ZOOMOUT')
        tb.separator()
        tb1 = tb.column(align=True)
        tb1.operator(operators.display_item.MoveUpDisplayItemFrame.bl_idname, text='', icon='TRIA_UP')
        tb1.operator(operators.display_item.MoveDownDisplayItemFrame.bl_idname, text='', icon='TRIA_DOWN')
        if len(mmd_root.display_item_frames)==0:
            return
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]

        c = col.column(align=True)
        row = c.row()
        row.template_list(
            "MMD_ROOT_UL_display_items",
            "",
            frame, "items",
            frame, "active_item",
            )
        tb = row.column()
        tb1 = tb.column(align=True)
        tb1.operator(operators.display_item.AddDisplayItem.bl_idname, text='', icon='ZOOMIN')
        tb1.operator(operators.display_item.RemoveDisplayItem.bl_idname, text='', icon='ZOOMOUT')
        tb.separator()
        tb1 = tb.column(align=True)
        tb1.operator(operators.display_item.MoveUpDisplayItem.bl_idname, text='', icon='TRIA_UP')
        tb1.operator(operators.display_item.MoveDownDisplayItem.bl_idname, text='', icon='TRIA_DOWN')
        if len(frame.items) == 0:
            return # If the list is empty we should stop drawing the panel here
        item = frame.items[frame.active_item]
        row = col.row(align=True)
        row.prop(item, 'type', text='')
        if item.type == 'BONE':
            armature = rig.armature()
            if armature is None:
                row.label('Armature not found', icon='ERROR')
                return
            row.prop_search(item, 'name', armature.pose, 'bones', icon='BONE_DATA', text='')

            row = col.row(align=True)
            row.operator(operators.display_item.SelectCurrentDisplayItem.bl_idname, text='Select')
        elif item.type == 'MORPH':
            row.prop(item, 'morph_type', text='')
            row.prop_search(item, 'name', mmd_root, item.morph_type, icon='SHAPEKEY_DATA', text='')
            if item.morph_type != 'vertex_morphs':
                return
            for i in rig.meshes():
                if i.data.shape_keys is not None and item.name in i.data.shape_keys.key_blocks:
                    row = col.row(align=True)
                    row.label(i.name+':')
                    row.prop(i.data.shape_keys.key_blocks[item.name], 'value')



class UL_Morphs(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT'}:            
            row = layout.split(percentage=0.4, align=True)
            row.prop(item, 'name', text='', emboss=False, icon='SHAPEKEY_DATA')
            row = row.split(percentage=0.6, align=True)
            row.prop(item, 'name_e', text='', emboss=True, icon_value=icon)
            row.prop(item, 'category', text='', emboss=False, icon_value=icon)
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
            
class UL_MaterialMorphOffsets(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT'}:            
            layout.label(text=item.material, translate=False, icon='MATERIAL')
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon) 

class UL_UVMorphOffsets(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT'}:
            layout.label(text=str(item.index), translate=False, icon='MESH_DATA')
            layout.prop(item, 'offset', text='', emboss=False, icon_value=icon, slider=True)
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class UL_BoneMorphOffsets(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT'}:            
            MMD_ROOT_UL_display_items.draw_bone_item(layout, mmd_model.Model(item.id_data).armature(), item.bone)
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)    

class UL_GroupMorphOffsets(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT'}:
            row = layout.split(percentage=0.4, align=True)
            row.label(item.name, translate=False, icon='SHAPEKEY_DATA')
            #row.prop(item, 'name', text='', emboss=False, icon='SHAPEKEY_DATA')
            row = row.row(align=True)
            row.prop(item, 'morph_type', text='', emboss=False, icon_value=icon)
            if item.name in getattr(item.id_data.mmd_root, item.morph_type):
                row.prop(item, 'factor', text='', emboss=False, icon_value=icon, slider=True)
            else:
                row.label(icon='ERROR')
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class MMDMorphToolsPanel(_PanelBase, Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_morph_tools'
    bl_label = 'Morph Tools'
    bl_options = {'DEFAULT_CLOSED'}            
    
    def draw(self, context):
        active_obj = context.active_object
        root = None
        if active_obj:
            root = mmd_model.Model.findRoot(active_obj)
        if root is None:
            c = self.layout.column()
            c.label('Select a MMD Model')
            return
        rig = mmd_model.Model(root)
        root = rig.rootObject()
        mmd_root = root.mmd_root        
        col = self.layout.column()
        row = col.row()
        row.prop(mmd_root, 'active_morph_type', expand=True)
        c = col.column(align=True)
        row = c.row()
        row.template_list(
            "UL_Morphs", "",
            mmd_root, mmd_root.active_morph_type,
            mmd_root, "active_morph"
            )
        tb = row.column()
        tb1 = tb.column(align=True)
        tb1.operator('mmd_tools.add_%s'%mmd_root.active_morph_type[:-1], text='', icon='ZOOMIN')
        tb1.operator(operators.morph.RemoveMorph.bl_idname, text='', icon='ZOOMOUT')
        tb.separator()
        tb1 = tb.column(align=True)
        tb1.operator(operators.morph.MoveUpMorph.bl_idname, text='', icon='TRIA_UP')
        tb1.operator(operators.morph.MoveDownMorph.bl_idname, text='', icon='TRIA_DOWN')
        
        items = getattr(mmd_root, mmd_root.active_morph_type)
        if len(items) > 0:
            morph = items[mmd_root.active_morph]
            draw_func = getattr(self, '_draw_%s_data'%mmd_root.active_morph_type[:-7], None)
            if draw_func:
                draw_func(context, rig, col, morph)

    def _draw_material_data(self, context, rig, col, morph):
        meshObj = rig.firstMesh()
        if meshObj is None:
            c = col.column(align=True)
            c.label("The model mesh can't be found", icon='ERROR')
            return
        c = col.column(align=True)
        c.label('Material Offsets (%d)'%len(morph.data))
        row = c.row()
        row.template_list(
            "UL_MaterialMorphOffsets", "",
            morph, "data",
            morph, "active_material_data"
            )   
        tb = row.column()
        tb1 = tb.column(align=True)  
        tb1.operator(operators.morph.AddMaterialOffset.bl_idname, text='', icon='ZOOMIN')
        tb1.operator(operators.morph.RemoveMaterialOffset.bl_idname, text='', icon='ZOOMOUT')
        # tb.separator()
        # tb1 = tb.column(align=True)
        # tb1.operator(operators.morph.MoveUpMorph.bl_idname, text='', icon='TRIA_UP')
        # tb1.operator(operators.morph.MoveDownMorph.bl_idname, text='', icon='TRIA_DOWN')  
        if len(morph.data) == 0:
            return # If the list is empty we should stop drawing the panel here
        data = morph.data[morph.active_material_data]
        c_mat = col.column(align=True)
        c_mat.prop_search(data, 'material', meshObj.data, 'materials')

        base_mat_name = data.material
        if "_temp" in base_mat_name or base_mat_name not in meshObj.data.materials:
            c = col.column(align=True)
            c.label('This is not a valid base material', icon='ERROR')
            return

        work_mat = meshObj.data.materials.get(base_mat_name + "_temp", None) # Temporary material to edit this offset (and see a live preview)
        if work_mat is None:
            c = col.column(align=True)
            row = c.row(align=True)
            row.operator(operators.morph.CreateWorkMaterial.bl_idname)
            row.operator(operators.morph.ClearTempMaterials.bl_idname, text='Clear')

            c = col.column()
            c.enabled = False # remove this line to allow user to edit directly
            row = c.row()
            row.prop(data, 'offset_type')
            row = c.row()
            row.column(align=True).prop(data, 'diffuse_color', expand=True, slider=True)
            c1 = row.column(align=True)
            c1.prop(data, 'specular_color', expand=True, slider=True)
            c1.prop(data, 'shininess', slider=True)
            row.column(align=True).prop(data, 'ambient_color', expand=True, slider=True)
            row = c.row()
            row.column(align=True).prop(data, 'edge_color', expand=True, slider=True)
            row = c.row()
            row.prop(data, 'edge_weight', slider=True)
            row = c.row()
            row.column(align=True).prop(data, 'texture_factor', expand=True, slider=True)
            row.column(align=True).prop(data, 'sphere_texture_factor', expand=True, slider=True)
            row.column(align=True).prop(data, 'toon_texture_factor', expand=True, slider=True)
        else:
            c_mat.enabled = False
            c = col.column(align=True)
            row = c.row(align=True)
            row.operator(operators.morph.ApplyMaterialOffset.bl_idname, text='Apply')
            row.operator(operators.morph.ClearTempMaterials.bl_idname, text='Clear')

            c = col.column()
            row = c.row()
            row.prop(data, 'offset_type')
            row = c.row()
            row.prop(work_mat.mmd_material, 'diffuse_color')
            row.prop(work_mat.mmd_material, 'alpha', slider=True)
            row = c.row()
            row.prop(work_mat.mmd_material, 'specular_color')
            row.prop(work_mat.mmd_material, 'shininess', slider=True)
            row = c.row()
            row.prop(work_mat.mmd_material, 'ambient_color')
            row.label() # for alignment only
            row = c.row()
            row.prop(work_mat.mmd_material, 'edge_color')
            row.prop(work_mat.mmd_material, 'edge_weight', slider=True)
            row = c.row()
            row.column(align=True).prop(data, 'texture_factor', expand=True, slider=True)
            row.column(align=True).prop(data, 'sphere_texture_factor', expand=True, slider=True)
            row.column(align=True).prop(data, 'toon_texture_factor', expand=True, slider=True)

    def _draw_bone_data(self, context, rig, col, morph):
        armature = rig.armature()
        if armature is None:
            c = col.column(align=True)
            c.label('Armature not found', icon='ERROR')
            return

        c = col.column(align=True)
        row = c.row(align=True)
        row.operator(operators.morph.ViewBoneMorph.bl_idname, text='View')
        row.operator('pose.transforms_clear', text='Clear')

        c = col.column(align=True)
        c.label('Bone Offsets (%d)'%len(morph.data))
        row = c.row()
        row.template_list(
            "UL_BoneMorphOffsets", "",
            morph, "data",
            morph, "active_bone_data"
            )
        tb = row.column()
        tb1 = tb.column(align=True)  
        tb1.operator(operators.morph.AddBoneMorphOffset.bl_idname, text='', icon='ZOOMIN')
        tb1.operator(operators.morph.RemoveBoneMorphOffset.bl_idname, text='', icon='ZOOMOUT')
        if len(morph.data) == 0:
            return # If the list is empty we should stop drawing the panel here
        data = morph.data[morph.active_bone_data]
        row = c.split(percentage=0.67, align=True)
        row.prop_search(data, 'bone', armature.pose, 'bones')
        row.operator(operators.morph.AssignBoneToOffset.bl_idname, text='Assign')
        if data.bone in armature.pose.bones.keys():
            c = col.column(align=True)
            row = c.row(align=True)
            row.operator(operators.morph.SelectRelatedBone.bl_idname, text='Select')
            row.operator(operators.morph.EditBoneOffset.bl_idname, text='Edit')
            row = row.row(align=True)
            row.operator(operators.morph.ApplyBoneOffset.bl_idname, text='Apply')
            b = context.active_pose_bone
            if b is None or b.name != data.bone:
                row.enabled = False

        c = col.column(align=True)
        c.enabled = False # remove this line to allow user to edit directly
        row = c.row()
        c1 = row.column(align=True)
        c1.prop(data, 'location')
        c1 = row.column(align=True)
        c1.prop(data, 'rotation')

    def _draw_uv_data(self, context, rig, col, morph):
        meshObj = rig.firstMesh()
        if meshObj is None:
            c = col.column(align=True)
            c.label("The model mesh can't be found", icon='ERROR')
            return

        c = col.column(align=True)
        row = c.row(align=True)
        row.operator(operators.morph.ViewUVMorph.bl_idname, text='View')
        row.operator(operators.morph.ClearUVMorphView.bl_idname, text='Clear')
        row = c.row(align=True)
        row.operator(operators.morph.EditUVMorph.bl_idname, text='Edit')
        row.operator(operators.morph.ApplyUVMorph.bl_idname, text='Apply')

        c = col.column(align=True)
        row = c.row(align=True)
        row.label('UV Offsets (%d)'%len(morph.data))
        row.prop(morph, 'uv_index')
        return
        row = c.row()
        row.template_list(
            "UL_UVMorphOffsets", "",
            morph, "data",
            morph, "active_uv_data",
            )

    def _draw_group_data(self, context, rig, col, morph):
        c = col.column(align=True)
        c.label('Group Offsets (%d)'%len(morph.data))
        row = c.row()
        row.template_list(
            "UL_GroupMorphOffsets", "",
            morph, "data",
            morph, "active_group_data"
            )
        tb = row.column()
        tb1 = tb.column(align=True)
        tb1.operator(operators.morph.AddGroupMorphOffset.bl_idname, text='', icon='ZOOMIN')
        tb1.operator(operators.morph.RemoveGroupMorphOffset.bl_idname, text='', icon='ZOOMOUT')
        if len(morph.data) == 0:
            return
        c = col.column(align=True)
        row = c.row(align=True)
        item = morph.data[morph.active_group_data]
        row.prop(item, 'morph_type', text='')
        row.prop_search(item, 'name', morph.id_data.mmd_root, item.morph_type, icon='SHAPEKEY_DATA', text='')


class UL_ObjectsMixIn(object):
    morph_filter = bpy.props.EnumProperty(
        name="Morph Filter",
        items = [
            ('ACTIVE', 'Active Model', '', 0),
            ('ALL', 'All Models', '', 1),
            ],
        default='ACTIVE',
        )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, 'name', text='', emboss=False, icon=self.icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text='', icon=self.icon)

    def draw_filter(self, context, layout):
        row = layout.row()
        row.prop(self, 'morph_filter', expand=True)

    def filter_items(self, context, data, propname):
        objects = getattr(data, propname)
        flt_flags = [~self.bitflag_filter_item] * len(objects)
        flt_neworder = []

        if self.morph_filter == 'ACTIVE':
            active_root = mmd_model.Model.findRoot(context.active_object)
            for i, obj in enumerate(objects):
                if obj.mmd_type == self.mmd_type and mmd_model.Model.findRoot(obj) == active_root:
                    flt_flags[i] = self.bitflag_filter_item
        else:
            for i, obj in enumerate(objects):
                if obj.mmd_type == self.mmd_type:
                    flt_flags[i] = self.bitflag_filter_item

        return flt_flags, flt_neworder

class UL_rigidbodies(UL_ObjectsMixIn, UIList):
    mmd_type = 'RIGID_BODY'
    icon = 'MESH_ICOSPHERE'


class MMDRigidbodySelectorPanel(_PanelBase, Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_rigidbody_list'
    bl_label = 'Rigid Bodies'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        active_obj = context.active_object
        root = None
        if active_obj:
            root = mmd_model.Model.findRoot(active_obj)
        if root is None:
            c = self.layout.column()
            c.label('Select a MMD Model')
            return

        rig = mmd_model.Model(root)
        root = rig.rootObject()
        mmd_root = root.mmd_root
        col = self.layout.column()
        c = col.column(align=True)
        row = c.row()
        row.template_list(
            "UL_rigidbodies",
            "",
            context.scene, "objects",
            mmd_root, 'active_rigidbody_index',
            )
        tb = row.column()
        tb1 = tb.column(align=True)
        tb1.operator(operators.rigid_body.AddRigidBody.bl_idname, text='', icon='ZOOMIN')
        tb1.operator(operators.rigid_body.RemoveRigidBody.bl_idname, text='', icon='ZOOMOUT')

        if mmd_model.isRigidBodyObject(active_obj):
            c = col.column(align=True)
            c.enabled = active_obj.mode == 'OBJECT'
            c.row(align=True).label(active_obj.name, icon='MESH_ICOSPHERE')
            c.row(align=True).prop(active_obj.mmd_rigid, 'shape', expand=True)
            c.column(align=True).prop(active_obj.mmd_rigid, 'size', text='')


class UL_joints(UL_ObjectsMixIn, UIList):
    mmd_type = 'JOINT'
    icon = 'CONSTRAINT'

class MMDJointSelectorPanel(_PanelBase, Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_joint_list'
    bl_label = 'Joints'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        active_obj = context.active_object
        root = None
        if active_obj:
            root = mmd_model.Model.findRoot(active_obj)
        if root is None:
            c = self.layout.column()
            c.label('Select a MMD Model')
            return

        rig = mmd_model.Model(root)
        root = rig.rootObject()
        mmd_root = root.mmd_root
        
        col = self.layout.column()
        c = col.column(align=True)
        
        row = c.row()
        row.template_list(
            "UL_joints",
            "",
            context.scene, "objects",
            mmd_root, 'active_joint_index',
            )
        tb = row.column()
        tb1 = tb.column(align=True)
        tb1.operator(operators.rigid_body.AddJoint.bl_idname, text='', icon='ZOOMIN')
        tb1.operator(operators.rigid_body.RemoveJoint.bl_idname, text='', icon='ZOOMOUT')
