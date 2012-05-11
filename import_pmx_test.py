# -*- coding: utf-8 -*-
import pmx
import bpy
import os
import mathutils


def main():
    pmx_file = pmx.File()
    pmx_file.load('F:/mac-tmp/cg/tmp/zezemiku/zezemiku.pmx')

    TO_BLE_MATRIX = mathutils.Matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]])

    model = pmx_file.model

    m = bpy.data.meshes.new(name=model.name)
    obj = bpy.data.objects.new(name='tmp', object_data=m)
    arm = bpy.data.armatures.new(name=model.name)
    root = bpy.data.objects.new(name=model.name, object_data=arm)
    bpy.context.scene.objects.link(obj)
    bpy.context.scene.objects.link(root)
    obj.parent = root

    m.vertices.add(count=len(model.vertices))
    vertex_groups = []
    for i in model.bones:
        vertex_groups.append(obj.vertex_groups.new(name=i.name))

    for i, v in enumerate(model.vertices):
        bv = m.vertices[i]
        bv.co = v.co
        bv.normal = v.normal
        if isinstance(v.weight.weights, pmx.BoneWeightSDEF):
            vertex_groups[v.weight.bones[0]].add(index=[i], weight=v.weight.weights.weight, type='REPLACE')
            vertex_groups[v.weight.bones[1]].add(index=[i], weight=1.0 - v.weight.weight, type='REPLACE')
        if len(v.weight.bones) == 1:
            vertex_groups[v.weight.bones[0]].add(index=[i], weight=1.0, type='REPLACE')
        elif len(v.weight.bones) == 2:
            vertex_groups[v.weight.bones[0]].add(index=[i], weight=v.weight.weights[0], type='REPLACE')
            vertex_groups[v.weight.bones[1]].add(index=[i], weight=1.0 - v.weight.weights[0], type='REPLACE')
        elif len(v.weight.bones) == 4:
            vertex_groups[v.weight.bones[0]].add(index=[i], weight=v.weight.weights[0], type='REPLACE')
            vertex_groups[v.weight.bones[1]].add(index=[i], weight=v.weight.weights[1], type='REPLACE')
            vertex_groups[v.weight.bones[2]].add(index=[i], weight=v.weight.weights[2], type='REPLACE')
            vertex_groups[v.weight.bones[3]].add(index=[i], weight=v.weight.weights[3], type='REPLACE')


    textures = []
    for i in model.textures:
        try:
            image = bpy.data.images.load(filepath=i.path)
        except Exception:
            print('ERROR: failed to load %s'%str(i.path))
        name = os.path.basename(i.path).split('.')[0]
        tex = bpy.data.textures.new(name=name, type='IMAGE')
        tex.image=image
        textures.append(tex)

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = root
    root.select=True
    if root.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    bones = []
    for i in model.bones:
        bone = arm.edit_bones.new(name=i.name)
        loc = mathutils.Vector(i.location)
        loc.rotate(TO_BLE_MATRIX)
        bone.head = loc
        bones.append(bone)
    for b_bone, m_bone in zip(bones, model.bones):
        if m_bone.parent != -1:
            b_bone.parent = bones[m_bone.parent]

    for b_bone, m_bone in zip(bones, model.bones):
        if isinstance(m_bone.displayConnection, int):
            if m_bone.displayConnection != -1:
                b_bone.tail = bones[m_bone.displayConnection].head
            else:
                b_bone.tail = b_bone.head
        else:
            loc = mathutils.Vector(m_bone.displayConnection)
            loc.rotate(TO_BLE_MATRIX)
            b_bone.tail = b_bone.head + loc

    bpy.ops.object.mode_set(mode='OBJECT')



    mat_face_count_list = []
    bpy.types.Material.ambient_color = bpy.props.FloatVectorProperty(name='ambient color')
    for i in model.materials:
        mat = bpy.data.materials.new(name=i.name)
        mat.diffuse_color = i.diffuse[0:3]
        mat.alpha = i.diffuse[3]
        mat.ambient_color = i.ambient
        mat.specular_color = i.specular[0:3]
        mat.specular_alpha = i.specular[3]
        mat_face_count_list.append(int(i.vertex_count/3))
        m.materials.append(mat)
        if i.texture != -1:
            texture_slot = mat.texture_slots.add()
            texture_slot.texture = textures[i.texture]
            texture_slot.texture_coords = 'UV'

    def flipUV_V(uv):
        u, v = uv
        v = 1.0 - v
        return [u, v]

    print(mat_face_count_list)
    m.tessfaces.add(count=len(model.faces))
    uvLayer = m.tessface_uv_textures.new()
    for i, f in enumerate(model.faces):
        bf = m.tessfaces[i]
        bf.vertices_raw = list(f) + [0]
        bf.use_smooth = True
        sum = 0
        uv = uvLayer.data[i]
        uv.uv1 = flipUV_V(model.vertices[f[0]].uv)
        uv.uv2 = flipUV_V(model.vertices[f[1]].uv)
        uv.uv3 = flipUV_V(model.vertices[f[2]].uv)
        for j, count in enumerate(mat_face_count_list):
            if i < count + sum:
                bf.material_index = j
                break
            sum += count
    m.transform(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ])

    m.update()
    if False:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.objects.active = obj
        obj.select=True
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.separate(type='MATERIAL')

        for i in root.children:
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

        bpy.ops.object.mode_set(mode='OBJECT')

        m.update()
