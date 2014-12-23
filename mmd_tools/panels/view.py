# -*- coding: utf-8 -*-

from bpy.types import Panel

class MMDViewPanel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_view'
    bl_label = 'MMD View Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'MMD Tools'
    bl_context = ''

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.label('View:')
        c = col.column(align=True)
        r = c.row(align=True)
        r.operator('mmd_tools.set_glsl_shading', text='GLSL')
        r.operator('mmd_tools.set_shadeless_glsl_shading', text='Shadeless')
        r = c.row(align=True)
        r.operator('mmd_tools.set_cycles_rendering', text='Cycles')
        r.operator('mmd_tools.reset_shading', text='Reset')
