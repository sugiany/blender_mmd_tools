# -*- coding: utf-8 -*-
import re
import math

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


## Boneのカスタムプロパティにname_jが存在する場合、name_jの値を
# それ以外の場合は通常のbone名をキーとしたpose_boneへの辞書を作成
def makePmxBoneMap(armObj):
    boneMap = {}
    for i in armObj.pose.bones:
        boneMap[i.get('name_j', i.name)] = i
    return i


class MMDCamera:
    def __init__(self, obj):
        if obj.type != 'EMPTY':
            if obj.parent is None or obj.type != 'CAMERA':
                raise ValueError('%s is not MMDCamera'%str(obj))
            obj = obj.parent
        if obj.type == 'EMPTY' and obj.get('is_mmd_camera', False):
            self.__emptyObj = obj
        else:
            raise ValueError('%s is not MMDCamera'%str(obj))


    @staticmethod
    def isMMDCamera(obj):
        if obj.type != 'EMPTY':
            if obj.parent is None or obj.type != 'CAMERA':
                return False
            obj = obj.parent
        return obj.type == 'EMPTY' and obj.get('is_mmd_camera', False)


    @staticmethod
    def convertToMMDCamera(cameraObj):
        import bpy
        import mathutils
        if MMDCamera.isMMDCamera(cameraObj):
            return MMDCamera(cameraObj)

        name = cameraObj.name
        cameraObj.name = name + '_mmd'
        empty = bpy.data.objects.new(name=name, object_data=None)
        bpy.context.scene.objects.link(empty)

        empty.rotation_mode = 'XYZ'
        empty.is_mmd_camera = True
        empty.mmd_camera_distance = 0.0
        cameraObj.parent = empty
        cameraObj.data.sensor_fit = 'VERTICAL'
        cameraObj.location = mathutils.Vector((0,0,0))
        cameraObj.rotation_mode = 'XYZ'
        cameraObj.rotation_euler = mathutils.Vector((math.radians(90.0),0,0))
        cameraObj.lock_location = (True, False, True)
        cameraObj.lock_rotation = (True, True, True)
        cameraObj.lock_scale = (True, True, True)
        driver = cameraObj.driver_add('location', 1).driver
        driverVar = driver.variables.new()
        driverVar.name = 'mmd_distance'
        driverVar.type = 'SINGLE_PROP'
        driverVar.targets[0].id_type = 'OBJECT'
        driverVar.targets[0].id = empty
        driverVar.targets[0].data_path = 'mmd_camera_distance'
        driver.type = 'SCRIPTED'
        driver.expression = '-%s'%driverVar.name
        return MMDCamera(empty)

    def object(sel):
        return self.__emptyObj
