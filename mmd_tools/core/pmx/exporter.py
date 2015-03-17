# -*- coding: utf-8 -*-
import os
import copy
import logging
import shutil

import mathutils
import bpy
import bmesh

from mmd_tools.core import pmx
from mmd_tools.core.bone import FnBone
from mmd_tools import bpyutils
import mmd_tools.core.model as mmd_model


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
        self.__bone_name_table = []
        self.__material_name_table = []

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
        for mat_name, mat_meshes in mat_map.items():
            face_count = 0
            for mat_faces, vertex_group_names in mat_meshes:
                mesh_vertices = []
                for face in mat_faces:
                    mesh_vertices.extend(face.vertices)

                for v in mesh_vertices:
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
            self.__exportMaterial(bpy.data.materials[mat_name], face_count)

    def __exportTexture(self, filepath):
        if filepath.strip() == '':
            return -1
        filepath = os.path.abspath(filepath)
        for i, tex in enumerate(self.__model.textures):
            if tex.path == filepath:
                return i
        t = pmx.Texture()
        t.path = filepath
        self.__model.textures.append(t)
        if not os.path.isfile(t.path):
            logging.warning('  The texture file does not exist: %s', t.path)
        return len(self.__model.textures) - 1

    def __copy_textures(self, tex_dir):
        if not os.path.isdir(tex_dir):
            os.mkdir(tex_dir)
            logging.info('Create a texture directory: %s', tex_dir)

        for texture in self.__model.textures:
            path = texture.path
            dest_path = os.path.join(tex_dir, os.path.basename(path))
            shutil.copyfile(path, dest_path)
            logging.info('Copy file %s --> %s', path, dest_path)
            texture.path = dest_path

    def __exportMaterial(self, material, num_faces):
        p_mat = pmx.Material()
        mmd_mat = material.mmd_material

        p_mat.name = mmd_mat.name_j or material.name
        p_mat.name_e = mmd_mat.name_e or material.name
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
        p_mat.comment = mmd_mat.comment

        p_mat.vertex_count = num_faces * 3
        tex_slots = material.texture_slots.values()
        if tex_slots[0]:
            tex = tex_slots[0].texture
            index = self.__exportTexture(tex.image.filepath)
            p_mat.texture = index
        if tex_slots[1]:
            tex = tex_slots[1].texture
            index = self.__exportTexture(tex.image.filepath)
            p_mat.sphere_texture = index

        if mmd_mat.is_shared_toon_texture:
            p_mat.toon_texture = mmd_mat.shared_toon_texture
            p_mat.is_shared_toon_texture = True
        else:
            p_mat.toon_texture =  self.__exportTexture(mmd_mat.toon_texture)
            p_mat.is_shared_toon_texture = False

        self.__material_name_table.append(material.name)
        self.__model.materials.append(p_mat)

    @classmethod
    def __countBoneDepth(cls, bone):
        if bone.parent is None:
            return 0
        else:
            return cls.__countBoneDepth(bone.parent) + 1

    def __exportBones(self):
        """ Export bones.
        Returns:
            A dictionary to map Blender bone names to bone indices of the pmx.model instance.
        """
        arm = self.__armature
        boneMap = {}
        pmx_bones = []
        pose_bones = arm.pose.bones
        world_mat = arm.matrix_world
        r = {}

        # sort by a depth of bones.
        t = []
        for i in pose_bones:
            t.append((i, self.__countBoneDepth(i)))

        sorted_bones = sorted(pose_bones, key=self.__countBoneDepth)

        with bpyutils.edit_object(arm) as data:
            for p_bone in sorted_bones:
                bone = data.edit_bones[p_bone.name]
                if p_bone.is_mmd_shadow_bone:
                    continue
                pmx_bone = pmx.Bone()
                if p_bone.mmd_bone.name_j != '':
                    pmx_bone.name = p_bone.mmd_bone.name_j
                else:
                    pmx_bone.name = bone.name

                mmd_bone = p_bone.mmd_bone
                if mmd_bone.additional_transform_bone_id != -1:
                    fnBone = FnBone.from_bone_id(arm, mmd_bone.additional_transform_bone_id)
                    pmx_bone.additionalTransform = (fnBone.pose_bone, mmd_bone.additional_transform_influence)
                pmx_bone.hasAdditionalRotate = mmd_bone.has_additional_rotation
                pmx_bone.hasAdditionalLocation = mmd_bone.has_additional_location

                pmx_bone_e = p_bone.mmd_bone.name_e or ''
                pmx_bone.location = world_mat * mathutils.Vector(bone.head) * self.__scale * self.TO_PMX_MATRIX
                pmx_bone.parent = bone.parent
                pmx_bone.visible = mmd_bone.is_visible
                pmx_bone.isMovable = not all(p_bone.lock_location)
                pmx_bone.isRotatable = not all(p_bone.lock_rotation)
                pmx_bones.append(pmx_bone)
                self.__bone_name_table.append(p_bone.name)
                boneMap[bone] = pmx_bone
                r[bone.name] = len(pmx_bones) - 1

                if p_bone.mmd_bone.is_tip:
                    pmx_bone.displayConnection = -1
                elif p_bone.mmd_bone.use_tail_location:
                    tail_loc = world_mat * mathutils.Vector(bone.tail) * self.__scale * self.TO_PMX_MATRIX
                    pmx_bone.displayConnection = tail_loc - pmx_bone.location
                else:
                    for child in bone.children:
                        if child.use_connect:
                            pmx_bone.displayConnection = child
                            break
                    #if not pmx_bone.displayConnection: #I think this wasn't working properly
                        #pmx_bone.displayConnection = bone.tail - bone.head

                #add fixed and local axes
                if mmd_bone.enabled_fixed_axis:
                    pmx_bone.axis = mmd_bone.fixed_axis

                if mmd_bone.enabled_local_axes:
                    pmx_bone.localCoordinate = pmx.Coordinate(
                        mmd_bone.local_axis_x, mmd_bone.local_axis_z)

            for idx, i in enumerate(pmx_bones):
                if i.parent is not None:
                    i.parent = pmx_bones.index(boneMap[i.parent])
                    logging.debug('the parent of %s:%s: %s', idx, i.name, i.parent)
                if isinstance(i.displayConnection, pmx.Bone):
                    i.displayConnection = pmx_bones.index(i.displayConnection)
                elif isinstance(i.displayConnection, bpy.types.EditBone):
                    i.displayConnection = pmx_bones.index(boneMap[i.displayConnection])

                if i.additionalTransform is not None:
                    b, influ = i.additionalTransform
                    i.additionalTransform = (r[b.name], influ)

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
                    if ik_pose_bone.mmd_shadow_bone_type == 'IK_TARGET':
                        ik_bone_index = bone_map[ik_pose_bone.parent.name]
                        logging.debug('  Found IK proxy bone: %s -> %s', ik_pose_bone.name, ik_pose_bone.parent.name)
                    else:
                        ik_bone_index = bone_map[c.subtarget]

                    ik_target_bone = self.__get_connected_child_bone(bone)
                    pmx_ik_bone = pmx_bones[ik_bone_index]
                    pmx_ik_bone.isIK = True
                    pmx_ik_bone.loopCount = c.iterations
                    pmx_ik_bone.transform_order += 1
                    pmx_ik_bone.target = bone_map[ik_target_bone.name]
                    pmx_ik_bone.ik_links = self.__exportIKLinks(bone, pmx_bones, bone_map, [], c.chain_count)

    def __get_connected_child_bone(self, target_bone):
        """ Get a connected child bone.

         Args:
             target_bone: A blender PoseBone

         Returns:
             A bpy.types.PoseBone object which is the closest bone from the tail position of target_bone.
             Return None if target_bone has no child bones.
        """
        r = None
        min_length = None
        for c in target_bone.children:
            length = (c.head - target_bone.tail).length
            if not min_length or length < min_length:
                min_length = length
                r = c
        return r

    def __exportVertexMorphs(self, meshes, root):
        shape_key_names = []
        for mesh in meshes:
            for i in mesh.shape_key_names:
                if i not in shape_key_names:
                    shape_key_names.append(i)

        morph_categories = {}
        if root:
            categories = {
                'SYSTEM': pmx.Morph.CATEGORY_SYSTEM,
                'EYEBROW': pmx.Morph.CATEGORY_EYEBROW,
                'EYE': pmx.Morph.CATEGORY_EYE,
                'MOUTH': pmx.Morph.CATEGORY_MOUTH,
                }
            for item in root.mmd_root.display_item_frames[u'表情'].items:
                morph_categories[item.name] = categories.get(item.morph_category, pmx.Morph.CATEGORY_OHTER)

        for i in shape_key_names:
            exported_vert = set()
            morph = pmx.VertexMorph(i, '', 4)
            morph.category = morph_categories.get(i, pmx.Morph.CATEGORY_OHTER)
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

    def __export_material_morphs(self, root):
        mmd_root = root.mmd_root
        for morph in mmd_root.material_morphs:
            mat_morph = pmx.MaterialMorph(
                name=morph.name,
                name_e=morph.name_e,
                category=morph.category
            )
            for data in morph.data:
                morph_data = pmx.MaterialMorphOffset()
                try:
                    morph_data.index = self.__material_name_table.index(data.material)
                except ValueError:
                    morph_data.index = -1
                morph_data.diffuse_offset = data.diffuse_color
                morph_data.specular_offset = data.specular_color
                morph_data.ambient_offset = data.ambient_color
                morph_data.edge_color_offset = data.edge_color
                morph_data.edge_size_offset = data.edge_weight
                morph_data.texture_factor = data.texture_factor
                morph_data.sphere_texture_factor = data.sphere_texture_factor
                morph_data.toon_texture_factor = data.toon_texture_factor
                mat_morph.offsets.append(morph_data)
            self.__model.morphs.append(mat_morph)

    def __sortMaterials(self):
        """ sort materials for alpha blending

         モデル内全頂点の平均座標をモデルの中心と考えて、
         モデル中心座標とマテリアルがアサインされている全ての面の構成頂点との平均距離を算出。
         この値が小さい順にソートしてみる。
         モデル中心座標から離れている位置で使用されているマテリアルほどリストの後ろ側にくるように。
         かなりいいかげんな実装
        """
        center = mathutils.Vector([0, 0, 0])
        vertices = self.__model.vertices
        vert_num = len(vertices)
        for v in self.__model.vertices:
            center += mathutils.Vector(v.co) / vert_num

        faces = self.__model.faces
        offset = 0
        distances = []
        for mat in self.__model.materials:
            d = 0
            face_num = int(mat.vertex_count / 3)
            for i in range(offset, offset + face_num):
                face = faces[i]
                d += (mathutils.Vector(vertices[face[0]].co) - center).length
                d += (mathutils.Vector(vertices[face[1]].co) - center).length
                d += (mathutils.Vector(vertices[face[2]].co) - center).length
            distances.append((d/mat.vertex_count, mat, offset, face_num))
            offset += face_num
        sorted_faces = []
        sorted_mat = []
        for mat, offset, vert_count in [(x[1], x[2], x[3]) for x in sorted(distances, key=lambda x: x[0])]:
            sorted_faces.extend(faces[offset:offset+vert_count])
            sorted_mat.append(mat)
        self.__model.materials = sorted_mat
        self.__model.faces = sorted_faces

    def __export_bone_morphs(self, root):
        mmd_root = root.mmd_root
        for morph in mmd_root.bone_morphs:
            bone_morph = pmx.BoneMorph(
                name=morph.name,
                name_e=morph.name_e,
                category=morph.category
            )
            for data in morph.data:
                morph_data = pmx.BoneMorphOffset()
                try:
                    morph_data.index = self.__bone_name_table.index(data.bone)
                except ValueError:
                    morph_data.index = -1
                morph_data.location_offset = data.location
                morph_data.rotation_offset = data.rotation
                bone_morph.offsets.append(morph_data)
            self.__model.morphs.append(bone_morph)

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


    def __exportRigidBodies(self, rigid_bodies, bone_map):
        rigid_map = {}
        rigid_cnt = 0
        for obj in rigid_bodies:
            p_rigid = pmx.Rigid()
            p_rigid.name = obj.mmd_rigid.name
            p_rigid.name_e = obj.mmd_rigid.name_e
            p_rigid.location = mathutils.Vector(obj.location) * self.__scale * self.TO_PMX_MATRIX
            p_rigid.rotation = mathutils.Vector(obj.rotation_euler) * self.TO_PMX_MATRIX * -1
            p_rigid.mode = int(obj.mmd_rigid.type)

            rigid_shape = obj.mmd_rigid.shape
            shape_size = mathutils.Vector(mmd_model.getRigidBodySize(obj))
            if rigid_shape == 'SPHERE':
                p_rigid.type = 0
                p_rigid.size = shape_size * self.__scale
            elif rigid_shape == 'BOX':
                p_rigid.type = 1
                p_rigid.size = shape_size * self.__scale * self.TO_PMX_MATRIX
            elif rigid_shape == 'CAPSULE':
                p_rigid.type = 2
                p_rigid.size = shape_size * self.__scale
            else:
                raise Exception('Invalid rigid body type: %s %s', obj.name, rigid_shape)

            p_rigid.collision_group_number = obj.mmd_rigid.collision_group_number
            mask = 0
            for i, v in enumerate(obj.mmd_rigid.collision_group_mask):
                if not v:
                    mask += (1<<i)
            p_rigid.collision_group_mask = mask

            rb = obj.rigid_body
            p_rigid.mass = rb.mass
            p_rigid.friction = rb.friction
            p_rigid.bounce = rb.restitution
            p_rigid.velocity_attenuation = rb.linear_damping
            p_rigid.rotation_attenuation = rb.angular_damping

            if 'mmd_tools_rigid_parent' in obj.constraints:
                constraint = obj.constraints['mmd_tools_rigid_parent']
                bone = constraint.subtarget
                p_rigid.bone = bone_map.get(bone, -1)
            self.__model.rigids.append(p_rigid)
            rigid_map[obj] = rigid_cnt
            rigid_cnt += 1
        return rigid_map

    def __exportJoints(self, joints, rigid_map):
        for joint in joints:
            rbc = joint.rigid_body_constraint
            p_joint = pmx.Joint()
            mmd_joint = joint.mmd_joint
            p_joint.name = mmd_joint.name_j
            p_joint.name_e = mmd_joint.name_e
            p_joint.location = (mathutils.Vector(joint.location) * self.TO_PMX_MATRIX * self.__scale).xyz
            p_joint.rotation = (mathutils.Vector(joint.rotation_euler) * self.TO_PMX_MATRIX * -1).xyz
            p_joint.src_rigid = rigid_map.get(rbc.object1, -1)
            p_joint.dest_rigid = rigid_map.get(rbc.object2, -1)
            p_joint.maximum_location = (mathutils.Vector([
                rbc.limit_lin_x_upper,
                rbc.limit_lin_y_upper,
                rbc.limit_lin_z_upper,
                ]) * self.TO_PMX_MATRIX * self.__scale).xyz
            p_joint.minimum_location =(mathutils.Vector([
                rbc.limit_lin_x_lower,
                rbc.limit_lin_y_lower,
                rbc.limit_lin_z_lower,
                ]) * self.TO_PMX_MATRIX * self.__scale).xyz
            p_joint.maximum_rotation = (mathutils.Vector([
                rbc.limit_ang_x_lower,
                rbc.limit_ang_y_lower,
                rbc.limit_ang_z_lower,
                ]) * self.TO_PMX_MATRIX * -1).xyz
            p_joint.minimum_rotation = (mathutils.Vector([
                rbc.limit_ang_x_upper,
                rbc.limit_ang_y_upper,
                rbc.limit_ang_z_upper,
                ]) * self.TO_PMX_MATRIX * -1).xyz

            p_joint.spring_constant = (mathutils.Vector(mmd_joint.spring_linear) * self.TO_PMX_MATRIX).xyz
            p_joint.spring_rotation_constant = (mathutils.Vector(mmd_joint.spring_angular) * self.TO_PMX_MATRIX).xyz
            self.__model.joints.append(p_joint)


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
                list([(x.group, x.weight) for x in v.groups if x.weight > 0]),
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
        root = args.get('root', None)
        self.__model = pmx.Model()
        self.__model.name = 'test'
        self.__model.name_e = 'test eng'
        if root is not None:
            self.__model.name = root.mmd_root.name
            self.__model.name_e = root.mmd_root.name_e

        self.__model.comment = 'exported by mmd_tools'

        meshes = args.get('meshes', [])
        self.__armature = args.get('armature', None)
        rigid_bodeis = args.get('rigid_bodies', [])
        joints = args.get('joints', [])        
        self.__copyTextures = args.get('copy_textures', False)
        self.__filepath = filepath

        self.__scale = 1.0/float(args.get('scale', 0.2))


        nameMap = self.__exportBones()
        self.__exportIK(nameMap)

        mesh_data = []
        for i in meshes:
            mesh_data.append(self.__loadMeshData(i))

        self.__exportMeshes(mesh_data, nameMap)
        self.__exportVertexMorphs(mesh_data, root)
        self.__sortMaterials()
        rigid_map = self.__exportRigidBodies(rigid_bodeis, nameMap)
        self.__exportJoints(joints, rigid_map)
        if root is not None:
            self.__exportDisplayItems(root, nameMap)
            self.__export_bone_morphs(root)
            self.__export_material_morphs(root)

        if self.__copyTextures:
            tex_dir = os.path.join(os.path.dirname(filepath), 'textures')
            self.__copy_textures(tex_dir)

        pmx.save(filepath, self.__model)

def export(filepath, **kwargs):
    exporter = __PmxExporter()
    exporter.execute(filepath, **kwargs)
