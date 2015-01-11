# -*- coding: utf-8 -*-

from bpy.types import Panel

class MMDMaterialPanel(Panel):
    bl_idname = 'MATERIAL_PT_mmd_tools_material'
    bl_label = 'MMD Material'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    @classmethod
    def poll(cls, context):
        material = context.active_object.active_material
        return material and material.mmd_material

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
        r = c.row()
        r.prop(mmd_material, 'comment')

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


class MMDTexturePanel(Panel):
    bl_idname = 'MATERIAL_PT_mmd_tools_texture'
    bl_label = 'MMD Texture'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'

    @classmethod
    def poll(cls, context):
        material = context.active_object.active_material
        return material and material.mmd_material

    def draw(self, context):
        material = context.active_object.active_material
        mmd_material = material.mmd_material

        layout = self.layout


        tex_slots = material.texture_slots.values()
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label('Texture:')
        r = row.column(align=True)
        if tex_slots[0]:
            tex = tex_slots[0].texture
            if tex.type == 'IMAGE' and tex.image:
                r2 = r.row(align=True)
                r2.prop(tex.image, 'filepath', text='')
                r2.operator('mmd_tools.material_remove_texture', text='', icon='PANEL_CLOSE')
            else:
                r.operator('mmd_tools.material_remove_texture', text='Remove', icon='PANEL_CLOSE')
                col.label('Texture is invalid.', icon='ERROR')
        else:
            r.operator('mmd_tools.material_open_texture', text='Add', icon='FILESEL')

        row = col.row(align=True)
        row.label('Sphere Texture:')
        r = row.column(align=True)
        if tex_slots[1]:
            tex = tex_slots[1].texture
            if tex.type == 'IMAGE' and tex.image:
                r2 = r.row(align=True)
                r2.prop(tex.image, 'filepath', text='')
            else:
                r.operator('mmd_tools.material_remove_sphere_texture', text='Remove', icon='PANEL_CLOSE')
                col.label('Sphere Texture is invalid.', icon='ERROR')
        else:
            r.operator('mmd_tools.material_open_texture', text='Add', icon='FILESEL')

        col = layout.column(align=True)
        c = col.column()
        r = c.row()
        r.prop(mmd_material, 'is_shared_toon_texture')
        if mmd_material.is_shared_toon_texture:
            r.prop(mmd_material, 'shared_toon_texture')
        r = c.row()
        r.prop(mmd_material, 'toon_texture')
        r = c.row()
        r.prop(mmd_material, 'sphere_texture_type')
