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

# def addBoneConstraint(obj, bone_name, constraint_type):
#     import bpy
#     selectAObject(obj)
#     bpy.ops.object.mode_set(mode='POSE')
#     obj.data.bones.active = parent.data.bones[bone_name]
#     bpy.ops.pose.constraint_add(type=constraint_type)


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


## Boneのカスタムプロパティにname_jが存在する場合、name_jの値を
# それ以外の場合は通常のbone名をキーとしたpose_boneへの辞書を作成
def makePmxBoneMap(armObj):
    boneMap = {}
    for i in armObj.pose.bones:
        boneMap[i.get('name_j', i.name)] = i
    return boneMap


def makeCapsule(segment=16, ring_count=8, radius=1.0, height=1.0, target_scene=None):
    import bpy
    if target_scene is None:
        target_scene = bpy.context.scene
    mesh = bpy.data.meshes.new(name='Capsule')
    meshObj = bpy.data.objects.new(name='Capsule', object_data=mesh)
    vertices = []
    top = (0, 0, height/2+radius)
    vertices.append(top)

    f = lambda i: radius*i/ring_count
    for i in range(ring_count, 0, -1):
        z = f(i-1)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            vertices.append((x,y,z+height/2))

    for i in range(ring_count):
        z = -f(i)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            vertices.append((x,y,z-height/2))

    bottom = (0, 0, -(height/2+radius))
    vertices.append(bottom)

    faces = []
    for i in range(1, segment):
        faces.append([0, i, i+1])
    faces.append([0, segment, 1])
    offset = segment + 1
    for i in range(ring_count*2-1):
        for j in range(segment-1):
            t = offset + j
            faces.append([t-segment, t, t+1, t-segment+1])
        faces.append([offset-1, offset+segment-1, offset, offset-segment])
        offset += segment
    for i in range(segment-1):
        t = offset + i
        faces.append([t-segment, offset, t-segment+1])
    faces.append([offset-1, offset, offset-segment])

    mesh.from_pydata(vertices, [], faces)
    target_scene.objects.link(meshObj)
    return meshObj

