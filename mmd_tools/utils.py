# -*- coding: utf-8 -*-
import re

## 指定したオブジェクトのみを選択状態かつアクティブにする
def selectAObject(obj):
    import bpy
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = obj
    obj.select=True

## 現在のモードを指定したオブジェクトのEdit Modeに変更する
def enterEditMode(obj):
    import bpy
    selectAObject(obj)
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


def separateByMaterials(meshObj):
    import bpy
    prev_parent = meshObj.parent
    dummy_parent = bpy.data.objects.new(name='tmp', object_data=None)
    meshObj.parent = dummy_parent

    enterEditMode(meshObj)
    try:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='MATERIAL')
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')

    for i in dummy_parent.children:
        mesh = i.data
        if len(mesh.polygons) > 0:
            mat_index = mesh.polygons[0].material_index
            mat = mesh.materials[mat_index]
            for k in mesh.materials:
                mesh.materials.pop(index=0, update_data=True)
            mesh.materials.append(mat)
            for po in mesh.polygons:
                po.material_index = 0
            i.name = mat.name
            i.parent = prev_parent
