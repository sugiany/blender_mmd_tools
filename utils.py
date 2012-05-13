# -*- coding: utf-8 -*-
import re

## 現在のモードを指定したオブジェクトのEdit Modeに変更する
def enterEditMode(obj):
    import bpy
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = obj
    obj.select=True
    if obj.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')


__CONVERT_NAME_TO_L_REGEXP = re.compile('^(.*)左(.*)$')
__CONVERT_NAME_TO_R_REGEXP = re.compile('^(.*)右(.*)$')
## 日本語で左右を命名されている名前をblender方式のL(R)に変更する
def convertNameToLR(name):
    m = __CONVERT_NAME_TO_L_REGEXP.match(name)
    if m:
        name = m.group(1) + m.group(2) + '.L'
    m = __CONVERT_NAME_TO_R_REGEXP.match(name)
    if m:
        name = m.group(1) + m.group(2) + '.R'
    return name
