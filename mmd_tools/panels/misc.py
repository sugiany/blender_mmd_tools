# -*- coding: utf-8 -*-

from bpy.types import Panel

from mmd_tools import operators

class MMDToolsObjectPanel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_object'
    bl_label = 'Object'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'MMD Tools'
    bl_context = ''

    def draw(self, context):
        active_obj = context.active_object

        layout = self.layout

        col = layout.column()
        col.label('Model:')
        c = col.column(align=True)
        c.operator(operators.model.CreateMMDModelRoot.bl_idname, text='Create')
        c.operator(operators.fileio.ImportPmx.bl_idname, text='Import')

        col.label('Motion(vmd):')
        c = col.column()
        c.operator('mmd_tools.import_vmd', text='Import')


        if active_obj is not None and active_obj.type == 'MESH':
            col = layout.column(align=True)
            col.label('Mesh:')
            c = col.column()
            c.operator('mmd_tools.separate_by_materials', text='Separate by materials')

        col = layout.column(align=True)
        col.label('Scene:')
        c = col.column(align=True)
        c.operator('mmd_tools.set_frame_range', text='Set frame range')
