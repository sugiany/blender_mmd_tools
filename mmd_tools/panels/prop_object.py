# -*- coding: utf-8 -*-

import bpy
from bpy.types import Panel

import mmd_tools.core.model as mmd_model


class _PanelBase(object):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'


class MMDModelObjectPanel(_PanelBase, Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_root_object'
    bl_label = 'MMD Model Information'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None:
            return False

        root = mmd_model.Model.findRoot(obj)
        if root is None:
            return False

        return True

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        root = mmd_model.Model.findRoot(obj)

        c = layout.column()
        c.prop(root.mmd_root, 'name')
        c.prop(root.mmd_root, 'name_e')
        c.prop(root.mmd_root, 'scale')
        c = layout.column()
        c.prop_search(root.mmd_root, 'comment_text', search_data=bpy.data, search_property='texts')
        c.prop_search(root.mmd_root, 'comment_e_text', search_data=bpy.data, search_property='texts')
        c = layout.column()
        c.operator('mmd_tools.change_mmd_ik_loop_factor', text='Change MMD IK Loop Factor')


class MMDRigidPanel(_PanelBase, Panel):
    bl_idname = 'RIGID_PT_mmd_tools_bone'
    bl_label = 'MMD Rigid Body'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.mmd_type == 'RIGID_BODY'

    def draw(self, context):
        obj = context.active_object

        layout = self.layout
        c = layout.column()
        c.prop(obj.mmd_rigid, 'name_j')
        c.prop(obj.mmd_rigid, 'name_e')

        c = layout.column(align=True)
        row = c.row(align=True)
        row.prop(obj.mmd_rigid, 'type', expand=True)

        root = mmd_model.Model.findRoot(obj)
        if root is None:
            row = c.row(align=True)
            row.enabled = False
            row.prop(obj.mmd_rigid, 'bone', text='', icon='BONE_DATA')
        else:
            row = c.row(align=True)
            armature = mmd_model.Model(root).armature()
            row.prop_search(obj.mmd_rigid, 'bone', text='', search_data=armature.pose, search_property='bones', icon='BONE_DATA')

        c = layout.column(align=True)
        c.enabled = obj.mode == 'OBJECT'
        c.row(align=True).prop(obj.mmd_rigid, 'shape', expand=True)
        c.column(align=True).prop(obj.mmd_rigid, 'size', text='')

        row = layout.row()
        if obj.rigid_body is None:
            row.operator('rigidbody.object_add', icon='MESH_ICOSPHERE')
            return

        c = row.column()
        c.prop(obj.rigid_body, 'mass')
        c.prop(obj.mmd_rigid, 'collision_group_number')
        c = row.column()
        c.prop(obj.rigid_body, 'restitution')
        c.prop(obj.rigid_body, 'friction')

        c = layout.column()
        #c.prop(obj.mmd_rigid, 'collision_group_mask')
        col = c.column(align=True)
        col.label('Collision Group Mask:')
        row = col.row(align=True)
        for i in range(0, 8):
            row.prop(obj.mmd_rigid, 'collision_group_mask', index=i, text=str(i), toggle=True)
        row = col.row(align=True)
        for i in range(8, 16):
            row.prop(obj.mmd_rigid, 'collision_group_mask', index=i, text=str(i), toggle=True)

        c = layout.column()
        c.label('Damping')
        row = c.row()
        row.prop(obj.rigid_body, 'linear_damping')
        row.prop(obj.rigid_body, 'angular_damping')


class MMDJointPanel(_PanelBase, Panel):
    bl_idname = 'JOINT_PT_mmd_tools_bone'
    bl_label = 'MMD Joint'
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
        if rbc is None:
            c.operator('rigidbody.constraint_add', icon='CONSTRAINT').type='GENERIC_SPRING'
        else:
            c.prop(rbc, 'object1')
            c.prop(rbc, 'object2')

            row = layout.row(align=True)
            col = row.column(align=True)
            col.label('X-Axis:')
            col.label('Y-Axis:')
            col.label('Z-Axis:')
            col = row.column(align=True)
            row = col.row(align=True)
            row.prop(rbc, 'limit_lin_x_lower')
            row.prop(rbc, 'limit_lin_x_upper')
            row = col.row(align=True)
            row.prop(rbc, 'limit_lin_y_lower')
            row.prop(rbc, 'limit_lin_y_upper')
            row = col.row(align=True)
            row.prop(rbc, 'limit_lin_z_lower')
            row.prop(rbc, 'limit_lin_z_upper')

            row = layout.row(align=True)
            col = row.column(align=True)
            col.label('X-Axis:')
            col.label('Y-Axis:')
            col.label('Z-Axis:')
            col = row.column(align=True)
            row = col.row(align=True)
            row.prop(rbc, 'limit_ang_x_lower')
            row.prop(rbc, 'limit_ang_x_upper')
            row = col.row(align=True)
            row.prop(rbc, 'limit_ang_y_lower')
            row.prop(rbc, 'limit_ang_y_upper')
            row = col.row(align=True)
            row.prop(rbc, 'limit_ang_z_lower')
            row.prop(rbc, 'limit_ang_z_upper')

        col = layout.column()
        row = col.row()
        row.column(align=True).prop(obj.mmd_joint, 'spring_linear')
        row.column(align=True).prop(obj.mmd_joint, 'spring_angular')

