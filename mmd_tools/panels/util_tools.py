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
                layout.label(text=item.name, translate=False, icon='MATERIAL')
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
