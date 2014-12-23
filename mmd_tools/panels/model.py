# -*- coding: utf-8 -*-

from bpy.types import Panel, UIList

from mmd_tools import rigging, operators


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

class MMDDisplayItemsPanel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_display_items'
    bl_label = 'MMD Display Items'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'MMD Tools'


    def draw(self, context):
        active_obj = context.active_object
        root = None
        if active_obj:
            root = rigging.Rig.findRoot(active_obj)
        if root is None:
            c = self.layout.column()
            c.label('Select a MMD Model')
            return

        rig = rigging.Rig(root)
        arm = rig.armature()
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
        item = frame.items[frame.active_item]
        row = col.row(align=True)
        row.prop(item, 'type', text='')
        if item.type == 'BONE':
            row.prop_search(item, 'name', rig.armature().pose, 'bones', icon='BONE_DATA', text='')

            row = col.row(align=True)
            row.operator(operators.display_item.SelectCurrentDisplayItem.bl_idname, text='Select')
        elif item.type == 'MORPH':
            row.prop(item, 'name', text='')

            for i in rig.meshes():
                if item.name in i.data.shape_keys.key_blocks:
                    row = col.row(align=True)
                    row.label(i.name+':')
                    row.prop(i.data.shape_keys.key_blocks[item.name], 'value')


class MMDRootPanel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_root'
    bl_label = 'MMD Model Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'MMD Tools'
    bl_context = ''

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if obj is None:
            c = layout.column()
            c.label('No object is selected.')
            return

        root = rigging.Rig.findRoot(obj)
        if root is None:
            c = layout.column()
            c.label('Create MMD Model')
            return

        rig = rigging.Rig(root)
        arm = rig.armature()

        c = layout.column()
        c.prop(root.mmd_root, 'name')
        c.prop(root.mmd_root, 'name_e')
        c.prop(root.mmd_root, 'scale')

        c = layout.column(align=True)
        c.prop(root.mmd_root, 'show_meshes')
        c.prop(root.mmd_root, 'show_armature')
        c.prop(root.mmd_root, 'show_rigid_bodies')
        c.prop(root.mmd_root, 'show_joints')
        c.prop(root.mmd_root, 'show_temporary_objects')

        c = layout.column(align=True)
        c.prop(root.mmd_root, 'show_names_of_rigid_bodies')
        c.prop(root.mmd_root, 'show_names_of_joints')



        col = self.layout.column(align=True)

        if not root.mmd_root.is_built:
            col.label(text='Press the "Build" button before playing the physical animation.', icon='ERROR')
        row = col.row(align=True)
        row.operator('mmd_tools.build_rig')
        row.operator('mmd_tools.clean_rig')
        col.operator('mmd_tools.apply_additioinal_transform')

        col = self.layout.column(align=True)
        col.operator(operators.fileio.ImportVmdToMMDModel.bl_idname, text='Import Motion')
        col.operator(operators.fileio.ExportPmx.bl_idname, text='Export Model')
