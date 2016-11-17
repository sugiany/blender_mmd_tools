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
            pose_bone = context.active_object.pose.bones.get(edit_bone.name, None)
            if pose_bone is None:
                return
        else:
            pose_bone = context.active_pose_bone

        layout = self.layout
        if pose_bone.is_mmd_shadow_bone:
            layout.label('MMD Shadow Bone!', icon='INFO')
            return

        mmd_bone = pose_bone.mmd_bone

        c = layout.column(align=True)
        c.label('Information:')
        c.prop(mmd_bone, 'name_j')
        c.prop(mmd_bone, 'name_e')
        c.label(text='ID: %d'%(mmd_bone.bone_id))

        c = layout.column(align=True)
        row = c.row()
        row.prop(mmd_bone, 'transform_order')
        row.prop(mmd_bone, 'transform_after_dynamics')
        row = c.row()
        row.prop(mmd_bone, 'is_visible')
        row.prop(mmd_bone, 'is_controllable')
        row = c.row()
        row.prop(mmd_bone, 'is_tip')
        #row.prop(mmd_bone, 'use_tail_location')

        c = layout.column(align=True)
        row = c.row()
        row.active = len([i for i in pose_bone.constraints if i.type == 'IK']) > 0
        row.prop(mmd_bone, 'ik_rotation_constraint')

        c = layout.column(align=True)
        c.prop(mmd_bone, 'enabled_fixed_axis')
        row = c.row()
        row.active = mmd_bone.enabled_fixed_axis
        row.column(align=True).prop(mmd_bone, 'fixed_axis', text='')

        c = layout.column(align=True)
        c.prop(mmd_bone, 'enabled_local_axes')
        row = c.row()
        row.active = mmd_bone.enabled_local_axes
        row.column(align=True).prop(mmd_bone, 'local_axis_x')
        row.column(align=True).prop(mmd_bone, 'local_axis_z')


class MMDBoneATPanel(Panel):
    bl_idname = 'BONE_PT_mmd_tools_bone_at'
    bl_label = 'MMD Additional Transformation'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_ARMATURE' and context.active_bone is not None or context.mode == 'POSE' and context.active_pose_bone is not None

    def draw(self, context):
        if context.mode == 'EDIT_ARMATURE':
            edit_bone = context.active_bone
            pose_bone = context.active_object.pose.bones.get(edit_bone.name, None)
            if pose_bone is None:
                return
        else:
            pose_bone = context.active_pose_bone

        layout = self.layout
        if pose_bone.is_mmd_shadow_bone:
            layout.label('MMD Shadow Bone!', icon='INFO')
            return

        mmd_bone = pose_bone.mmd_bone

        c = layout.column(align=True)
        row = c.row()
        row.prop(mmd_bone, 'has_additional_rotation', text='Rotation')
        row.prop(mmd_bone, 'has_additional_location', text='Location')

        c = layout.column(align=True)
        c.prop_search(mmd_bone, 'additional_transform_bone', pose_bone.id_data.pose, 'bones', icon='BONE_DATA', text='')
        c.prop(mmd_bone, 'additional_transform_influence', text='Influence', slider=True)
        if mmd_bone.is_additional_transform_dirty:
            c.label(text='Changes has not been applied.', icon='ERROR')
        else:
            c.label()

