# -*- coding: utf-8 -*-

from bpy.types import Panel

class MMDBonePanel(Panel):
    bl_idname = 'BONE_PT_mmd_tools_bone'
    bl_label = 'MMD Bone Tools'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_ARMATURE' and context.active_bone is not None or context.mode == 'POSE' and context.active_pose_bone is not None

    def draw(self, context):
        if context.mode == 'EDIT_ARMATURE':
            edit_bone = context.active_bone
            pose_bone = context.active_object.pose.bones[edit_bone.name]
        else:
            pose_bone = context.active_pose_bone

        layout = self.layout
        c = layout.column(align=True)

        c.label('Information:')
        c.prop(pose_bone.mmd_bone, 'name_j')
        c.prop(pose_bone.mmd_bone, 'name_e')

        c = layout.column(align=True)
        row = c.row()
        row.prop(pose_bone.mmd_bone, 'transform_order')
        row.prop(pose_bone.mmd_bone, 'transform_after_dynamics')
        row.prop(pose_bone.mmd_bone, 'is_visible')
        row = c.row()
        row.prop(pose_bone.mmd_bone, 'is_controllable')
        row.prop(pose_bone.mmd_bone, 'is_tip')
        row.prop(pose_bone.mmd_bone, 'enabled_local_axes')

        row = layout.row(align=True)
        c = row.column()
        c.prop(pose_bone.mmd_bone, 'local_axis_x')
        c = row.column()
        c.prop(pose_bone.mmd_bone, 'local_axis_z')

        c = layout.column()

        c.label('Additional Transformation:')
        if pose_bone.mmd_bone.is_additional_transform_dirty:
            c.label(text='Changes has not been applied.', icon='ERROR')
        row = c.row()
        row.prop(pose_bone.mmd_bone, 'has_additional_rotation', text='Rotation')
        row.prop(pose_bone.mmd_bone, 'has_additional_location', text='Location')
        c.prop_search(pose_bone.mmd_bone, 'additional_transform_bone', pose_bone.id_data.pose, 'bones', icon='BONE_DATA', text='')
        c.prop(pose_bone.mmd_bone, 'additional_transform_influence', text='Influence')
