# -*- coding: utf-8 -*-
from . import pmx
from . import bpyutils

import collections
import os
import copy
import logging
import shutil

import mathutils
import bpy
import bmesh

class _Vertex:
    def __init__(self, co, groups, normal, offsets):
        self.co = copy.deepcopy(co)
        self.groups = copy.copy(groups) # [(group_number, weight), ...]
        self.normal = copy.deepcopy(normal)
        self.offsets = copy.deepcopy(offsets)
        self.index = None
        self.uv = None

class _Face:
    def __init__(self, vertices, normal):
        ''' Temporary Face Class
        '''
        self.vertices = copy.copy(vertices)
        self.normal = copy.deepcopy(normal)

class _Mesh:
    def __init__(self, mesh_data, material_faces, shape_key_names, vertex_group_names, materials):
        self.mesh_data = mesh_data
        self.material_faces = material_faces # dict of {material_index => [face1, face2, ....]}
        self.shape_key_names = shape_key_names
        self.vertex_group_names = vertex_group_names
        self.materials = materials

    def __del__(self):
        logging.debug('remove mesh data: %s', str(self.mesh_data))
        bpy.data.meshes.remove(self.mesh_data)


class __PmxExporter:
    TO_PMX_MATRIX = mathutils.Matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]])

    def __init__(self):
        self.__model = None

    @staticmethod
    def flipUV_V(uv):
        u, v = uv
        return [u, 1.0-v]

    def __exportMeshes(self, meshes, bone_map):
        mat_map = {}
        for mesh in meshes:
            for index, mat_faces in mesh.material_faces.items():
                name = mesh.materials[index].name
                if name not in mat_map:
                    mat_map[name] = []
                mat_map[name].append((mat_faces, mesh.vertex_group_names))

        # export vertices
        texture_list = []
        vert_count = 0
        for mat_name, mat_meshes in mat_map.items():
            face_count = 0
            for mat_faces, vertex_group_names in mat_meshes:
                mesh_vertices = []
                for face in mat_faces:
                    mesh_vertices.extend(face.vertices)

                for v in mesh_vertices:
                    vert_count += 1
                    if v.index is not None:
                        continue

                    v.index = len(self.__model.vertices)
                    pv = pmx.Vertex()
                    pv.co = list(v.co)
                    pv.normal = v.normal * -1
                    pv.uv = self.flipUV_V(v.uv)

                    t = len(v.groups)
                    if t == 0:
                        weight = pmx.BoneWeight()
                        weight.type = pmx.BoneWeight.BDEF1
                        weight.bones = [-1]
                        pv.weight = weight
                    elif t == 1:
                        weight = pmx.BoneWeight()
                        weight.type = pmx.BoneWeight.BDEF1
                        weight.bones = [bone_map[vertex_group_names[v.groups[0][0]]]]
                        pv.weight = weight
                    elif t == 2:
                        vg1, vg2 = v.groups
                        weight = pmx.BoneWeight()
                        weight.type = pmx.BoneWeight.BDEF2
                        weight.bones = [
                            bone_map[vertex_group_names[vg1[0]]],
                            bone_map[vertex_group_names[vg2[0]]]
                            ]
                        weight.weights = [vg1[1]]
                        pv.weight = weight
                    else:
                        weight = pmx.BoneWeight()
                        weight.type = pmx.BoneWeight.BDEF4
                        weight.bones = [-1, -1, -1, -1]
                        weight.weights = [0.0, 0.0, 0.0, 0.0]
                        for i in range(min(len(v.groups), 4)):
                            gn, w = v.groups[i]
                            weight.bones[i] = bone_map[vertex_group_names[gn]]
                            weight.weights[i] = w
                        pv.weight = weight
                    self.__model.vertices.append(pv)

                for face in mat_faces:
                    self.__model.faces.append([x.index for x in face.vertices])
                face_count += len(mat_faces)
            self.__exportMaterial(bpy.data.materials[mat_name], face_count, texture_list)


    def __exportTexture(self, texture):
        if not isinstance(texture, bpy.types.ImageTexture):
            return -1

        path = texture.image.filepath
        if self.__copyTextures:
            tex_dir = os.path.join(os.path.dirname(self.__filepath), 'textures')
            if not os.path.isdir(tex_dir):
                os.mkdir(tex_dir)
                logging.info('Create a texture directory: %s', tex_dir)

            dest_path = os.path.join(tex_dir, os.path.basename(path))
            shutil.copyfile(path, dest_path)
            logging.info('Copy file %s --> %s', path, dest_path)
            path = dest_path

        t = pmx.Texture()
        t.path = path
        self.__model.textures.append(t)
        if not os.path.isfile(t.path):
            logging.warning('  The texture file does not exist: %s', t.path)
        return len(self.__model.textures) - 1

    def __exportMaterial(self, material, num_faces, textureList):
        p_mat = pmx.Material()
        mmd_mat = material.mmd_material

        p_mat.name = mmd_mat.name_j
        p_mat.name_e = mmd_mat.name_e
        p_mat.diffuse = list(material.diffuse_color) + [material.alpha]
        p_mat.ambient = mmd_mat.ambient_color
        p_mat.specular = list(material.specular_color) + [material.specular_alpha]
        p_mat.is_double_sided = mmd_mat.is_double_sided
        p_mat.enabled_drop_shadow = mmd_mat.enabled_drop_shadow
        p_mat.enabled_self_shadow_map = mmd_mat.enabled_self_shadow_map
        p_mat.enabled_self_shadow = mmd_mat.enabled_self_shadow
        p_mat.enabled_toon_edge = mmd_mat.enabled_toon_edge
        p_mat.edge_color = mmd_mat.edge_color
        p_mat.edge_size = mmd_mat.edge_weight
        p_mat.sphere_texture_mode = int(mmd_mat.sphere_texture_type)
        p_mat.is_shared_toon_texture = mmd_mat.is_shared_toon_texture
        p_mat.comment = mmd_mat.comment

        if mmd_mat.is_shared_toon_texture:
            p_mat.toon_texture = mmd_mat.shared_toon_texture

        p_mat.vertex_count = num_faces * 3
        if len(material.texture_slots) > 0:
            if material.texture_slots[0] is not None:
                tex = material.texture_slots[0].texture
                index = -1
                if tex not in textureList:
                    index = self.__exportTexture(tex)
                    textureList.append(tex)
                else:
                    index = textureList.index(tex)
                p_mat.texture = index
                p_mat.diffuse[3] = 1.0 # Set the alpha value to 1.0 if the material has textures.
            if not mmd_mat.is_shared_toon_texture and material.texture_slots[1] is not None:
                tex = material.texture_slots[1].texture
                index = -1
                if tex not in textureList:
                    index = self.__exportTexture(tex)
                    textureList.append(tex)
                else:
                    index = textureList.index(tex)
                p_mat.toon_texture = index
            if material.texture_slots[2] is not None:
                tex = material.texture_slots[2].texture
                index = -1
                if tex not in textureList:
                    index = self.__exportTexture(tex)
                    textureList.append(tex)
                else:
                    index = textureList.index(tex)
                p_mat.sphere_texture = index
        self.__model.materials.append(p_mat)

    def __exportBones(self):
        """ Export bones.
        @return the dictionary to map Blender bone names to bone indices of the pmx.model instance.
        """
        arm = self.__armature
        boneMap = {}
        pmx_bones = []
        pose_bones = arm.pose.bones
        world_mat = arm.matrix_world
        r = {}
        with bpyutils.edit_object(arm) as data:
            for bone in data.edit_bones:
                p_bone = pose_bones[bone.name]
                if p_bone.is_mmd_shadow_bone:
                    continue
                pmx_bone = pmx.Bone()
                if p_bone.mmd_bone.name_j != '':
                    pmx_bone.name = p_bone.mmd_bone.name_j
                else:
                    pmx_bone.name = bone.name
                pmx_bone_e = p_bone.mmd_bone.name_e or ''
                pmx_bone.location = world_mat * mathutils.Vector(bone.head) * self.__scale * self.TO_PMX_MATRIX
                pmx_bone.parent = bone.parent
                pmx_bone.visible = not p_bone.bone.hide
                pmx_bone.isMovable = not all(p_bone.lock_location)
                pmx_bone.isRotatable = not all(p_bone.lock_rotation)
                pmx_bones.append(pmx_bone)
                boneMap[bone] = pmx_bone
                r[bone.name] = len(pmx_bones) - 1

                if len(bone.children) == 0 and not p_bone.mmd_bone.is_tip:
                    pmx_tip_bone = pmx.Bone()
                    pmx_tip_bone.name = 'tip_' + bone.name
                    pmx_tip_bone.location =  world_mat * mathutils.Vector(bone.tail) * self.__scale * self.TO_PMX_MATRIX
                    pmx_tip_bone.parent = bone
                    pmx_bones.append(pmx_tip_bone)
                    pmx_bone.displayConnection = pmx_tip_bone
                elif len(bone.children) > 0:
                    pmx_bone.displayConnection = list(filter(lambda x: not pose_bones[x.name].is_mmd_shadow_bone, sorted(bone.children, key=lambda x: 1 if pose_bones[x.name].mmd_bone.is_tip else 0)))[0]

            for i in pmx_bones:
                if i.parent is not None:
                    i.parent = pmx_bones.index(boneMap[i.parent])
                    logging.debug('the parent of %s: %s', i.name, i.parent)
                if isinstance(i.displayConnection, pmx.Bone):
                    i.displayConnection = pmx_bones.index(i.displayConnection)
                elif isinstance(i.displayConnection, bpy.types.EditBone):
                    i.displayConnection = pmx_bones.index(boneMap[i.displayConnection])

            self.__model.bones = pmx_bones
        return r

    def __exportIKLinks(self, pose_bone, pmx_bones, bone_map, ik_links, count):
        if count <= 0:
            return ik_links

        logging.debug('    Create IK Link for %s', pose_bone.name)
        ik_link = pmx.IKLink()
        ik_link.target = bone_map[pose_bone.name]
        if pose_bone.use_ik_limit_x or pose_bone.use_ik_limit_y or pose_bone.use_ik_limit_z:
            minimum = []
            maximum = []
            if pose_bone.use_ik_limit_x:
                minimum.append(-pose_bone.ik_max_x)
                maximum.append(-pose_bone.ik_min_x)
            else:
                minimum.append(0.0)
                maximum.append(0.0)

            if pose_bone.use_ik_limit_y:
                minimum.append(pose_bone.ik_min_y)
                maximum.append(pose_bone.ik_max_y)
            else:
                minimum.append(0.0)
                maximum.append(0.0)

            if pose_bone.use_ik_limit_z:
                minimum.append(pose_bone.ik_min_z)
                maximum.append(pose_bone.ik_max_z)
            else:
                minimum.append(0.0)
                maximum.append(0.0)
            ik_link.minimumAngle = minimum
            ik_link.maximumAngle = maximum

        if pose_bone.parent is not None:
            return self.__exportIKLinks(pose_bone.parent, pmx_bones, bone_map, ik_links + [ik_link], count - 1)
        else:
            return ik_link + [ik_link]


    def __exportIK(self, bone_map):
        """ Export IK constraints
         @param bone_map the dictionary to map Blender bone names to bone indices of the pmx.model instance.
        """
        pmx_bones = self.__model.bones
        arm = self.__armature
        pose_bones = arm.pose.bones
        for bone in pose_bones:
            for c in bone.constraints:
                if c.type == 'IK':
                    logging.debug('  Found IK constraint.')
                    ik_pose_bone = pose_bones[c.subtarget]
                    if ik_pose_bone.mmd_shadow_bone_type == 'IK_PROXY':
                        ik_bone_index = bone_map[ik_pose_bone.parent.name]
                        logging.debug('  Found IK proxy bone: %s -> %s', ik_pose_bone.name, ik_pose_bone.parent.name)
                    else:
                        ik_bone_index = bone_map[c.subtarget]

                    pmx_ik_bone = pmx_bones[ik_bone_index]
                    pmx_ik_bone.isIK = True
                    pmx_ik_bone.transform_order += 1
                    pmx_ik_bone.target = pmx_bones[bone_map[bone.name]].displayConnection
                    pmx_ik_bone.ik_links = self.__exportIKLinks(bone, pmx_bones, bone_map, [], c.chain_count)

    def __exportVertexMorphs(self, meshes):
        shape_key_names = []
        for mesh in meshes:
            for i in mesh.shape_key_names:
                if i not in shape_key_names:
                    shape_key_names.append(i)

        for i in shape_key_names:
            exported_vert = set()
            morph = pmx.VertexMorph(i, '', 4)
            for mesh in meshes:
                vertices = []
                for mf in mesh.material_faces.values():
                    for f in mf:
                        vertices.extend(f.vertices)

                if i in mesh.shape_key_names:
                    for v in vertices:
                        if v.index in exported_vert:
                            continue
                        exported_vert.add(v.index)

                        offset = v.offsets[mesh.shape_key_names.index(i)]
                        if mathutils.Vector(offset).length < 0.001:
                            continue

                        mo = pmx.VertexMorphOffset()
                        mo.index = v.index
                        mo.offset = offset
                        morph.offsets.append(mo)
            self.__model.morphs.append(morph)

    def __exportDisplayItems(self, root, bone_map):
        res = []
        morph_map = {}
        for i, m in enumerate(self.__model.morphs):
            morph_map[m.name] = i
        for i in root.mmd_root.display_item_frames:
            d = pmx.Display()
            d.name = i.name
            d.name_e = i.name_e
            d.isSpecial = i.is_special
            items = []
            for j in i.items:
                if j.type == 'BONE' and j.name in bone_map:
                    items.append((0, bone_map[j.name]))
                elif j.type == 'MORPH' and j.name in morph_map:
                    items.append((1, morph_map[j.name]))
                else:
                    logging.warning('Display item (%s, %s) was not found.', j.type, j.name)
            d.data = items
            res.append(d)
        self.__model.display = res

    @staticmethod
    def __convertFaceUVToVertexUV(vert_index, uv, vertices_map):
        vertices = vertices_map[vert_index]
        for i in vertices:
            if i.uv is None:
                i.uv = uv
                return i
            elif (i.uv[0] - uv[0])**2 + (i.uv[1] - uv[1])**2 < 0.0001:
                return i
        n = copy.deepcopy(i)
        n.uv = uv
        vertices.append(n)
        return n

    @staticmethod
    def __triangulate(mesh):
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()

    def __loadMeshData(self, meshObj):
        shape_key_weights = []
        for i in meshObj.data.shape_keys.key_blocks:
            shape_key_weights.append(i.value)
            i.value = 0.0

        vertex_group_names = list(map(lambda x: x.name, meshObj.vertex_groups))

        base_mesh = meshObj.to_mesh(bpy.context.scene, True, 'PREVIEW', False)
        base_mesh.transform(meshObj.matrix_world)
        base_mesh.transform(self.TO_PMX_MATRIX*self.__scale)
        self.__triangulate(base_mesh)
        base_mesh.update(calc_tessface=True)

        base_vertices = {}
        for v in base_mesh.vertices:
            base_vertices[v.index] = [_Vertex(
                v.co,
                list(map(lambda x: (x.group, x.weight), v.groups)),
                v.normal,
                [])]

        # calculate offsets
        shape_key_names = []
        for i in meshObj.data.shape_keys.key_blocks[1:]:
            shape_key_names.append(i.name)
            i.value = 1.0
            mesh = meshObj.to_mesh(bpy.context.scene, True, 'PREVIEW', False)
            mesh.transform(meshObj.matrix_world)
            mesh.transform(self.TO_PMX_MATRIX*self.__scale)
            mesh.update(calc_tessface=True)
            for key in base_vertices.keys():
                base = base_vertices[key][0]
                v = mesh.vertices[key]
                base.offsets.append(mathutils.Vector(v.co) - mathutils.Vector(base.co))
            bpy.data.meshes.remove(mesh)
            i.value = 0.0

        # load face data
        materials = {}
        for face, uv in zip(base_mesh.tessfaces, base_mesh.tessface_uv_textures.active.data):
            if len(face.vertices) != 3:
                raise Exception
            v1 = self.__convertFaceUVToVertexUV(face.vertices[0], uv.uv1, base_vertices)
            v2 = self.__convertFaceUVToVertexUV(face.vertices[1], uv.uv2, base_vertices)
            v3 = self.__convertFaceUVToVertexUV(face.vertices[2], uv.uv3, base_vertices)

            t = _Face(
                [v1, v2, v3],
                face.normal)
            if face.material_index not in materials:
                materials[face.material_index] = []
            materials[face.material_index].append(t)

        for i, sk in enumerate(meshObj.data.shape_keys.key_blocks):
            sk.value = shape_key_weights[i]

        return _Mesh(
            base_mesh,
            materials,
            shape_key_names,
            vertex_group_names,
            base_mesh.materials)


    def execute(self, filepath, **args):
        self.__model = pmx.Model()
        self.__model.name = 'test'
        self.__model.name_e = 'test eng'

        self.__model.comment = 'exported by mmd_tools'

        meshes = args.get('meshes', [])
        self.__armature = args.get('armature', None)
        rigid_bodeis = args.get('rigid_bodeis', [])
        joints = args.get('joints', [])
        root = args.get('root', None)
        self.__copyTextures = args.get('copy_textures', False)
        self.__filepath = filepath

        self.__scale = 1.0/float(args.get('scale', 0.2))


        nameMap = self.__exportBones()
        self.__exportIK(nameMap)

        mesh_data = []
        for i in meshes:
            mesh_data.append(self.__loadMeshData(i))

        self.__exportMeshes(mesh_data, nameMap)
        self.__exportVertexMorphs(mesh_data)
        if root is not None:
            self.__exportDisplayItems(root, nameMap)

        pmx.save(filepath, self.__model)

def export(filepath, **kwargs):
    exporter = __PmxExporter()
    exporter.execute(filepath, **kwargs)
