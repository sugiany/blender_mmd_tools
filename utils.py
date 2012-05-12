# -*- coding: utf-8 -*-
import bpy

## 現在のモードを指定したオブジェクトのEdit Modeに変更する
def enterEditMode(obj):
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = obj
    obj.select=True
    if obj.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
