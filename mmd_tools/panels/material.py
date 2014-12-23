# -*- coding: utf-8 -*-

from bpy.types import Panel

class MMDMaterialPanel(Panel):
    bl_idname = 'MATERIAL_PT_mmd_tools_material'
    bl_label = 'MMD Material Tools'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        material = context.active_object.active_material
        mmd_material = material.mmd_material

        layout = self.layout

        col = layout.column(align=True)
        col.label('Information:')
        c = col.column()
        r = c.row()
        r.prop(mmd_material, 'name_j')
        r = c.row()
        r.prop(mmd_material, 'name_e')

        col = layout.column(align=True)
        col.label('Color:')
        c = col.column()
        r = c.row()
        r.prop(material, 'diffuse_color')
        r = c.row()
        r.label('Diffuse Alpha:')
        r.prop(material, 'alpha')
        r = c.row()
        r.prop(mmd_material, 'ambient_color')
        r = c.row()
        r.prop(material, 'specular_color')
        r = c.row()
        r.label('Specular Alpha:')
        r.prop(material, 'specular_alpha')

        col = layout.column(align=True)
        col.label('Shadow:')
        c = col.column()
        r = c.row()
        r.prop(mmd_material, 'is_double_sided')
        r.prop(mmd_material, 'enabled_drop_shadow')
        r = c.row()
        r.prop(mmd_material, 'enabled_self_shadow_map')
        r.prop(mmd_material, 'enabled_self_shadow')

        col = layout.column(align=True)
        col.label('Edge:')
        c = col.column()
        r = c.row()
        r.prop(mmd_material, 'enabled_toon_edge')
        r.prop(mmd_material, 'edge_weight')
        r = c.row()
        r.prop(mmd_material, 'edge_color')

        col = layout.column(align=True)
        col.label('Other:')
        c = col.column()
        r = c.row()
        r.prop(mmd_material, 'is_shared_toon_texture')
        r.prop(mmd_material, 'shared_toon_texture')
        r = c.row()
        r.prop(mmd_material, 'sphere_texture_type')
        r = c.row()
        r.prop(mmd_material, 'comment')
