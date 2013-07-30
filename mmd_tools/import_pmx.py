# -*- coding: utf-8 -*-
from . import pmx
from . import utils
from . import rigging
from . import bpyutils

import math

import bpy
import os
import mathutils
import collections
import logging
import time

class PMXImporter:
    TO_BLE_MATRIX = mathutils.Matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]])

    def __init__(self):
        self.__model = None
        self.__targetScene = bpy.context.scene

        self.__scale = None

        self.__root = None
        self.__armObj = None
        self.__meshObj = None
        self.__rigidsSetObj = None
        self.__jointsSetObj = None

        self.__vertexTable = None
        self.__vertexGroupTable = None
        self.__textureTable = None

        self.__boneTable = []
        self.__rigidTable = []
        self.__nonCollisionJointTable = None
        self.__jointTable = []

        self.__materialFaceCountTable = None
        self.__nonCollisionConstraints = []

        # object groups
        self.__allObjGroup = None    # a group which contains all objects created for the target model by mmd_tools.
        self.__mainObjGroup = None    # a group which contains armature and mesh objects.
        self.__rigidObjGroup = None  # a group which contains objects of rigid bodies imported from a pmx model.
        self.__jointObjGroup = None  # a group which contains objects of joints imported from a pmx model.
        self.__tempObjGroup = None   # a group which contains temporary objects.

    @staticmethod
    def flipUV_V(uv):
        u, v = uv
        return [u, 1.0-v]

    def __getMaterialIndexFromFaceIndex(self, face_index):
        count = 0
        for i, c in enumerate(self.__materialFaceCountTable):
            if face_index < count + c:
                return i
            count += c
        raise Exception('invalid face index.')

    def __createObjects(self):
        """ Create main objects and link them to scene.
        """
        pmxModel = self.__model
        self.__rig = rigging.Rig.create(pmxModel.name, pmxModel.name_e, self.__scale)

        # self.__root = bpy.data.objects.new(name=pmxModel.name, object_data=None)
        # self.__root.mmd_type = 'ROOT'
        # self.__targetScene.objects.link(self.__root)

        mesh = bpy.data.meshes.new(name=pmxModel.name)
        self.__meshObj = bpy.data.objects.new(name=pmxModel.name+'_mesh', object_data=mesh)
        self.__targetScene.objects.link(self.__meshObj)
    
        self.__armObj = self.__rig.armature()
        self.__armObj.hide = True
        self.__meshObj.parent = self.__armObj

        # arm = bpy.data.armatures.new(name=pmxModel.name)
        # self.__armObj = bpy.data.objects.new(name=pmxModel.name+'_arm', object_data=arm)
        # self.__meshObj.parent = self.__armObj

        # self.__targetScene.objects.link(self.__meshObj)
        # self.__targetScene.objects.link(self.__armObj)

        # self.__armObj.parent = self.__root

        # self.__rigidsSetObj = rigging.getRigidGroupObject(self.__root)
        # self.__jointsSetObj = rigging.getJointGroupObject(self.__root)

        # self.__allObjGroup.objects.link(self.__root)
        # self.__allObjGroup.objects.link(self.__armObj)
        # self.__allObjGroup.objects.link(self.__meshObj)
        # self.__mainObjGroup.objects.link(self.__armObj)
        # self.__mainObjGroup.objects.link(self.__meshObj)

    def __createGroups(self):
        pmxModel = self.__model
        self.__mainObjGroup = bpy.data.groups.new(name='mmd_tools.' + pmxModel.name)
        logging.debug('Create main group: %s', self.__mainObjGroup.name)
        self.__allObjGroup = bpy.data.groups.new(name='mmd_tools.' + pmxModel.name + '_all')
        logging.debug('Create all group: %s', self.__allObjGroup.name)
        self.__rigidObjGroup = bpy.data.groups.new(name='mmd_tools.' + pmxModel.name + '_rigids')
        logging.debug('Create rigid group: %s', self.__rigidObjGroup.name)
        self.__jointObjGroup = bpy.data.groups.new(name='mmd_tools.' + pmxModel.name + '_joints')
        logging.debug('Create joint group: %s', self.__jointObjGroup.name)
        self.__tempObjGroup = bpy.data.groups.new(name='mmd_tools.' + pmxModel.name + '_temp')
        logging.debug('Create temporary group: %s', self.__tempObjGroup.name)

    def __importVertexGroup(self):
        self.__vertexGroupTable = []
        for i in self.__model.bones:
            self.__vertexGroupTable.append(self.__meshObj.vertex_groups.new(name=i.name))

    def __importVertices(self):
        self.__importVertexGroup()

        pmxModel = self.__model
        mesh = self.__meshObj.data

        mesh.vertices.add(count=len(self.__model.vertices))
        for i, pv in enumerate(pmxModel.vertices):
            bv = mesh.vertices[i]

            bv.co = mathutils.Vector(pv.co) * self.TO_BLE_MATRIX * self.__scale
            bv.normal = pv.normal

            if isinstance(pv.weight.weights, pmx.BoneWeightSDEF):
                self.__vertexGroupTable[pv.weight.bones[0]].add(index=[i], weight=pv.weight.weights.weight, type='REPLACE')
                self.__vertexGroupTable[pv.weight.bones[1]].add(index=[i], weight=1.0-pv.weight.weights.weight, type='REPLACE')
            elif len(pv.weight.bones) == 1:
                self.__vertexGroupTable[pv.weight.bones[0]].add(index=[i], weight=1.0, type='REPLACE')
            elif len(pv.weight.bones) == 2:
                self.__vertexGroupTable[pv.weight.bones[0]].add(index=[i], weight=pv.weight.weights[0], type='REPLACE')
                self.__vertexGroupTable[pv.weight.bones[1]].add(index=[i], weight=1.0-pv.weight.weights[0], type='REPLACE')
            elif len(pv.weight.bones) == 4:
                self.__vertexGroupTable[pv.weight.bones[0]].add(index=[i], weight=pv.weight.weights[0], type='REPLACE')
                self.__vertexGroupTable[pv.weight.bones[1]].add(index=[i], weight=pv.weight.weights[1], type='REPLACE')
                self.__vertexGroupTable[pv.weight.bones[2]].add(index=[i], weight=pv.weight.weights[2], type='REPLACE')
                self.__vertexGroupTable[pv.weight.bones[3]].add(index=[i], weight=pv.weight.weights[3], type='REPLACE')
            else:
                raise Exception('unkown bone weight type.')

    def __importTextures(self):
        pmxModel = self.__model

        self.__textureTable = []
        for i in pmxModel.textures:
            name = os.path.basename(i.path).split('.')[0]
            tex = bpy.data.textures.new(name=name, type='IMAGE')
            try:
                tex.image = bpy.data.images.load(filepath=i.path)
            except Exception:
                logging.warning('failed to load %s', str(i.path))
            self.__textureTable.append(tex)

    def __createEditBones(self, obj, pmx_bones):
        """ create EditBones from pmx file data.
        @return the list of bone names which can be accessed by the bone index of pmx data.
        """
        editBoneTable = []
        nameTable = []
        dependency_cycle_ik_bones = []
        for i, p_bone in enumerate(pmx_bones):
            if p_bone.isIK:
                if p_bone.target != -1:
                    t = pmx_bones[p_bone.target]
                    if p_bone.parent == t.parent:
                        dependency_cycle_ik_bones.append(i)

        with bpyutils.edit_object(obj) as data:
            for i in pmx_bones:
                bone = data.edit_bones.new(name=i.name)
                loc = mathutils.Vector(i.location) * self.__scale * self.TO_BLE_MATRIX
                bone.head = loc
                editBoneTable.append(bone)
                nameTable.append(bone.name)

            for i, (b_bone, m_bone) in enumerate(zip(editBoneTable, pmx_bones)):
                if m_bone.parent != -1:
                    if i not in dependency_cycle_ik_bones:
                        b_bone.parent = editBoneTable[m_bone.parent]
                    else:
                        b_bone.parent = editBoneTable[m_bone.parent].parent

            for b_bone, m_bone in zip(editBoneTable, pmx_bones):
                if isinstance(m_bone.displayConnection, int):
                    if m_bone.displayConnection != -1:
                        b_bone.tail = editBoneTable[m_bone.displayConnection].head
                    else:
                        b_bone.tail = b_bone.head
                else:
                    loc = mathutils.Vector(m_bone.displayConnection) * self.TO_BLE_MATRIX * self.__scale
                    b_bone.tail = b_bone.head + loc

            for b_bone in editBoneTable:
                # Set the length of too short bones to 1 because Blender delete them.
                if b_bone.length  < 0.001:
                    loc = mathutils.Vector([0, 0, 1]) * self.__scale
                    b_bone.tail = b_bone.head + loc

            for b_bone, m_bone in zip(editBoneTable, pmx_bones):
                if b_bone.parent is not None and b_bone.parent.tail == b_bone.head:
                    if not m_bone.isMovable:
                        b_bone.use_connect = True

        return nameTable

    def __sortPoseBonesByBoneIndex(self, pose_bones, bone_names):
        r = []
        for i in bone_names:
            r.append(pose_bones[i])
        return r

    def __applyIk(self, index, pmx_bone, pose_bones):
        """ create a IK bone constraint
         If the IK bone and the target bone is separated, a dummy IK target bone is created as a child of the IK bone.
         @param index the bone index
         @param pmx_bone pmx.Bone
         @param pose_bones the list of PoseBones sorted by the bone index
        """

        ik_bone = pose_bones[pmx_bone.target].parent
        target_bone = pose_bones[index]

        if (mathutils.Vector(ik_bone.tail) - mathutils.Vector(target_bone.head)).length > 0.001:
            logging.info('Found a seperated IK constraint: IK: %s, Target: %s', ik_bone.name, target_bone.name)
            with bpyutils.edit_object(self.__armObj) as data:
                s_bone = data.edit_bones.new(name='shadow')
                logging.info('  Create a proxy bone: %s', s_bone.name)
                s_bone.head = ik_bone.tail
                s_bone.tail = s_bone.head + mathutils.Vector([0, 0, 1])
                s_bone.layers = (False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)
                s_bone.parent = data.edit_bones[target_bone.name]
                logging.info('  Set parent: %s -> %s', target_bone.name, s_bone.name)
                # Must not access to EditBones from outside of the 'with' section.
                s_bone_name = s_bone.name

            logging.info('  Use %s as IK target bone instead of %s', s_bone_name, target_bone.name)
            target_bone = self.__armObj.pose.bones[s_bone_name]
            target_bone.is_mmd_shadow_bone = True
            target_bone.mmd_shadow_bone_type = 'IK_PROXY'

        ikConst = ik_bone.constraints.new('IK')
        ikConst.chain_count = len(pmx_bone.ik_links)
        ikConst.target = self.__armObj
        ikConst.subtarget = target_bone.name
        if pmx_bone.isRotatable and not pmx_bone.isMovable :
            ikConst.use_location = pmx_bone.isMovable
            ikConst.use_rotation = pmx_bone.isRotatable
        for i in pmx_bone.ik_links:
            if i.maximumAngle is not None:
                bone = pose_bones[i.target]
                bone.use_ik_limit_x = True
                bone.use_ik_limit_y = True
                bone.use_ik_limit_z = True
                bone.ik_max_x = -i.minimumAngle[0]
                bone.ik_max_y = i.maximumAngle[1]
                bone.ik_max_z = i.maximumAngle[2]
                bone.ik_min_x = -i.maximumAngle[0]
                bone.ik_min_y = i.minimumAngle[1]
                bone.ik_min_z = i.minimumAngle[2]

    @staticmethod
    def __findNoneAdditionalBone(target, pose_bones, visited_bones=None):
        if visited_bones is None:
            visited_bones = []
        if target in visited_bones:
            raise ValueError('Detected cyclic dependency.')
        for i in filter(lambda x: x.type == 'CHILD_OF', target.constraints):
            if i.subtarget != target.parent.name:
                return PMXImporter.__findNoneAdditionalBone(pose_bones[i.subtarget], pose_bones, visited_bones)
        return target

    def __applyAdditionalTransform(self, obj, src, dest, influence, pose_bones, rotation=False, location=False):
        """ apply additional transform to the bone.
         @param obj the object of the target armature
         @param src the PoseBone that apply the transform to another bone.
         @param dest the PoseBone that another bone apply the transform to.
        """
        if not rotation and not location:
            return
        bone_name = None

        # If src has been applied the additional transform by another bone,
        # copy the constraint of it to dest.
        src = self.__findNoneAdditionalBone(src, pose_bones)

        with bpyutils.edit_object(obj) as data:
            src_bone = data.edit_bones[src.name]
            s_bone = data.edit_bones.new(name='shadow')
            s_bone.head = src_bone.head
            s_bone.tail = src_bone.tail
            s_bone.parent = src_bone.parent
            #s_bone.use_connect = src_bone.use_connect
            s_bone.layers = (False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)
            s_bone.use_inherit_rotation = False
            s_bone.use_local_location = True
            s_bone.use_inherit_scale = False
            bone_name = s_bone.name

            dest_bone = data.edit_bones[dest.name]
            dest_bone.use_inherit_rotation = not rotation
            dest_bone.use_local_location = not location

        p_bone = obj.pose.bones[bone_name]
        p_bone.is_mmd_shadow_bone = True
        p_bone.mmd_shadow_bone_type = 'ADDITIONAL_TRANSFORM'

        if rotation:
            c = p_bone.constraints.new('COPY_ROTATION')
            c.target = obj
            c.subtarget = src.name
            c.target_space = 'LOCAL'
            c.owner_space = 'LOCAL'

            if influence > 0:
                c.influence = influence
            else:
                c.influence = -influence
                c.invert_x = True
                c.invert_y = True
                c.invert_z = True

        if location:
            c = p_bone.constraints.new('COPY_LOCATION')
            c.target = obj
            c.subtarget = src.name
            c.target_space = 'LOCAL'
            c.owner_space = 'LOCAL'

            if influence > 0:
                c.influence = influence
            else:
                c.influence = -influence
                c.invert_x = True
                c.invert_y = True
                c.invert_z = True

        c = dest.constraints.new('CHILD_OF')

        c.target = obj
        c.subtarget = p_bone.name
        c.use_location_x = location
        c.use_location_y = location
        c.use_location_z = location
        c.use_rotation_x = rotation
        c.use_rotation_y = rotation
        c.use_rotation_z = rotation
        c.use_scale_x = False
        c.use_scale_y = False
        c.use_scale_z = False
        c.inverse_matrix = mathutils.Matrix(src.matrix).inverted()

        if dest.parent is not None:
            parent = dest.parent
            c = dest.constraints.new('CHILD_OF')
            c.target = obj
            c.subtarget = parent.name
            c.use_location_x = False
            c.use_location_y = False
            c.use_location_z = False
            c.use_scale_x = False
            c.use_scale_y = False
            c.use_scale_z = False
            c.inverse_matrix = mathutils.Matrix(parent.matrix).inverted()

    def __importBones(self):
        pmxModel = self.__model

        boneNameTable = self.__createEditBones(self.__armObj, pmxModel.bones)
        pose_bones = self.__sortPoseBonesByBoneIndex(self.__armObj.pose.bones, boneNameTable)
        self.__boneTable = pose_bones
        for i, p_bone in sorted(enumerate(pmxModel.bones), key=lambda x: x[1].transform_order):
            b_bone = pose_bones[i]
            b_bone.mmd_bone.name_e = p_bone.name_e
            b_bone.mmd_bone.transform_order = p_bone.transform_order
            b_bone.mmd_bone.is_visible = p_bone.visible
            b_bone.mmd_bone.is_controllable = p_bone.isControllable

            if not p_bone.isRotatable:
                b_bone.lock_rotation = [True, True, True]

            if not p_bone.isMovable:
                b_bone.lock_location = [True, True, True]

            if p_bone.isIK:
                if p_bone.target != -1:
                    self.__applyIk(i, p_bone, pose_bones)

            if p_bone.hasAdditionalRotate or p_bone.hasAdditionalLocation:
                bone_index, influ = p_bone.additionalTransform
                src_bone = pmxModel.bones[bone_index]
                self.__applyAdditionalTransform(
                    self.__armObj,
                    pose_bones[bone_index],
                    b_bone,
                    influ,
                    self.__armObj.pose.bones,
                    p_bone.hasAdditionalRotate,
                    p_bone.hasAdditionalLocation
                    )

            if p_bone.localCoordinate is not None:
                b_bone.mmd_bone.enabled_local_axes = True
                b_bone.mmd_bone.local_axis_x = p_bone.localCoordinate.x_axis
                b_bone.mmd_bone.local_axis_z = p_bone.localCoordinate.z_axis

            if len(b_bone.children) == 0:
                b_bone.mmd_bone.is_tip = True
                b_bone.lock_rotation = [True, True, True]
                b_bone.lock_location = [True, True, True]
                b_bone.lock_scale = [True, True, True]
                b_bone.bone.hide = True

    def __importRigids(self):
        self.__rigidTable = []
        start_time = time.time()
        for rigid in self.__model.rigids:
            if self.__onlyCollisions and rigid.mode != pmx.Rigid.MODE_STATIC:
                continue

            loc = mathutils.Vector(rigid.location) * self.TO_BLE_MATRIX * self.__scale
            rot = mathutils.Vector(rigid.rotation) * self.TO_BLE_MATRIX * -1
            if rigid.type == pmx.Rigid.TYPE_BOX:
                size = mathutils.Vector(rigid.size) * self.TO_BLE_MATRIX
            else:
                size = mathutils.Vector(rigid.size)

            obj = self.__rig.createRigidBody(
                name = rigid.name,
                name_e = rigid.name_e,
                shape_type = rigid.type,
                dynamics_type = rigid.mode,
                location = loc,
                rotation = rot,
                size = size * self.__scale,
                collision_group_number = rigid.collision_group_number,
                collision_group_mask = [rigid.collision_group_mask & (1<<i) == 0 for i in range(16)],
                arm_obj = self.__armObj,
                mass=rigid.mass,
                friction = rigid.friction,
                angular_damping = rigid.rotation_attenuation,
                linear_damping = rigid.velocity_attenuation,
                bounce = rigid.bounce,
                bone = None if rigid.bone == -1 or rigid.bone is None else self.__boneTable[rigid.bone].name,
                )
            obj.hide = True
            self.__rigidObjGroup.objects.link(obj)

            self.__rigidTable.append(obj)
        logging.debug('Finished importing rigid bodies in %f seconds.', time.time() - start_time)

    
    def __importJoints(self):
        if self.__onlyCollisions:
            return
        self.__jointTable = []
        for joint in self.__model.joints:
            loc = mathutils.Vector(joint.location) * self.TO_BLE_MATRIX * self.__scale
            rot = mathutils.Vector(joint.rotation) * self.TO_BLE_MATRIX * -1

            obj = self.__rig.createJoint(
                name = joint.name,
                name_e = joint.name_e,
                location = loc,
                rotation = rot,
                size = 0.5 * self.__scale,
                rigid_a = self.__rigidTable[joint.src_rigid],
                rigid_b = self.__rigidTable[joint.dest_rigid],
                maximum_location = mathutils.Vector(joint.maximum_location) * self.TO_BLE_MATRIX * self.__scale,
                minimum_location = mathutils.Vector(joint.minimum_location) * self.TO_BLE_MATRIX * self.__scale,
                maximum_rotation = mathutils.Vector(joint.maximum_rotation) * self.TO_BLE_MATRIX * -1,
                minimum_rotation = mathutils.Vector(joint.minimum_rotation) * self.TO_BLE_MATRIX * -1,
                spring_linear = mathutils.Vector(joint.spring_constant) * self.TO_BLE_MATRIX,
                spring_angular = mathutils.Vector(joint.spring_rotation_constant) * self.TO_BLE_MATRIX,
                )
            obj.hide = True
            self.__jointTable.append(obj)
            self.__jointObjGroup.objects.link(obj)


    def __importMaterials(self):
        self.__importTextures()

        pmxModel = self.__model

        self.__materialTable = []
        self.__materialFaceCountTable = []
        for i in pmxModel.materials:
            mat = bpy.data.materials.new(name=i.name)
            mmd_material = mat.mmd_material
            mat.diffuse_color = i.diffuse[0:3]
            mat.alpha = i.diffuse[3]
            mat.specular_color = i.specular[0:3]
            mat.specular_alpha = i.specular[3]

            mmd_material.name_j = i.name
            mmd_material.name_e = i.name_e
            mmd_material.ambient_color = i.ambient
            mmd_material.is_double_sided = i.is_double_sided
            mmd_material.enabled_drop_shadow = i.enabled_drop_shadow
            mmd_material.enabled_self_shadow_map = i.enabled_self_shadow_map
            mmd_material.enabled_self_shadow = i.enabled_self_shadow
            mmd_material.enabled_toon_edge = i.enabled_toon_edge
            mmd_material.edge_color = i.edge_color
            mmd_material.edge_weight = i.edge_size
            mmd_material.sphere_texture_type = str(i.sphere_texture_mode)
            mmd_material.comment = i.comment

            self.__materialFaceCountTable.append(int(i.vertex_count/3))
            self.__meshObj.data.materials.append(mat)
            if i.texture != -1:
                texture_slot = mat.texture_slots.create(0)
                texture_slot.use_map_alpha = True
                texture_slot.texture = self.__textureTable[i.texture]
                texture_slot.texture_coords = 'UV'
                mat.use_transparency = True
                mat.transparency_method = 'Z_TRANSPARENCY'
                mat.alpha = 0
            if not i.is_shared_toon_texture and i.toon_texture != -1:
                texture_slot = mat.texture_slots.create(1)
                texture_slot.use_map_alpha = True
                texture_slot.texture = self.__textureTable[i.toon_texture]
                texture_slot.texture_coords = 'UV'
                mat.use_textures[1] = False
                mat.use_transparency = True
                mat.transparency_method = 'Z_TRANSPARENCY'
                mat.alpha = 0
            if i.sphere_texture != -1:
                texture_slot = mat.texture_slots.create(2)
                texture_slot.use_map_alpha = True
                texture_slot.texture = self.__textureTable[i.sphere_texture]
                texture_slot.texture_coords = 'UV'
                mat.use_textures[2] = False
                mat.use_transparency = True
                mat.transparency_method = 'Z_TRANSPARENCY'
                mat.alpha = 0

    def __importFaces(self):
        pmxModel = self.__model
        mesh = self.__meshObj.data

        mesh.tessfaces.add(len(pmxModel.faces))
        uvLayer = mesh.tessface_uv_textures.new()
        for i, f in enumerate(pmxModel.faces):
            bf = mesh.tessfaces[i]
            bf.vertices_raw = list(f) + [0]
            bf.use_smooth = True
            face_count = 0
            uv = uvLayer.data[i]
            uv.uv1 = self.flipUV_V(pmxModel.vertices[f[0]].uv)
            uv.uv2 = self.flipUV_V(pmxModel.vertices[f[1]].uv)
            uv.uv3 = self.flipUV_V(pmxModel.vertices[f[2]].uv)

            bf.material_index = self.__getMaterialIndexFromFaceIndex(i)

    def __importVertexMorphs(self):
        pmxModel = self.__model

        utils.selectAObject(self.__meshObj)
        bpy.ops.object.shape_key_add()

        for morph in filter(lambda x: isinstance(x, pmx.VertexMorph), pmxModel.morphs):
            shapeKey = self.__meshObj.shape_key_add(morph.name)
            for md in morph.offsets:
                shapeKeyPoint = shapeKey.data[md.index]
                offset = mathutils.Vector(md.offset) * self.TO_BLE_MATRIX
                shapeKeyPoint.co = shapeKeyPoint.co + offset * self.__scale

    def __addArmatureModifier(self, meshObj, armObj):
        armModifier = meshObj.modifiers.new(name='Armature', type='ARMATURE')
        armModifier.object = armObj
        armModifier.use_vertex_groups = True

    def __renameLRBones(self):
        pose_bones = self.__armObj.pose.bones
        for i in pose_bones:
            if i.is_mmd_shadow_bone:
                continue
            i.mmd_bone.name_j = i.name
            i.name = utils.convertNameToLR(i.name)
            self.__meshObj.vertex_groups[i.mmd_bone.name_j].name = i.name

    def execute(self, **args):
        if 'pmx' in args:
            self.__model = args['pmx']
        else:
            self.__model = pmx.load(args['filepath'])

        self.__scale = args.get('scale', 1.0)
        renameLRBones = args.get('rename_LR_bones', False)
        self.__onlyCollisions = args.get('only_collisions', False)
        self.__ignoreNonCollisionGroups = args.get('ignore_non_collision_groups', True)
        self.__distance_of_ignore_collisions = args.get('distance_of_ignore_collisions', 1) # 衝突を考慮しない距離（非衝突グループ設定を無視する距離）
        self.__distance_of_ignore_collisions /= 2

        logging.info('****************************************')
        logging.info(' mmd_tools.import_pmx module')
        logging.info('----------------------------------------')
        logging.info(' Start to load model data form a pmx file')
        logging.info('            by the mmd_tools.pmx modlue.')
        logging.info('')

        start_time = time.time()

        self.__createGroups()
        self.__createObjects()

        self.__importVertices()
        self.__importBones()
        self.__importMaterials()
        self.__importFaces()
        self.__importRigids()
        self.__importJoints()

        self.__importVertexMorphs()

        if renameLRBones:
            self.__renameLRBones()

        self.__addArmatureModifier(self.__meshObj, self.__armObj)
        self.__meshObj.data.update()

        bpy.types.Object.pmx_import_scale = bpy.props.FloatProperty(name='pmx_import_scale')
        self.__armObj.pmx_import_scale = self.__scale

        for i in [self.__rigidObjGroup.objects, self.__jointObjGroup.objects, self.__tempObjGroup.objects]:
            for j in i:
                self.__allObjGroup.objects.link(j)

        bpy.context.scene.gravity[2] = -9.81 * 10 * self.__scale
        self.__rig.rootObject().mmd_root.show_meshes = True

        logging.info(' Finished importing the model in %f seconds.', time.time() - start_time)
        logging.info('----------------------------------------')
        logging.info(' mmd_tools.import_pmx module')
        logging.info('****************************************')
