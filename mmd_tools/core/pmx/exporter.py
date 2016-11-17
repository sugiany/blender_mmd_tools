# -*- coding: utf-8 -*-
import os
import copy
import logging
import shutil
import time

import mathutils
import bpy
import bmesh

from collections import OrderedDict
from mmd_tools.core import pmx
from mmd_tools.core.bone import FnBone
from mmd_tools.core.material import FnMaterial
from mmd_tools.core.vmd.exporter import VMDExporter
from mmd_tools import bpyutils
from mmd_tools.utils import saferelpath


class _Vertex:
    def __init__(self, co, groups, offsets, old_index, edge_scale, vertex_order):
        self.co = copy.deepcopy(co)
        self.groups = copy.copy(groups) # [(group_number, weight), ...]
        self.offsets = copy.deepcopy(offsets)
        self.old_index = old_index # used for exporting uv morphs
        self.edge_scale = edge_scale
        self.vertex_order = vertex_order # used for controlling vertex order
        self.index = None
        self.uv = None
        self.normal = None
        self.sdef_data = None # (C, R0, R1)

class _Face:
    def __init__(self, vertices):
        ''' Temporary Face Class
        '''
        self.vertices = copy.copy(vertices)

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

class _DefaultMaterial:
    def __init__(self):
        mat = bpy.data.materials.new('')
        #mat.mmd_material.diffuse_color = (0, 0, 0)
        #mat.mmd_material.specular_color = (0, 0, 0)
        #mat.mmd_material.ambient_color = (0, 0, 0)
        self.material = mat
        logging.debug('create default material: %s', str(self.material))

    def __del__(self):
        if self.material:
            logging.debug('remove default material: %s', str(self.material))
            bpy.data.materials.remove(self.material)


