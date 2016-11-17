# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator

from mmd_tools import utils
import mmd_tools.core.model as mmd_model


class AddDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.add_display_item_frame'
    bl_label = 'Add Display Item Frame'
    bl_description = 'Add a display item frame to the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        item = mmd_root.display_item_frames.add()
        item.name = 'Display Frame'
        mmd_root.active_display_item_frame = len(mmd_root.display_item_frames)-1
        return {'FINISHED'}

class RemoveDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.remove_display_item_frame'
    bl_label = 'Remove Display Item Frame'
    bl_description = 'Remove active display item frame from the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        # Let's prevent the accidental deletion of the special frames
        if not mmd_root.display_item_frames[mmd_root.active_display_item_frame].is_special:
            mmd_root.display_item_frames.remove(mmd_root.active_display_item_frame)
            mmd_root.active_display_item_frame = max(0, mmd_root.active_display_item_frame-1)
        return {'FINISHED'}

class MoveUpDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.move_up_display_item_frame'
    bl_label = 'Move Up Display Item Frame'
    bl_description = 'Move active display item frame up in the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        if mmd_root.active_display_item_frame <= 0:
            return {'FINISHED'}

        mmd_root.display_item_frames.move(mmd_root.active_display_item_frame, mmd_root.active_display_item_frame-1)
        mmd_root.active_display_item_frame -= 1
        return {'FINISHED'}

class MoveDownDisplayItemFrame(Operator):
    bl_idname = 'mmd_tools.move_down_display_item_frame'
    bl_label = 'Move Down Display Item Frame'
    bl_description = 'Move active display item frame down in the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        if len( mmd_root.display_item_frames)-1 <= mmd_root.active_display_item_frame:
            return {'FINISHED'}

        mmd_root.display_item_frames.move(mmd_root.active_display_item_frame, mmd_root.active_display_item_frame+1)
        mmd_root.active_display_item_frame += 1
        return {'FINISHED'}

class AddDisplayItem(Operator):
    bl_idname = 'mmd_tools.add_display_item'
    bl_label = 'Add Display Item'
    bl_description = 'Add a display item to the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        item = frame.items.add()
        item.type = 'MORPH' if frame.name == u'表情' else 'BONE'
        item.name = 'Display Item'
        frame.active_item = len(frame.items)-1
        return {'FINISHED'}

class RemoveDisplayItem(Operator):
    bl_idname = 'mmd_tools.remove_display_item'
    bl_label = 'Remove Display Item'
    bl_description = 'Remove active display item from the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        frame.items.remove(frame.active_item)
        frame.active_item = max(0, frame.active_item-1)
        return {'FINISHED'}

class MoveUpDisplayItem(Operator):
    bl_idname = 'mmd_tools.move_up_display_item'
    bl_label = 'Move Up Display Item'
    bl_description = 'Move active display item up in the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        if frame.active_item <= 0:
            return {'FINISHED'}

        frame.items.move(frame.active_item, frame.active_item-1)
        frame.active_item -= 1
        return {'FINISHED'}

class MoveDownDisplayItem(Operator):
    bl_idname = 'mmd_tools.move_down_display_item'
    bl_label = 'Move Down Display Item'
    bl_description = 'Move active display item down in the list'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        mmd_root = root.mmd_root
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        if len(frame.items)-1 <= frame.active_item:
            return {'FINISHED'}

        frame.items.move(frame.active_item, frame.active_item+1)
        frame.active_item += 1
        return {'FINISHED'}

class SelectCurrentDisplayItem(Operator):
    bl_idname = 'mmd_tools.select_current_display_item'
    bl_label = 'Select Current Display Item'
    bl_description = 'Select the bone assigned to the display item in the armature'
    bl_options = {'PRESET'}

    def execute(self, context):
        obj = context.active_object
        root = mmd_model.Model.findRoot(obj)
        rig = mmd_model.Model(root)
        mmd_root = root.mmd_root
        arm = rig.armature()
        frame = mmd_root.display_item_frames[mmd_root.active_display_item_frame]
        item = frame.items[frame.active_item]
        utils.selectSingleBone(context, arm, item.name)
        return {'FINISHED'}
