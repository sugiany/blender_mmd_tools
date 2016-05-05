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

def setParentToBone(obj, parent, bone_name):
    import bpy
    selectAObject(parent)
    bpy.ops.object.mode_set(mode='POSE')
    selectAObject(obj)
    bpy.context.scene.objects.active = parent
    parent.select = True
    bpy.ops.object.mode_set(mode='POSE')
    parent.data.bones.active = parent.data.bones[bone_name]
    bpy.ops.object.parent_set(type='BONE', xmirror=False, keep_transform=False)
    bpy.ops.object.mode_set(mode='OBJECT')

def selectSingleBone(context, armature, bone_name, reset_pose=False):
    import bpy
    from mathutils import Vector, Quaternion
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except:
        pass
    for i in context.scene.objects:
        i.select = False
    armature.hide = False
    armature.select = True
    armature.layers[context.scene.active_layer] = True
    context.scene.objects.active = armature
    if reset_pose:
        def_loc = Vector((0,0,0))
        def_rot = Quaternion((1,0,0,0))
        def_scale = Vector((1,1,1))
        for p_bone in armature.pose.bones:
            p_bone.location = def_loc
            p_bone.rotation_quaternion = def_rot
            p_bone.scale = def_scale
    bpy.ops.object.mode_set(mode='POSE')
    armature_bones = armature.data.bones
    for i in armature_bones:
        i.select = (i.name == bone_name)
        i.select_head = i.select_tail = i.select
        if i.select:
            armature_bones.active = i
            i.hide = False
            #armature.data.layers[list(i.layers).index(True)] = True


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

## src_vertex_groupのWeightをdest_vertex_groupにaddする
def mergeVertexGroup(meshObj, src_vertex_group_name, dest_vertex_group_name):
    mesh = meshObj.data
    src_vertex_group = meshObj.vertex_groups[src_vertex_group_name]
    dest_vertex_group = meshObj.vertex_groups[dest_vertex_group_name]

    vtxIndex = src_vertex_group.index
    for v in mesh.vertices:
        try:
            gi = [i.group for i in v.groups].index(vtxIndex)
            dest_vertex_group.add([v.index], v.groups[gi].weight, 'ADD')
        except ValueError:
            pass

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

def clearUnusedMeshes():
    import bpy
    meshes_to_delete = []
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            meshes_to_delete.append(mesh)

    for mesh in meshes_to_delete:
        bpy.data.meshes.remove(mesh)
    


## Boneのカスタムプロパティにname_jが存在する場合、name_jの値を
# それ以外の場合は通常のbone名をキーとしたpose_boneへの辞書を作成
def makePmxBoneMap(armObj):
    boneMap = {}
    for i in armObj.pose.bones:
        # Maintain backward compatibility with mmd_tools v0.4.x or older.
        name = i.get('mmd_bone_name_j', i.get('name_j', None))
        if name is None:
            name = i.mmd_bone.name_j or i.name
        boneMap[name] = i
    return boneMap

def uniqueName(name, used_names):
    if name not in used_names:
        return name
    count = 1
    new_name = orig_name = re.sub(r'\.\d{1,}$', '', name)
    while new_name in used_names:
        new_name = '%s.%03d'%(orig_name, count)
        count += 1
    return new_name

def int2base(x, base):
    """
    Method to convert an int to a base
    Source: http://stackoverflow.com/questions/2267362
    """
    import string
    digs = string.digits + string.ascii_uppercase
    if x < 0: sign = -1
    elif x == 0: return digs[0]
    else: 
        sign = 1
        x *= sign
        digits = []
    while x:
        digits.append(digs[x % base])
        x = int(x / base)
    if sign < 0:
        digits.append('-')
    digits.reverse()
    return ''.join(digits)
