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
        if active_obj is not None and active_obj.type == 'MESH':
            col.operator('mmd_tools.separate_by_materials', text='Separate By Materials')

        if active_obj is None:
            return

        root = mmd_model.Model.findRoot(active_obj)
        if root is None:
            return

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
        col.operator(operators.fileio.ImportVmdToMMDModel.bl_idname, text='Import Motion')
        col.operator(operators.fileio.ExportPmx.bl_idname, text='Export Model')


class MMD_ROOT_UL_display_item_frames(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mmd_root = data
        frame = item

        if self.layout_type in {'DEFAULT'}:
            layout.label(text=frame.name, translate=False, icon_value=icon)
            if frame.is_special:
                layout.label(text='', icon='LOCKED')
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class MMD_ROOT_UL_display_items(UIList):
    morph_filter = bpy.props.EnumProperty(
        name="Morph Filter",
        items = [
            ('OTHER', 'Other', '', 4),
            ('MOUTH', 'Mouth', '', 3),
            ('EYE', 'Eye', '', 2),
            ('EYEBROW', 'Eye Brow', '', 1),
            ('SYSTEM', 'System', '', 0),
            ('NONE', 'All', '', 10),
            ],
        default='NONE',
        )

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mmd_root = data

        if self.layout_type in {'DEFAULT'}:
            if item.type == 'BONE':
                ic = 'BONE_DATA'
            else:
                ic = 'SHAPEKEY_DATA'
            layout.label(text=item.name, translate=False, icon=ic)
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
            if item.morph_category == self.morph_filter:
                flt_flags[i] = self.bitflag_filter_item

        return flt_flags, flt_neworder


    def draw_filter(self, context, layout):
        row = layout.row()
        row.prop(self, 'morph_filter')


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
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        c.prop(frame, 'name')

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
            row.prop_search(item, 'name', rig.armature().pose, 'bones', icon='BONE_DATA', text='')

            row = col.row(align=True)
            row.operator(operators.display_item.SelectCurrentDisplayItem.bl_idname, text='Select')
        elif item.type == 'MORPH':
            row.prop(item, 'morph_category', text='')
            row.prop(item, 'name', text='')

            for i in rig.meshes():
                if i.data.shape_keys is not None and item.name in i.data.shape_keys.key_blocks:
                    row = col.row(align=True)
                    row.label(i.name+':')
                    row.prop(i.data.shape_keys.key_blocks[item.name], 'value')



class UL_Morphs(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT'}:            
            layout.label(text=item.name, translate=False, icon='SHAPEKEY_DATA')
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
            
               
class UL_BoneMorphOffsets(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT'}:            
            layout.label(text=item.bone, translate=False, icon='BONE_DATA')
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
        items_map = {"MATMORPH":"material_morphs", 
                 "BONEMORPH":"bone_morphs", 
                 "VTXMORPH":"vertex_morphs"}      
        col = self.layout.column()
        c = col.column(align=True)
        c.label('Morphs')
        row = c.row()
        row.template_list(
            "UL_Morphs", "",
            mmd_root, items_map[mmd_root.active_morph_type],
            mmd_root, "active_morph"
            )
        tb = row.column()
        tb1 = tb.column(align=True)
        if mmd_root.active_morph_type == "VTXMORPH":
            tb1.operator(operators.morph.AddVertexMorph.bl_idname, text='', icon='ZOOMIN')   
        elif mmd_root.active_morph_type == "MATMORPH":
            tb1.operator(operators.morph.AddMaterialMorph.bl_idname, text='', icon='ZOOMIN')
        elif mmd_root.active_morph_type == "BONEMORPH":
            tb1.operator(operators.morph.AddBoneMorph.bl_idname, text='', icon='ZOOMIN')
        tb1.operator(operators.morph.RemoveMorph.bl_idname, text='', icon='ZOOMOUT')
        tb.separator()
        tb1 = tb.column(align=True)
        tb1.operator(operators.morph.MoveUpMorph.bl_idname, text='', icon='TRIA_UP')
        tb1.operator(operators.morph.MoveDownMorph.bl_idname, text='', icon='TRIA_DOWN')
        c.prop(mmd_root, 'active_morph_type', text='Active')  
        
        items = getattr(mmd_root, items_map[mmd_root.active_morph_type])      
        if mmd_root.active_morph < len(items):
            morph = items[mmd_root.active_morph]
            c = col.column(align=True)
            row = c.row()
            row.prop(morph, 'name')
            row = c.row()
            row.prop(morph, 'name_e')
            row = c.row()
            row.prop(morph, 'category') 
            
            if mmd_root.active_morph_type == "MATMORPH":
                self.__draw_material_data(rig, col, morph)
            elif mmd_root.active_morph_type == "BONEMORPH":
                self.__draw_bone_data(rig, col, morph)
                
                
    def __draw_material_data(self, rig, col, morph):
        meshObj = None
        for i in rig.meshes():
            meshObj = i 
            break
        if meshObj is None:
            c = col.column(align=True)
            c.label("The model mesh can't be found", icon='ERROR')
            return
        c = col.column(align=True)
        c.label('Material Offsets')
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
        c.prop_search(data, 'material', meshObj.data, 'materials')
         
        base_mat = meshObj.data.materials[data.material] # Base Material of this Offset
        if "_temp" in base_mat.name:
            c = col.column(align=True)
            c.label('This is not a valid base material', icon='ERROR')
            return
         
        work_mat = None # Temporary material to edit this offset (and see a live preview)
        work_mat_name = base_mat.name + "_temp"
        if work_mat_name in meshObj.data.materials.keys():
            work_mat = meshObj.data.materials[work_mat_name] 
        else:
            c = col.column(align=True)
            row = c.row()
            row.operator(operators.morph.CreateWorkMaterial.bl_idname) 
            row.operator(operators.morph.ClearTempMaterials.bl_idname, text='Clear')
        if work_mat is not None:            
            c = col.column(align=True)
            row = c.row()
            row.prop(data, 'offset_type')
            row = c.row()
            row.prop(work_mat, 'diffuse_color')
            row = c.row()
            row.label('Diffuse Alpha:')
            row.prop(work_mat, 'alpha')
            row = c.row()
            row.prop(work_mat, 'specular_color') 
            row = c.row()
            row.label('Specular Alpha:')
            row.prop(work_mat, 'specular_alpha')            
            row = c.row()
            row.prop(work_mat.mmd_material, 'ambient_color')
            row = c.row()
            row.prop(work_mat.mmd_material, 'edge_color')
            row = c.row()
            row.prop(work_mat.mmd_material, 'edge_weight')
            row = c.row()
            row.prop(data, 'texture_factor')
            row = c.row()
            row.prop(data, 'sphere_texture_factor')
            row = c.row()
            row.prop(data, 'toon_texture_factor')
            row = c.row()
            row.operator(operators.morph.ApplyMaterialOffset.bl_idname, text='Apply')
            row.operator(operators.morph.ClearTempMaterials.bl_idname, text='Clear')
            
    def __draw_bone_data(self, rig, col, morph):
        armature = rig.armature()
        if armature.type != 'ARMATURE':
            c = col.column(align=True)
            c.label('Armature not found', icon='ERROR')
            return
        c = col.column(align=True)
        c.label('Bone Offsets')
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
        c.prop_search(data, 'bone', armature.pose, 'bones')
        if data.bone in armature.pose.bones.keys():
            c = col.column(align=True)
            row = c.row()
            row.operator(operators.morph.SelectRelatedBone.bl_idname, text='Select')
            row.operator(operators.morph.EditBoneOffset.bl_idname, text='Edit')
            row.operator(operators.morph.AssignBoneToOffset.bl_idname, text='Assign')
            row = c.row()
            row.operator('pose.transforms_clear', text='Clear')
            row.operator(operators.morph.ApplyBoneOffset.bl_idname, text='Apply')
        else:
            c = col.column(align=True)
            row = c.row()
            row.operator(operators.morph.AssignBoneToOffset.bl_idname, text='Assign')
            

class UL_ObjectsMixIn(object):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, 'name', text='', emboss=False, icon=self.icon)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text='', icon=self.icon)

    def draw_filter(self, context, layout):
        pass

    def filter_items(self, context, data, propname):
        objects = getattr(data, propname)
        flt_flags = [~self.bitflag_filter_item] * len(objects)
        flt_neworder = []

        for i, obj in enumerate(objects):
            if obj.mmd_type == self.mmd_type:
                flt_flags[i] = self.bitflag_filter_item

        return flt_flags, flt_neworder

class UL_rigidbodies(UL_ObjectsMixIn, UIList):
    mmd_type = 'RIGID_BODY'
    icon = 'MESH_ICOSPHERE'


class MMDRigidbodySelectorPanel(_PanelBase, Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_rigidbody_list'
    bl_label = 'Rigidbodies'
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
        self.layout.template_list(
            "UL_rigidbodies",
            "",
            context.scene, "objects",
            mmd_root, 'active_rigidbody_index',
            )


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

        self.layout.template_list(
            "UL_joints",
            "",
            context.scene, "objects",
            mmd_root, 'active_joint_index',
            )
