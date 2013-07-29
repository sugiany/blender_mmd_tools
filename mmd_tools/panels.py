# -*- coding: utf-8 -*-

from bpy.types import Panel
from . import operators
from . import rigging

class MMDToolsObjectPanel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_object'
    bl_label = 'MMD Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = ''

    def draw(self, context):
        active_obj = context.active_object

        layout = self.layout

        col = layout.column(align=True)
        col.label('Import:')
        c = col.column()
        r = c.row()
        r.operator('mmd_tools.import_model', text='Model')
        r.operator('mmd_tools.import_vmd', text='Motion')

        col.label('Export:')
        c = col.column()
        r = c.row()
        r.operator('mmd_tools.export_pmx', text='Model')

        if active_obj is not None and active_obj.type == 'MESH':
            col = layout.column(align=True)
            col.label('Mesh:')
            c = col.column()
            c.operator('mmd_tools.separate_by_materials', text='Separate by materials')
        if active_obj is not None and active_obj.type == 'MESH':
            col = layout.column(align=True)
            col.label('Material:')
            c = col.column()
            c.operator('mmd_tools.set_shadeless_materials', text='Shadeless')

        col = layout.column(align=True)
        col.label('Scene:')
        c = col.column(align=True)
        c.operator('mmd_tools.set_frame_range', text='Set frame range')


class MMDRootPanel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_root'
    bl_label = 'MMD Model Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if obj is None:
            c = layout.column()
            c.label('No object is selected.')
            return

        root = rigging.Rig.findRoot(obj)
        if root is None:
            c = layout.column()
            c.label('Create MMD Model')
            return

        rig = rigging.Rig(root)
        arm = rig.armature()

        c = layout.column()
        c.prop(root.mmd_root, 'name')
        c.prop(root.mmd_root, 'name_e')
        c.prop(root.mmd_root, 'scale')

        c = layout.column(align=True)
        c.prop(root.mmd_root, 'show_armature')
        c.prop(root.mmd_root, 'show_rigid_bodies')
        c.prop(root.mmd_root, 'show_joints')
        c.prop(root.mmd_root, 'show_temporary_objects')

        col = self.layout.column(align=True)

        if not root.mmd_root.is_built:
            col.label(text='Press the "Build" button before playing the physical animation.', icon='ERROR')
        row = col.row(align=True)
        row.operator('mmd_tools.build_rig')
        row.operator('mmd_tools.clean_rig')

        col = self.layout.column()
        col.operator(operators.ImportVmdToMMDModel.bl_idname, text='Import Motion')


class MMDViewPanel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_view'
    bl_label = 'MMD View Tools'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label('View:')
        c = col.column(align=True)
        r = c.row()
        r.operator('mmd_tools.set_glsl_shading', text='GLSL')
        r.operator('mmd_tools.set_shadeless_glsl_shading', text='Shadeless')
        r = c.row()
        r.operator('mmd_tools.set_cycles_rendering', text='Cycles')
        r.operator('mmd_tools.reset_shading', text='Reset')

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
        r.prop(mmd_material, 'sphere_texture_type')
        r = c.row()
        r.prop(mmd_material, 'comment')

class MMDCameraPanel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_camera'
    bl_label = 'MMD Camera Tools'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        from . import mmd_camera
        obj = context.active_object
        return obj is not None and (obj.type == 'CAMERA' or mmd_camera.MMDCamera.isMMDCamera(obj))

    def draw(self, context):
        from . import mmd_camera
        obj = context.active_object

        layout = self.layout

        if mmd_camera.MMDCamera.isMMDCamera(obj):
            mmd_cam = mmd_camera.MMDCamera(obj)
            empty = mmd_cam.object()
            camera = mmd_cam.camera()

            row = layout.row(align=True)

            c = row.column()
            c.prop(empty, 'location')
            c.prop(camera, 'location', index=1, text='Distance')

            c = row.column()
            c.prop(empty, 'rotation_euler')

            row = layout.row(align=True)
            row.prop(empty.mmd_camera, 'angle')
            row = layout.row(align=True)
            row.prop(empty.mmd_camera, 'is_perspective')
        else:
            col = layout.column(align=True)

            c = col.column()
            r = c.row()
            r.operator('mmd_tools.convert_to_mmd_camera', 'Convert')

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

class MMDRigidPanel(Panel):
    bl_idname = 'RIGID_PT_mmd_tools_bone'
    bl_label = 'MMD Rigid Tools'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.mmd_type == 'RIGID_BODY'

    def draw(self, context):
        from . import rigging
        obj = context.active_object

        layout = self.layout
        c = layout.column()
        c.prop(obj, 'name')
        c.prop(obj.mmd_rigid, 'name_e')

        row = layout.row(align=True)
        row.prop(obj.mmd_rigid, 'type')

        armature = rigging.findArmatureObject(obj)
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
