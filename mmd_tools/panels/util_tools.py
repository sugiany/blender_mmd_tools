# -*- coding: utf-8 -*-

from bpy.types import Panel, UIList

from mmd_tools.core.model import Model

class _PanelBase(object):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'mmd_utils'

class UL_Materials(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT'}:    
            if item:        
                row = layout.row(align=True)
                item_prop = getattr(item, 'mmd_material')
                row.prop(item_prop, 'name_j', text='', emboss=False, icon='MATERIAL')
                row.prop(item_prop, 'name_e', text='', emboss=True)
            else:
                layout.label(text='UNSET', translate=False, icon='ERROR')
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def draw_filter(self, context, layout):
        layout.label(text="Use the arrows to sort", icon='INFO')

class MMDMaterialSorter(_PanelBase, Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_material_sorter'
    bl_label = 'Material Sorter'
    bl_context = ''

    def draw(self, context):
        layout = self.layout
        active_obj = context.active_object
        if (active_obj is None or active_obj.type != 'MESH' or
            active_obj.mmd_type != 'NONE'):
            layout.label("Select a mesh object")
            return

        col = layout.column(align=True)
        row = col.row()
        row.template_list("UL_Materials", "",
                          active_obj.data, "materials",
                          active_obj, "active_material_index")
        tb = row.column()
        tbl = tb.column(align=True)
        tbl.operator('mmd_tools.move_material_up', text='', icon='TRIA_UP')
        tbl.operator('mmd_tools.move_material_down', text='', icon='TRIA_DOWN')

class UL_ModelMeshes(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT'}:           
            layout.label(text=item.name, translate=False, icon='OBJECT_DATA')
        elif self.layout_type in {'COMPACT'}:
            pass
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

    def draw_filter(self, context, layout):
        layout.label(text="Use the arrows to sort", icon='INFO')

    def filter_items(self, context, data, propname):
        # We will use the filtering to sort the mesh objects to match the rig order
        objects = getattr(data, propname)
        flt_flags = [~self.bitflag_filter_item] * len(objects)
        flt_neworder = list(range(len(objects)))
        active_root = Model.findRoot(context.active_object)
        #rig = Model(active_root)
        #for i, obj in enumerate(objects):
        #    if (obj.type == 'MESH' and obj.mmd_type == 'NONE'
        #            and Model.findRoot(obj) == active_root):
        #        flt_flags[i] = self.bitflag_filter_item
        #        new_index = rig.getMeshIndex(obj.name)
        #        flt_neworder[i] = new_index
        name_dict = {}
        for i, obj in enumerate(objects):
            if (obj.type == 'MESH' and obj.mmd_type == 'NONE'
                    and Model.findRoot(obj) == active_root):
                flt_flags[i] = self.bitflag_filter_item
                name_dict[obj.name] = i

        for new_index, name in enumerate(sorted(name_dict.keys())):
            i = name_dict[name]
            flt_neworder[i] = new_index

        return flt_flags, flt_neworder


class MMDMeshSorter(_PanelBase, Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_meshes_sorter'
    bl_label = 'Meshes Sorter'
    bl_context = ''

    def draw(self, context):
        layout = self.layout
        active_obj = context.active_object
        root = Model.findRoot(active_obj)
        if root is None:
            layout.label("Select a MMD Model")
            return
        rig = Model(root)
        if rig.firstMesh() is None:
            layout.label("This model don't have meshes")
            return

        col = layout.column(align=True)
        row = col.row()
        row.template_list("UL_ModelMeshes", "",
                          context.scene, "objects",
                          root.mmd_root, "active_mesh_index")
        tb = row.column()
        tbl = tb.column(align=True)
        tbl.operator('mmd_tools.move_mesh_up', text='', icon='TRIA_UP')
        tbl.operator('mmd_tools.move_mesh_down', text='', icon='TRIA_DOWN')
