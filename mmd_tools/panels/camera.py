# -*- coding: utf-8 -*-

from bpy.types import Panel

import mmd_tools.core.camera as mmd_camera

class MMDCameraPanel(Panel):
    bl_idname = 'OBJECT_PT_mmd_tools_camera'
    bl_label = 'MMD Camera Tools'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and (obj.type == 'CAMERA' or mmd_camera.MMDCamera.isMMDCamera(obj))

    def draw(self, context):
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