class __PmxExporter:
    TO_PMX_MATRIX = mathutils.Matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]])
    CATEGORIES = {
        'SYSTEM': pmx.Morph.CATEGORY_SYSTEM,
        'EYEBROW': pmx.Morph.CATEGORY_EYEBROW,
        'EYE': pmx.Morph.CATEGORY_EYE,
        'MOUTH': pmx.Morph.CATEGORY_MOUTH,
        }

    def __init__(self):
        self.__model = None
        self.__bone_name_table = []
        self.__material_name_table = []
        self.__vertex_index_map = {} # used for exporting uv morphs
        self.__default_material = None
        self.__vertex_order_map = None # used for controlling vertex order

    @staticmethod
    def flipUV_V(uv):
        u, v = uv
        return [u, 1.0-v]

    def __getDefaultMaterial(self):
        if self.__default_material is None:
            self.__default_material = _DefaultMaterial()
        return self.__default_material.material

    def __sortVertices(self):
        logging.info(' - Sorting vertices ...')
        weight_items = self.__vertex_order_map.items()
        sorted_indices = [i[0] for i in sorted(weight_items, key=lambda x: x[1].vertex_order)]
        vertices = self.__model.vertices
        self.__model.vertices = [vertices[i] for i in sorted_indices]

        # update indices
        index_map = {x:i for i, x in enumerate(sorted_indices)}
        for v in self.__vertex_order_map.values(): # for vertex morphs
            v.index = index_map[v.index]
        for v in self.__vertex_index_map.values(): # for uv morphs
            v[:] = [index_map[i] for i in v]
        for f in self.__model.faces:
            f[:] = [index_map[i] for i in f]
        logging.debug('   - Done (count:%d)', len(self.__vertex_order_map))

    def __exportMeshes(self, meshes, bone_map):
        mat_map = OrderedDict()
        for mesh in meshes:
            for index, mat_faces in sorted(mesh.material_faces.items(), key=lambda x: x[0]):
                name = mesh.materials[index].name
                if name not in mat_map:
                    mat_map[name] = []
                mat_map[name].append((mat_faces, mesh.vertex_group_names))

        sort_vertices = self.__vertex_order_map is not None
        if sort_vertices:
            self.__vertex_order_map.clear()

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
                    if v.old_index is not None:
                        self.__vertex_index_map[v.old_index].append(v.index)
                    if sort_vertices:
                        self.__vertex_order_map[v.index] = v

                    pv = pmx.Vertex()
                    pv.co = list(v.co)
                    pv.normal = v.normal
                    pv.uv = self.flipUV_V(v.uv)
                    pv.edge_scale = v.edge_scale

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
                        w1, w2 = vg1[1], vg2[1]
                        weight.weights = [w1/(w1+w2)]
                        if v.sdef_data:
                            weight.type = pmx.BoneWeight.SDEF
                            sdef_weights = pmx.BoneWeightSDEF()
                            sdef_weights.weight = weight.weights[0]
                            sdef_weights.c = v.sdef_data[0]
                            sdef_weights.r0 = v.sdef_data[1]
                            sdef_weights.r1 = v.sdef_data[2]
                            weight.weights = sdef_weights
                        pv.weight = weight
                    else:
                        weight = pmx.BoneWeight()
                        weight.type = pmx.BoneWeight.BDEF4
                        weight.bones = [-1, -1, -1, -1]
                        weight.weights = [0.0, 0.0, 0.0, 0.0]
                        w_all = 0.0
                        for i in range(min(len(v.groups), 4)):
                            gn, w = v.groups[i]
                            weight.bones[i] = bone_map[vertex_group_names[gn]]
                            weight.weights[i] = w
                            w_all += w
                        for i in range(4):
                            weight.weights[i] /= w_all
                        pv.weight = weight
                    self.__model.vertices.append(pv)

                for face in mat_faces:
                    self.__model.faces.append([x.index for x in face.vertices])
                face_count += len(mat_faces)
            self.__exportMaterial(bpy.data.materials[mat_name], face_count)

        if sort_vertices:
            self.__sortVertices()

    def __exportTexture(self, filepath):
        if filepath.strip() == '':
            return -1
        # Use bpy.path to resolve '//' in .blend relative filepaths
        filepath = bpy.path.abspath(filepath)
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

    def __copy_textures(self, output_dir, base_folder=''):
        tex_dir = output_dir
        tex_dir_fallback = os.path.join(tex_dir, 'textures')
        tex_dir_preference = bpyutils.addon_preferences('base_texture_folder', '')
        for texture in self.__model.textures:
            path = texture.path
            tex_dir = output_dir  # restart to the default directory at each loop
            if not os.path.isfile(path):
                logging.warning('*** skipping texture file which does not exist: %s', path)
                continue
            dst_name = os.path.basename(path)
            if base_folder != '':
                dst_name = saferelpath(path, base_folder, strategy='outside')
                if dst_name.startswith('..'):
                    # Check if the texture comes from the preferred folder
                    if tex_dir_preference:
                        dst_name = saferelpath(path, tex_dir_preference, strategy='outside')
                    if dst_name.startswith('..'):
                        # If the code reaches here the texture is somewhere else
                        logging.warning('The texture %s is not inside the base texture folder', path)
                        # Fall back to basename and textures folder
                        dst_name = os.path.basename(path)
                        tex_dir = tex_dir_fallback
            else:
                tex_dir = tex_dir_fallback
            dest_path = os.path.join(tex_dir, dst_name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            if path != dest_path:  # Only copy if the paths are different                        
                shutil.copyfile(path, dest_path)
                logging.info('Copy file %s --> %s', path, dest_path)
            texture.path = dest_path

    def __exportMaterial(self, material, num_faces):
        p_mat = pmx.Material()
        mmd_mat = material.mmd_material

        p_mat.name = mmd_mat.name_j or material.name
        p_mat.name_e = mmd_mat.name_e or material.name
        p_mat.diffuse = list(mmd_mat.diffuse_color) + [mmd_mat.alpha]
        p_mat.ambient = mmd_mat.ambient_color
        p_mat.specular = mmd_mat.specular_color
        p_mat.shininess = mmd_mat.shininess
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
        fnMat = FnMaterial(material)
        tex = fnMat.get_texture()
        if tex and tex.type == 'IMAGE':  # Ensure the texture is an image
            index = self.__exportTexture(tex.image.filepath)
            p_mat.texture = index
        tex = fnMat.get_sphere_texture()
        if tex and tex.type == 'IMAGE':  # Ensure the texture is an image
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

    def __exportBones(self, meshes):
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

        # determine the bone order
        vtx_grps = {}
        for mesh in meshes:
            if mesh.modifiers.get('mmd_bone_order_override', None):
                vtx_grps = mesh.vertex_groups
                break

        class _Dummy:
            index = float('inf')
        sorted_bones = sorted(pose_bones, key=lambda x: vtx_grps.get(x.name, _Dummy).index)
        #sorted_bones = sorted(pose_bones, key=self.__countBoneDepth)

        pmx_matrix = self.TO_PMX_MATRIX * world_mat * self.__scale
        def __to_pmx_location(loc):
            return pmx_matrix * mathutils.Vector(loc)
        if True: # no need to enter edit mode
            for p_bone in sorted_bones:
                if p_bone.is_mmd_shadow_bone:
                    continue
                bone = p_bone.bone
                mmd_bone = p_bone.mmd_bone
                pmx_bone = pmx.Bone()
                pmx_bone.name = mmd_bone.name_j or bone.name
                pmx_bone.name_e = mmd_bone.name_e or bone.name

                pmx_bone.hasAdditionalRotate = mmd_bone.has_additional_rotation
                pmx_bone.hasAdditionalLocation = mmd_bone.has_additional_location
                pmx_bone.additionalTransform = [None, mmd_bone.additional_transform_influence]
                if mmd_bone.additional_transform_bone_id != -1:
                    fnBone = FnBone.from_bone_id(arm, mmd_bone.additional_transform_bone_id)
                    if fnBone:
                        pmx_bone.additionalTransform[0] = fnBone.pose_bone

                pmx_bone.location = __to_pmx_location(p_bone.head)
                pmx_bone.parent = bone.parent
                pmx_bone.visible = mmd_bone.is_visible
                pmx_bone.isControllable = mmd_bone.is_controllable
                pmx_bone.isMovable = not all(p_bone.lock_location)
                pmx_bone.isRotatable = not all(p_bone.lock_rotation)
                pmx_bone.transform_order = mmd_bone.transform_order
                pmx_bone.transAfterPhis = mmd_bone.transform_after_dynamics
                pmx_bones.append(pmx_bone)
                self.__bone_name_table.append(p_bone.name)
                boneMap[bone] = pmx_bone
                r[bone.name] = len(pmx_bones) - 1

                if bone.use_connect and p_bone.parent.mmd_bone.is_tip:
                    logging.debug(' * fix location of bone %s, parent %s is tip', bone.name, bone.parent.name)
                    pmx_bone.location = boneMap[bone.parent].location

                # a connected child bone is prefered
                pmx_bone.displayConnection = None
                for child in bone.children:
                    if child.use_connect:
                        pmx_bone.displayConnection = child
                        break
                if not pmx_bone.displayConnection:
                    if mmd_bone.is_tip:
                        pmx_bone.displayConnection = -1
                    else:
                        tail_loc = __to_pmx_location(p_bone.tail)
                        pmx_bone.displayConnection = tail_loc - pmx_bone.location

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
                elif isinstance(i.displayConnection, bpy.types.Bone):
                    i.displayConnection = pmx_bones.index(boneMap[i.displayConnection])

                pose_bone = i.additionalTransform[0]
                i.additionalTransform[0] = r.get(pose_bone.name, -1) if pose_bone else -1

            if len(pmx_bones) == 0:
                # avoid crashing MMD
                pmx_bone = pmx.Bone()
                pmx_bone.name = u'全ての親'
                pmx_bone.name_e = 'Root'
                pmx_bone.location = __to_pmx_location([0,0,0])
                tail_loc = __to_pmx_location([0,0,1])
                pmx_bone.displayConnection = tail_loc - pmx_bone.location
                pmx_bones.append(pmx_bone)

            self.__model.bones = pmx_bones
        return r

    @staticmethod
    def __convertIKLimitAngles(min_angle, max_angle, pose_bone):
        mat = mathutils.Matrix([
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0]])

        def __align_rotation(rad):
            from math import pi
            base_rad = -pi/2 if rad < 0 else pi/2
            return int(0.5 + rad/base_rad) * base_rad

        rot = pose_bone.bone.matrix_local.to_euler()
        rot.x = __align_rotation(rot.x)
        rot.y = __align_rotation(rot.y)
        rot.z = __align_rotation(rot.z)
        m = mat * rot.to_matrix().transposed().inverted() * -1

        new_min_angle = m * mathutils.Vector(min_angle)
        new_max_angle = m * mathutils.Vector(max_angle)
        for i in range(3):
            if new_min_angle[i] > new_max_angle[i]:
                new_min_angle[i], new_max_angle[i] = new_max_angle[i], new_min_angle[i]
        return new_min_angle, new_max_angle

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
                minimum.append(pose_bone.ik_min_x)
                maximum.append(pose_bone.ik_max_x)
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

            ik_limit_override = pose_bone.constraints.get('mmd_ik_limit_override', None)
            if ik_limit_override:
                if ik_limit_override.use_limit_x:
                    minimum[0] = ik_limit_override.min_x
                    maximum[0] = ik_limit_override.max_x
                if ik_limit_override.use_limit_y:
                    minimum[1] = ik_limit_override.min_y
                    maximum[1] = ik_limit_override.max_y
                if ik_limit_override.use_limit_z:
                    minimum[2] = ik_limit_override.min_z
                    maximum[2] = ik_limit_override.max_z

            minimum, maximum = self.__convertIKLimitAngles(minimum, maximum, pose_bone)
            ik_link.minimumAngle = list(minimum)
            ik_link.maximumAngle = list(maximum)

        if pose_bone.parent is not None:
            return self.__exportIKLinks(pose_bone.parent, pmx_bones, bone_map, ik_links + [ik_link], count - 1)
        else:
            return ik_links + [ik_link]


    def __exportIK(self, bone_map):
        """ Export IK constraints
         @param bone_map the dictionary to map Blender bone names to bone indices of the pmx.model instance.
        """
        pmx_bones = self.__model.bones
        arm = self.__armature
        ik_loop_factor = max(arm.get('mmd_ik_loop_factor', 1), 1)
        pose_bones = arm.pose.bones
        for bone in pose_bones:
            if bone.is_mmd_shadow_bone:
                continue
            for c in bone.constraints:
                if c.type == 'IK'and not c.mute:
                    logging.debug('  Found IK constraint.')
                    ik_pose_bone = pose_bones[c.subtarget]
                    if ik_pose_bone.mmd_shadow_bone_type == 'IK_TARGET':
                        ik_bone_index = bone_map[ik_pose_bone.parent.name]
                        logging.debug('  Found IK proxy bone: %s -> %s', ik_pose_bone.name, ik_pose_bone.parent.name)
                    else:
                        ik_bone_index = bone_map[c.subtarget]

                    ik_target_bone = self.__get_ik_target_bone(bone)
                    if ik_target_bone is None:
                        logging.warning('  - IK bone: %s, IK Target not found !!!', pmx_ik_bone.name)
                        continue
                    pmx_ik_bone = pmx_bones[ik_bone_index]
                    logging.debug('  - IK bone: %s, IK Target: %s', pmx_ik_bone.name, ik_target_bone.name)
                    pmx_ik_bone.isIK = True
                    pmx_ik_bone.loopCount = max(int(c.iterations/ik_loop_factor), 1)
                    pmx_ik_bone.rotationConstraint = bone.mmd_bone.ik_rotation_constraint
                    pmx_ik_bone.target = bone_map[ik_target_bone.name]
                    pmx_ik_bone.ik_links = self.__exportIKLinks(bone, pmx_bones, bone_map, [], c.chain_count)

    def __get_ik_target_bone(self, target_bone):
        """ Get mmd ik target bone.

         Args:
             target_bone: A blender PoseBone

         Returns:
             A bpy.types.PoseBone object which is the closest bone from the tail position of target_bone.
             Return None if target_bone has no child bones.
        """
        valid_children = [c for c in target_bone.children if not c.is_mmd_shadow_bone]

        # search 'mmd_ik_target_override' first
        for c in valid_children:
            ik_target_override = c.constraints.get('mmd_ik_target_override', None)
            if ik_target_override and ik_target_override.subtarget == target_bone.name:
                logging.debug('  (use "mmd_ik_target_override")')
                return c

        r = None
        min_length = None
        for c in valid_children:
            if c.bone.use_connect:
                return c
            length = (c.head - target_bone.tail).length
            if min_length is None or length < min_length:
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
        morph_english_names = {}
        if root:
            categories = self.CATEGORIES
            for vtx_morph in root.mmd_root.vertex_morphs:
                morph_english_names[vtx_morph.name] = vtx_morph.name_e
                morph_categories[vtx_morph.name] = categories.get(vtx_morph.category, pmx.Morph.CATEGORY_OHTER)

        for i in shape_key_names:
            exported_vert = set()
            morph = pmx.VertexMorph(i, '', 4)
            morph.name_e = morph_english_names.get(i, '')
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

                        offset = v.offsets.get(i, None)
                        if offset is None:
                            continue

                        mo = pmx.VertexMorphOffset()
                        mo.index = v.index
                        mo.offset = offset
                        morph.offsets.append(mo)
            self.__model.morphs.append(morph)

    def __export_material_morphs(self, root):
        mmd_root = root.mmd_root
        categories = self.CATEGORIES
        for morph in mmd_root.material_morphs:
            mat_morph = pmx.MaterialMorph(
                name=morph.name,
                name_e=morph.name_e,
                category=categories.get(morph.category, pmx.Morph.CATEGORY_OHTER)
            )
            for data in morph.data:
                morph_data = pmx.MaterialMorphOffset()
                try:
                    if data.material != '':
                        morph_data.index = self.__material_name_table.index(data.material)
                    else:
                        morph_data.index = -1
                except ValueError:
                    logging.warning('Material Morph (%s): Material %s was not found.', morph.name, data.material)
                    continue
                morph_data.offset_type = ['MULT', 'ADD'].index(data.offset_type)
                morph_data.diffuse_offset = data.diffuse_color
                morph_data.specular_offset = data.specular_color
                morph_data.shininess_offset = data.shininess
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
        for mat, bl_mat_name in zip(self.__model.materials, self.__material_name_table):
            d = 0
            face_num = int(mat.vertex_count / 3)
            for i in range(offset, offset + face_num):
                face = faces[i]
                d += (mathutils.Vector(vertices[face[0]].co) - center).length
                d += (mathutils.Vector(vertices[face[1]].co) - center).length
                d += (mathutils.Vector(vertices[face[2]].co) - center).length
            distances.append((d/mat.vertex_count, mat, offset, face_num, bl_mat_name))
            offset += face_num
        sorted_faces = []
        sorted_mat = []
        self.__material_name_table.clear()
        for d, mat, offset, vert_count, bl_mat_name in sorted(distances, key=lambda x: x[0]):
            sorted_faces.extend(faces[offset:offset+vert_count])
            sorted_mat.append(mat)
            self.__material_name_table.append(bl_mat_name)
        self.__model.materials = sorted_mat
        self.__model.faces = sorted_faces

    def __export_bone_morphs(self, root):
        mmd_root = root.mmd_root
        if len(mmd_root.bone_morphs) == 0:
            return
        categories = self.CATEGORIES
        pose_bones = self.__armature.pose.bones
        for morph in mmd_root.bone_morphs:
            bone_morph = pmx.BoneMorph(
                name=morph.name,
                name_e=morph.name_e,
                category=categories.get(morph.category, pmx.Morph.CATEGORY_OHTER)
            )
            for data in morph.data:
                morph_data = pmx.BoneMorphOffset()
                try:
                    morph_data.index = self.__bone_name_table.index(data.bone)
                except ValueError:
                    morph_data.index = -1
                blender_bone = pose_bones.get(data.bone, None)
                if blender_bone is None:
                    logging.warning('Bone Morph (%s): Bone %s was not found.', morph.name, data.bone)
                    continue
                mat = VMDExporter.makeVMDBoneLocationMatrix(blender_bone)
                morph_data.location_offset = mat * mathutils.Vector(data.location) * self.__scale
                rw, rx, ry, rz = VMDExporter.convertToVMDBoneRotation(blender_bone, data.rotation)
                morph_data.rotation_offset = (rx, ry, rz, rw)
                bone_morph.offsets.append(morph_data)
            self.__model.morphs.append(bone_morph)

    def __export_uv_morphs(self, root):
        mmd_root = root.mmd_root
        if len(mmd_root.uv_morphs) == 0:
            return
        categories = self.CATEGORIES
        for morph in mmd_root.uv_morphs:
            uv_morph = pmx.UVMorph(
                name=morph.name,
                name_e=morph.name_e,
                category=categories.get(morph.category, pmx.Morph.CATEGORY_OHTER)
            )
            offsets = []
            for data in morph.data:
                dx, dy, dz, dw = data.offset
                offset = (dx, -dy, 0, 0) # dz, dw are not used
                for idx in self.__vertex_index_map.get(data.index, []):
                    morph_data = pmx.UVMorphOffset()
                    morph_data.index = idx
                    morph_data.offset = offset
                    offsets.append(morph_data)
            uv_morph.offsets = sorted(offsets, key=lambda x: x.index)
            self.__model.morphs.append(uv_morph)

    def __export_group_morphs(self, root):
        mmd_root = root.mmd_root
        if len(mmd_root.group_morphs) == 0:
            return
        categories = self.CATEGORIES
        start_index = len(self.__model.morphs)
        for morph in mmd_root.group_morphs:
            group_morph = pmx.GroupMorph(
                name=morph.name,
                name_e=morph.name_e,
                category=categories.get(morph.category, pmx.Morph.CATEGORY_OHTER)
            )
            self.__model.morphs.append(group_morph)

        morph_map = self.__get_pmx_morph_map()
        for morph, group_morph in zip(mmd_root.group_morphs, self.__model.morphs[start_index:]):
            for data in morph.data:
                morph_index = morph_map.get((data.morph_type, data.name), -1)
                if morph_index < 0:
                    logging.warning('Group Morph (%s): Morph %s was not found.', morph.name, data.name)
                    continue
                morph_data = pmx.GroupMorphOffset()
                morph_data.morph = morph_index
                morph_data.factor = data.factor
                group_morph.offsets.append(morph_data)

    def __exportDisplayItems(self, root, bone_map):
        res = []
        morph_map = self.__get_pmx_morph_map()
        for i in root.mmd_root.display_item_frames:
            d = pmx.Display()
            d.name = i.name
            d.name_e = i.name_e
            d.isSpecial = i.is_special
            items = []
            for j in i.items:
                if j.type == 'BONE' and j.name in bone_map:
                    items.append((0, bone_map[j.name]))
                elif j.type == 'MORPH' and (j.morph_type, j.name) in morph_map:
                    items.append((1, morph_map[(j.morph_type, j.name)]))
                else:
                    logging.warning('Display item (%s, %s) was not found.', j.type, j.name)
            d.data = items
            res.append(d)
        self.__model.display = res

    def __get_pmx_morph_map(self):
        morph_types = {
            pmx.GroupMorph : 'group_morphs',
            pmx.VertexMorph : 'vertex_morphs',
            pmx.BoneMorph : 'bone_morphs',
            pmx.UVMorph : 'uv_morphs',
            pmx.MaterialMorph : 'material_morphs',
            }
        morph_map = {}
        for i, m in enumerate(self.__model.morphs):
            morph_map[(morph_types[type(m)], m.name)] = i
        return morph_map


    def __exportRigidBodies(self, rigid_bodies, bone_map):
        rigid_map = {}
        rigid_cnt = 0
        for obj in rigid_bodies:
            rb = obj.rigid_body
            if rb is None:
                logging.warning(' * Settings of rigid body "%s" not found, skipped!', obj.name)
                continue
            p_rigid = pmx.Rigid()
            mmd_rigid = obj.mmd_rigid
            p_rigid.name = mmd_rigid.name_j
            p_rigid.name_e = mmd_rigid.name_e
            p_rigid.location = mathutils.Vector(obj.location) * self.__scale * self.TO_PMX_MATRIX
            p_rigid.rotation = mathutils.Vector(obj.rotation_euler) * self.TO_PMX_MATRIX * -1
            p_rigid.mode = int(mmd_rigid.type)

            rigid_shape = mmd_rigid.shape
            shape_size = mathutils.Vector(mmd_rigid.size)
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

            p_rigid.bone = bone_map.get(mmd_rigid.bone, -1)
            p_rigid.collision_group_number = mmd_rigid.collision_group_number
            mask = 0
            for i, v in enumerate(mmd_rigid.collision_group_mask):
                if not v:
                    mask += (1<<i)
            p_rigid.collision_group_mask = mask

            p_rigid.mass = rb.mass
            p_rigid.friction = rb.friction
            p_rigid.bounce = rb.restitution
            p_rigid.velocity_attenuation = rb.linear_damping
            p_rigid.rotation_attenuation = rb.angular_damping

            self.__model.rigids.append(p_rigid)
            rigid_map[obj] = rigid_cnt
            rigid_cnt += 1
        return rigid_map

    def __exportJoints(self, joints, rigid_map):
        for joint in joints:
            rbc = joint.rigid_body_constraint
            if rbc is None:
                logging.warning(' * Settings of joint "%s" not found, skipped!', joint.name)
                continue
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
    def __convertFaceUVToVertexUV(vert_index, uv, normal, vertices_map):
        vertices = vertices_map[vert_index]
        for i in vertices:
            if i.uv is None:
                i.uv = uv
                i.normal = normal
                return i
            elif (i.uv[0] - uv[0])**2 + (i.uv[1] - uv[1])**2 < 0.0001 and (normal - i.normal).length < 0.01:
                return i
        n = copy.deepcopy(i)
        n.uv = uv
        n.normal = normal
        vertices.append(n)
        return n

    @staticmethod
    def __triangulate(mesh, custom_normals):
        bm = bmesh.new()
        bm.from_mesh(mesh)

        is_triangulated = True
        face_verts_to_loop_id_map = {}

        loop_id = 0
        for f in bm.faces:
            vert_to_loop_id = face_verts_to_loop_id_map.setdefault(f, {})
            if is_triangulated and len(f.verts) != 3:
                is_triangulated = False
            for v in f.verts:
                vert_to_loop_id[v] = loop_id
                loop_id += 1

        loop_normals = None
        if is_triangulated:
            loop_normals = custom_normals
        else:
            face_map = bmesh.ops.triangulate(bm, faces=bm.faces, quad_method=1, ngon_method=1)['face_map']
            logging.debug(' - Remapping custom normals...')
            loop_normals = []
            for f in bm.faces:
                vert_to_loop_id = face_verts_to_loop_id_map[face_map.get(f, f)]
                for v in f.verts:
                    loop_normals.append(custom_normals[vert_to_loop_id[v]])
            logging.debug('   - Done (faces:%d)', len(bm.faces))
            bm.to_mesh(mesh)
            face_map.clear()
        face_verts_to_loop_id_map.clear()
        bm.free()

        assert(len(loop_normals) == len(mesh.loops))
        return loop_normals

    @staticmethod
    def __get_normals(mesh, matrix):
        custom_normals = None
        if hasattr(mesh, 'has_custom_normals'):
            logging.debug(' - Calculating normals split...')
            mesh.calc_normals_split()
            custom_normals = [(matrix * l.normal).normalized() for l in mesh.loops]
            mesh.free_normals_split()
        elif mesh.use_auto_smooth:
            logging.debug(' - Calculating normals split (angle:%f)...', mesh.auto_smooth_angle)
            mesh.calc_normals_split(mesh.auto_smooth_angle)
            custom_normals = [(matrix * l.normal).normalized() for l in mesh.loops]
            mesh.free_normals_split()
        else:
            logging.debug(' - Calculating normals...')
            mesh.calc_normals()
            #custom_normals = [(matrix * mesh.vertices[l.vertex_index].normal).normalized() for l in mesh.loops]
            custom_normals = []
            for f in mesh.polygons:
                if f.use_smooth:
                    for v in f.vertices:
                        custom_normals.append((matrix * mesh.vertices[v].normal).normalized())
                else:
                    for v in f.vertices:
                        custom_normals.append((matrix * f.normal).normalized())
        logging.debug('   - Done (polygons:%d)', len(mesh.polygons))
        return custom_normals

    def __doLoadMeshData(self, meshObj, bone_map, key_blocks):
        vertex_group_names = {i:x.name for i, x in enumerate(meshObj.vertex_groups) if x.name in bone_map}
        vg_edge_scale = meshObj.vertex_groups.get('mmd_edge_scale', None)
        vg_vertex_order = meshObj.vertex_groups.get('mmd_vertex_order', None)

        pmx_matrix = self.TO_PMX_MATRIX * meshObj.matrix_world * self.__scale
        sx, sy, sz = meshObj.matrix_world.to_scale()
        normal_matrix = pmx_matrix.to_3x3()
        if not (sx == sy == sz):
            invert_scale_matrix = mathutils.Matrix([[1.0/sx,0,0], [0,1.0/sy,0], [0,0,1.0/sz]])
            normal_matrix *= invert_scale_matrix # reset the scale of meshObj.matrix_world
            normal_matrix *= invert_scale_matrix # the scale transform of normals

        base_mesh = meshObj.to_mesh(bpy.context.scene, True, 'PREVIEW', False)
        loop_normals = self.__triangulate(base_mesh, self.__get_normals(base_mesh, normal_matrix))
        base_mesh.transform(pmx_matrix)
        base_mesh.update(calc_tessface=True)

        sort_vertices = self.__vertex_order_map is not None
        has_uv_morphs = self.__vertex_index_map is None # currently support for first mesh only
        if has_uv_morphs:
            self.__vertex_index_map = dict([(v.index, []) for v in base_mesh.vertices])


        def _get_weight(vertex_group, vertex, default_weight):
            for i in vertex.groups:
                if i.group == vertex_group.index:
                    return vertex_group.weight(vertex.index)
            return default_weight

        get_edge_scale = None
        if vg_edge_scale:
            get_edge_scale = lambda x: _get_weight(vg_edge_scale, x, 1)
        else:
            get_edge_scale = lambda x: 1

        get_vertex_order = None
        if sort_vertices:
            mesh_id = self.__vertex_order_map.setdefault('mesh_id', 0)
            self.__vertex_order_map['mesh_id'] += 1
            if vg_vertex_order and self.__vertex_order_map['method'] == 'CUSTOM':
                get_vertex_order = lambda x: (mesh_id, _get_weight(vg_vertex_order, x, 2), x.index)
            else:
                get_vertex_order = lambda x: (mesh_id, x.index)
        else:
            get_vertex_order = lambda x: None

        base_vertices = {}
        for v in base_mesh.vertices:
            base_vertices[v.index] = [_Vertex(
                v.co,
                [(x.group, x.weight) for x in v.groups if x.weight > 0 and x.group in vertex_group_names],
                {},
                v.index if has_uv_morphs else None,
                get_edge_scale(v),
                get_vertex_order(v),
                )]

        # restore SDEF data from shape keys
        sdef_shape_key_names = ('mmd_sdef_c', 'mmd_sdef_r0', 'mmd_sdef_r1')
        if all([i in key_blocks for i in sdef_shape_key_names]):
            sdef_counts = 0
            basis_data = key_blocks[0].data
            sdef_c_data = key_blocks[sdef_shape_key_names[0]].data
            sdef_r0_data = key_blocks[sdef_shape_key_names[1]].data
            sdef_r1_data = key_blocks[sdef_shape_key_names[2]].data
            for key in base_vertices.keys():
                c_co = sdef_c_data[key].co
                if (c_co - basis_data[key].co).length < 0.001:
                    continue
                c_co = pmx_matrix * c_co
                r0_co = pmx_matrix * sdef_r0_data[key].co
                r1_co = pmx_matrix * sdef_r1_data[key].co
                base_vertices[key][0].sdef_data = (c_co, r0_co, r1_co)
                sdef_counts += 1
            key_blocks = [i for i in key_blocks if i.name not in sdef_shape_key_names]
            logging.info('Restored %d SDEF vertices', sdef_counts)

        # calculate offsets
        shape_key_names = []
        for i in key_blocks[1:]:
            shape_key_names.append(i.name)
            i.value = 1.0
            mesh = meshObj.to_mesh(bpy.context.scene, True, 'PREVIEW', False)
            mesh.transform(pmx_matrix)
            mesh.update(calc_tessface=True)
            for key in base_vertices.keys():
                base = base_vertices[key][0]
                v = mesh.vertices[key]
                offset = mathutils.Vector(v.co) - mathutils.Vector(base.co)
                if offset.length < 0.001:
                    continue
                base.offsets[i.name] = offset
            bpy.data.meshes.remove(mesh)
            i.value = 0.0

        # load face data
        materials = {}
        uv_data = base_mesh.tessface_uv_textures.active
        if uv_data:
            uv_data = uv_data.data
        else:
            class _DummyUV:
                uv1 = uv2 = uv3 = (0, 0)
            uv_data = iter(lambda: _DummyUV, None)
        for face, uv in zip(base_mesh.tessfaces, uv_data):
            if len(face.vertices) != 3:
                raise Exception
            idx = face.index * 3
            n1, n2, n3 = loop_normals[idx:idx+3]
            v1 = self.__convertFaceUVToVertexUV(face.vertices[0], uv.uv1, n1, base_vertices)
            v2 = self.__convertFaceUVToVertexUV(face.vertices[1], uv.uv2, n2, base_vertices)
            v3 = self.__convertFaceUVToVertexUV(face.vertices[2], uv.uv3, n3, base_vertices)

            t = _Face([v1, v2, v3])
            if face.material_index not in materials:
                materials[face.material_index] = []
            materials[face.material_index].append(t)

        # assign default material
        if len(base_mesh.materials) < len(materials):
            base_mesh.materials.append(self.__getDefaultMaterial())
        else:
            for i, m in enumerate(base_mesh.materials):
                if m is None:
                    base_mesh.materials[i] = self.__getDefaultMaterial()

        return _Mesh(
            base_mesh,
            materials,
            shape_key_names,
            vertex_group_names,
            base_mesh.materials)

    def __loadMeshData(self, meshObj, bone_map):
        show_only_shape_key = meshObj.show_only_shape_key
        meshObj.show_only_shape_key = False

        shape_key_weights = []
        key_blocks = ()
        if meshObj.data.shape_keys:
            key_blocks = meshObj.data.shape_keys.key_blocks
        for i in key_blocks:
            shape_key_weights.append(i.value)
            i.value = 0.0

        muted_modifiers = []
        for m in meshObj.modifiers:
            if m.type != 'ARMATURE' or m.object is None:
                continue
            if m.object.data.pose_position == 'REST':
                muted_modifiers.append((m, m.show_viewport))
                m.show_viewport = False

        try:
            return self.__doLoadMeshData(meshObj, bone_map, key_blocks)
        finally:
            meshObj.show_only_shape_key = show_only_shape_key
            for i, sk in enumerate(key_blocks):
                sk.value = shape_key_weights[i]
            for m, show in muted_modifiers:
                m.show_viewport = show


    def execute(self, filepath, **args):
        root = args.get('root', None)
        self.__model = pmx.Model()
        self.__model.name = 'test'
        self.__model.name_e = 'test eng'
        self.__model.comment = 'exported by mmd_tools'
        self.__model.comment_e = 'exported by mmd_tools'

        if root is not None:
            self.__model.name = root.mmd_root.name
            self.__model.name_e = root.mmd_root.name_e
            txt = bpy.data.texts.get(root.mmd_root.comment_text, None)
            if txt:
                self.__model.comment = txt.as_string().replace('\n', '\r\n')
            txt = bpy.data.texts.get(root.mmd_root.comment_e_text, None)
            if txt:
                self.__model.comment_e = txt.as_string().replace('\n', '\r\n')
            if len(root.mmd_root.uv_morphs) > 0:
                self.__vertex_index_map = None # has_uv_morphs = True

        meshes = args.get('meshes', [])
        meshes = tuple(meshes) # ??? a filter object can only iterate once
        self.__armature = args.get('armature', None)
        rigid_bodeis = args.get('rigid_bodies', [])
        joints = args.get('joints', [])        
        self.__copyTextures = args.get('copy_textures', False)
        self.__filepath = filepath

        self.__scale = 1.0/float(args.get('scale', 0.2))
        sort_materials = args.get('sort_materials', False)
        sort_vertices = args.get('sort_vertices', 'NONE')
        if sort_vertices != 'NONE':
            self.__vertex_order_map = {'method':sort_vertices}


        nameMap = self.__exportBones(meshes)
        self.__exportIK(nameMap)

        mesh_data = []
        for i in meshes:
            mesh_data.append(self.__loadMeshData(i, nameMap))

        self.__exportMeshes(mesh_data, nameMap)
        self.__exportVertexMorphs(mesh_data, root)
        if sort_materials:
            self.__sortMaterials()
        rigid_map = self.__exportRigidBodies(rigid_bodeis, nameMap)
        self.__exportJoints(joints, rigid_map)
        if root is not None:
            self.__export_bone_morphs(root)
            self.__export_material_morphs(root)
            self.__export_uv_morphs(root)
            self.__export_group_morphs(root)
            self.__exportDisplayItems(root, nameMap)

        if self.__copyTextures:
            output_dir = os.path.dirname(filepath)
            import_folder = root.get('import_folder', '') if root else ''
            base_folder = bpyutils.addon_preferences('base_texture_folder', '')
            self.__copy_textures(output_dir, import_folder or base_folder)

        pmx.save(filepath, self.__model)

def export(filepath, **kwargs):
    logging.info('****************************************')
    logging.info(' %s module'%__name__)
    logging.info('----------------------------------------')
    start_time = time.time()
    exporter = __PmxExporter()
    exporter.execute(filepath, **kwargs)
    logging.info(' Finished exporting the model in %f seconds.', time.time() - start_time)
    logging.info('----------------------------------------')
    logging.info(' %s module'%__name__)
    logging.info('****************************************')
