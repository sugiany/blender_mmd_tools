# -*- coding: utf-8 -*-

from bpy.types import Panel

import mmd_tools.core.model as mmd_model

class MMDRigidPanel(Panel):
    bl_idname = 'RIGID_PT_mmd_tools_bone'
    bl_label = 'MMD Rigid Tool'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.mmd_type == 'RIGID_BODY'

    def draw(self, context):
        obj = context.active_object

        layout = self.layout
        c = layout.column()
        c.prop(obj, 'name')
        c.prop(obj.mmd_rigid, 'name_e')

        row = layout.row(align=True)
        row.prop(obj.mmd_rigid, 'type')

        root = mmd_model.Rig.findRoot(obj)
        rig = mmd_model.Rig(root)
        armature = rig.armature()
        relation = obj.constraints.get('mmd_tools_rigid_parent')
        if relation is not None:
            row.prop_search(relation, 'subtarget', text='', search_data=armature.pose, search_property='bones', icon='BONE_DATA')
        else:
            row.prop_search(obj.mmd_rigid, 'bone', text='', search_data=armature.pose, search_property='bones', icon='BONE_DATA')
        row = layout.row()

        c = row.column()
        c.prop(obj.rigid_body, 'mass')
        c.prop(obj.mmd_rigid, 'collision_group_number')
        c = row.column()
        c.prop(obj.rigid_body, 'restitution', text='Bounciness')
        c.prop(obj.rigid_body, 'friction')

        c = layout.column()
        c.prop(obj.mmd_rigid, 'collision_group_mask')

        c = layout.column()
        c.label('Damping')
        row = c.row()
        row.prop(obj.rigid_body, 'linear_damping')
        row.prop(obj.rigid_body, 'angular_damping')


class MMDJointPanel(Panel):
    bl_idname = 'JOINT_PT_mmd_tools_bone'
    bl_label = 'MMD Joint Tools'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.mmd_type == 'JOINT'

    def draw(self, context):
        obj = context.active_object
        rbc = obj.rigid_body_constraint

        layout = self.layout
        c = layout.column()
        c.prop(obj.mmd_joint, 'name_j')
        c.prop(obj.mmd_joint, 'name_e')

        c = layout.column()
        c.prop(rbc, 'object1')
        c.prop(rbc, 'object2')

        col = layout.column()
        row = col.row(align=True)
        row.label('X-Axis:')
        row.prop(rbc, 'limit_lin_x_lower')
        row.prop(rbc, 'limit_lin_x_upper')
        row = col.row(align=True)
        row.label('Y-Axis:')
        row.prop(rbc, 'limit_lin_y_lower')
        row.prop(rbc, 'limit_lin_y_upper')
        row = col.row(align=True)
        row.label('Z-Axis:')
        row.prop(rbc, 'limit_lin_z_lower')
        row.prop(rbc, 'limit_lin_z_upper')

        col = layout.column()
        row = col.row(align=True)
        row.label('X-Axis:')
        row.prop(rbc, 'limit_ang_x_lower')
        row.prop(rbc, 'limit_ang_x_upper')
        row = col.row(align=True)
        row.label('Y-Axis:')
        row.prop(rbc, 'limit_ang_y_lower')
        row.prop(rbc, 'limit_ang_y_upper')
        row = col.row(align=True)
        row.label('Z-Axis:')
        row.prop(rbc, 'limit_ang_z_lower')
        row.prop(rbc, 'limit_ang_z_upper')

        col = layout.column()
        col.label('Spring(Linear):')
        row = col.row()
        row.prop(obj.mmd_joint, 'spring_linear', text='')
        col.label('Spring(Angular):')
        row = col.row()
        row.prop(obj.mmd_joint, 'spring_angular', text='')
