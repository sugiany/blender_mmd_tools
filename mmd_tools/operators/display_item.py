# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator

from mmd_tools import rigging


class AddDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.add_display_item_frame'
    bl_label = 'Add Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        item = mmd_root.display_item_frames.add()
        item.name = 'Display Frame'
        return {'FINISHED'}

class RemoveDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.remove_display_item_frame'
    bl_label = 'Remove Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        mmd_root.display_item_frames.remove(mmd_root.active_display_item_frame)
        return {'FINISHED'}

class MoveUpDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.move_up_display_item_frame'
    bl_label = 'Move Up Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        if mmd_root.active_display_item_frame <= 0:
            return {'FINISHED'}

        mmd_root.display_item_frames.move(mmd_root.active_display_item_frame, mmd_root.active_display_item_frame-1)
        mmd_root.active_display_item_frame -= 1
        return {'FINISHED'}

class MoveDownDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.move_down_display_item_frame'
    bl_label = 'Move Down Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        if len( mmd_root.display_item_frames)-1 <= mmd_root.active_display_item_frame:
            return {'FINISHED'}

        mmd_root.display_item_frames.move(mmd_root.active_display_item_frame, mmd_root.active_display_item_frame+1)
        mmd_root.active_display_item_frame += 1
        return {'FINISHED'}

class AddDisplayItem(Operator):
    bl_idname = 'mmd_tools.add_display_item'
    bl_label = 'Add Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        item = frame.items.add()
        item.name = 'Display Item'
        return {'FINISHED'}

class RemoveDisplayItem(Operator):
    bl_idname = 'mmd_tools.remove_display_item'
    bl_label = 'Remove Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        frame.items.remove(frame.active_item)
        return {'FINISHED'}

class MoveUpDisplayItem(Operator):
    bl_idname = 'mmd_tools.move_up_display_item'
    bl_label = 'Move Up Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        if frame.active_item <= 0:
            return {'FINISHED'}

        frame.items.move(frame.active_item, frame.active_item-1)
        frame.active_item -= 1
        return {'FINISHED'}

class MoveDownDisplayItem(Operator):
    bl_idname = 'mmd_tools.move_down_display_item'
    bl_label = 'Move Down Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        if len(frame.items)-1 <= frame.active_item:
            return {'FINISHED'}

        frame.items.move(frame.active_item, frame.active_item+1)
        frame.active_item += 1
        return {'FINISHED'}

class SelectCurrentDisplayItem(Operator):
    bl_idname = 'mmd_tools.select_current_display_item'
    bl_label = 'Select Current Display Item Frame'
    bl_description = ''
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = rigging.Rig.findRoot(obj)
        rig = rigging.Rig(root)
        mmd_root = root.mmd_root

        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        arm = rig.armature()
        for i in context.scene.objects:
            i.select = False
        arm.hide = False
        arm.select = True
        context.scene.objects.active = arm

        bpy.ops.object.mode_set(mode='POSE')
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        item = frame.items[frame.active_item]
        bone_name = item.name
        for i in arm.pose.bones:
            i.bone.select = (i.name == bone_name)
        return {'FINISHED'}
