# -*- coding: utf-8 -*-
from . import pmx
from . import utils
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

        self.__vertexTable = None
        self.__vertexGroupTable = None
        self.__textureTable = None

        self.__mutedIkConsts = []
        self.__boneTable = []
        self.__rigidTable = []
        self.__nonCollisionJointTable = None
        self.__jointTable = []

        self.__materialFaceCountTable = None

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

        self.__root = bpy.data.objects.new(name=pmxModel.name, object_data=None)
        self.__targetScene.objects.link(self.__root)

        mesh = bpy.data.meshes.new(name=pmxModel.name)
        self.__meshObj = bpy.data.objects.new(name=pmxModel.name+'_mesh', object_data=mesh)

        arm = bpy.data.armatures.new(name=pmxModel.name)
        self.__armObj = bpy.data.objects.new(name=pmxModel.name+'_arm', object_data=arm)
        self.__meshObj.parent = self.__armObj

        self.__targetScene.objects.link(self.__meshObj)
        self.__targetScene.objects.link(self.__armObj)

        self.__armObj.parent = self.__root

        self.__allObjGroup.objects.link(self.__root)
        self.__allObjGroup.objects.link(self.__armObj)
        self.__allObjGroup.objects.link(self.__meshObj)
        self.__mainObjGroup.objects.link(self.__armObj)
        self.__mainObjGroup.objects.link(self.__meshObj)

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
            name = os.path.basename(i.path.replace('\\', os.path.sep)).split('.')[0]
            tex = bpy.data.textures.new(name=name, type='IMAGE')
            try:
                tex.image = bpy.data.images.load(filepath=bpy.path.resolve_ncase(path=i.path))
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

        with bpyutils.edit_object(obj):
            for i in pmx_bones:
                bone = obj.data.edit_bones.new(name=i.name)
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
            with bpyutils.edit_object(self.__armObj):
                s_bone = self.__armObj.data.edit_bones.new(name='shadow')
                logging.info('  Create a proxy bone: %s', s_bone.name)
                s_bone.head = ik_bone.tail
                s_bone.tail = s_bone.head + mathutils.Vector([0, 0, 1])
                s_bone.layers = (False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)
                s_bone.parent = self.__armObj.data.edit_bones[target_bone.name]
                logging.info('  Set parent: %s -> %s', target_bone.name, s_bone.name)
                # Must not access to EditBones from outside of the 'with' section.
                s_bone_name = s_bone.name

            logging.info('  Use %s as IK target bone instead of %s', s_bone_name, target_bone.name)
            target_bone = self.__armObj.pose.bones[s_bone_name]
            target_bone.is_mmd_shadow_bone = True

        ikConst = ik_bone.constraints.new('IK')
        ikConst.mute = True
        self.__mutedIkConsts.append(ikConst)
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

        with bpyutils.edit_object(obj):
            src_bone = obj.data.edit_bones[src.name]
            s_bone = obj.data.edit_bones.new(name='shadow')
            s_bone.head = src_bone.head
            s_bone.tail = src_bone.tail
            s_bone.parent = src_bone.parent
            #s_bone.use_connect = src_bone.use_connect
            s_bone.layers = (False, False, False, False, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)
            s_bone.use_inherit_rotation = False
            s_bone.use_local_location = True
            s_bone.use_inherit_scale = False
            bone_name = s_bone.name

            dest_bone = obj.data.edit_bones[dest.name]
            dest_bone.use_inherit_rotation = not rotation
            dest_bone.use_local_location = not location

        p_bone = obj.pose.bones[bone_name]
        p_bone.is_mmd_shadow_bone = True

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
            b_bone.mmd_bone_name_e = p_bone.name_e

            if not p_bone.isRotatable:
                b_bone.lock_rotation = [True, True, True]

            if not p_bone.isMovable:
                b_bone.lock_location =[True, True, True]

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
                b_bone.mmd_enabled_local_axis = True
                b_bone.mmd_local_axis_x = p_bone.localCoordinate.x_axis
                b_bone.mmd_local_axis_z = p_bone.localCoordinate.z_axis

            if len(b_bone.children) == 0:
                b_bone.is_mmd_tip_bone = True
                b_bone.lock_rotation = [True, True, True]
                b_bone.lock_location = [True, True, True]
                b_bone.lock_scale = [True, True, True]
                b_bone.bone.hide = True

    def __importRigids(self):
        self.__rigidTable = []
        self.__nonCollisionJointTable = []
        start_time = time.time()
        collisionGroups = []
        for i in range(16):
            collisionGroups.append([])
        imported_rigids = []
        for rigid in self.__model.rigids:
            if self.__onlyCollisions and rigid.mode != pmx.Rigid.MODE_STATIC:
                continue

            loc = mathutils.Vector(rigid.location) * self.TO_BLE_MATRIX * self.__scale
            rot = mathutils.Vector(rigid.rotation) * self.TO_BLE_MATRIX * -1
            rigid_type = None
            if rigid.type == pmx.Rigid.TYPE_SPHERE:
                bpy.ops.mesh.primitive_uv_sphere_add(
                    segments=16,
                    ring_count=8,
                    size=1,
                    view_align=False,
                    enter_editmode=False
                    )
                size = mathutils.Vector([1,1,1]) * rigid.size[0]
                rigid_type = 'SPHERE'
                bpy.ops.object.shade_smooth()
            elif rigid.type == pmx.Rigid.TYPE_BOX:
                bpy.ops.mesh.primitive_cube_add(
                    view_align=False,
                    enter_editmode=False
                    )
                size = mathutils.Vector(rigid.size) * self.TO_BLE_MATRIX
                rigid_type = 'BOX'
            elif rigid.type == pmx.Rigid.TYPE_CAPSULE:
                obj = utils.makeCapsule(radius=rigid.size[0], height=rigid.size[1])
                size = mathutils.Vector([1,1,1])
                rigid_type = 'CAPSULE'
                bpy.ops.object.shade_smooth()
            else:
                raise Exception('Invalid rigid type')

            if rigid.type != pmx.Rigid.TYPE_CAPSULE:
                obj = bpy.context.selected_objects[0]
            obj.name = rigid.name
            obj.scale = size * self.__scale
            obj.hide_render = True
            obj.draw_type = 'WIRE'
            obj.is_mmd_rigid = True
            self.__rigidObjGroup.objects.link(obj)
            utils.selectAObject(obj)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            obj.location = loc
            obj.rotation_euler = rot
            bpy.ops.rigidbody.object_add(type='ACTIVE')
            if rigid.mode == pmx.Rigid.MODE_STATIC and rigid.bone is not None:
                bpy.ops.object.modifier_add(type='COLLISION')
                utils.setParentToBone(obj, self.__armObj, self.__boneTable[rigid.bone].name)
            elif rigid.bone is not None:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select = True
                bpy.context.scene.objects.active = self.__root
                bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

                target_bone = self.__boneTable[rigid.bone]
                empty = bpy.data.objects.new(
                    'mmd_bonetrack',
                    None)
                bpy.context.scene.objects.link(empty)
                empty.location = target_bone.tail
                empty.empty_draw_size = 0.5 * self.__scale
                empty.empty_draw_type = 'ARROWS'
                empty.is_mmd_rigid_track_target = True
                self.__tempObjGroup.objects.link(empty)

                utils.selectAObject(empty)
                bpy.context.scene.objects.active = obj
                bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=False)

                empty.hide = True


                for i in target_bone.constraints:
                    if i.type == 'IK':
                        self.__mutedIkConsts.remove(i)
                const = target_bone.constraints.new('DAMPED_TRACK')
                const.target = empty
            else:
                obj.parent = self.__armObj
                bpy.ops.object.select_all(action='DESELECT')
                obj.select = True

            obj.rigid_body.collision_shape = rigid_type
            group_flags = []
            rb = obj.rigid_body
            rb.friction = rigid.friction
            rb.mass = rigid.mass
            rb.angular_damping = rigid.rotation_attenuation
            rb.linear_damping = rigid.velocity_attenuation
            rb.restitution = rigid.bounce
            if rigid.mode == pmx.Rigid.MODE_STATIC:
                rb.kinematic = True

            imported_rigids.append(rigid)
            collisionGroups[rigid.collision_group_number].append(obj)
            self.__rigidTable.append(obj)

        for rigid, obj in zip(imported_rigids, self.__rigidTable):
            for i in range(16):
                if rigid.collision_group_mask & (1<<i) == 0:
                    for j in collisionGroups[i]:
                        self.__makeNonCollisionConstraint(obj, j)

        for c in self.__mutedIkConsts:
            c.mute = False

        logging.debug('Finished importing rigid bodies in %f seconds.', time.time() - start_time)


    def __getRigidRange(self, obj):
        return (mathutils.Vector(obj.bound_box[0]) - mathutils.Vector(obj.bound_box[6])).length

    def __makeNonCollisionConstraint(self, obj_a, obj_b):
        if obj_a == obj_b:
            return
        pair = frozenset((obj_a, obj_b))
        if pair in self.__nonCollisionJointTable:
            return
        if (mathutils.Vector(obj_a.location) - mathutils.Vector(obj_b.location)).length > self.__distance_of_ignore_collisions * (self.__getRigidRange(obj_a) + self.__getRigidRange(obj_b)):
            return

        self.__nonCollisionJointTable.append(pair)


    def __createNonCollisionConstraint(self):
        total_len = len(self.__nonCollisionJointTable)
        if total_len < 1:
            return

        start_time = time.time()
        logging.debug('-'*60)
        logging.debug(' creating ncc, counts: %d', total_len)

        ncc_root = bpy.data.objects.new(name='ncc_root', object_data=None)
        self.__targetScene.objects.link(ncc_root)
        ncc_root.parent = self.__root
        self.__tempObjGroup.objects.link(ncc_root)

        ncc_obj = bpy.data.objects.new('ncc', None)
        bpy.context.scene.objects.link(ncc_obj)
        ncc_obj.location = [0, 0, 0]
        ncc_obj.empty_draw_size = 0.5 * self.__scale
        ncc_obj.empty_draw_type = 'ARROWS'
        ncc_obj.is_mmd_non_collision_constraint = True
        ncc_obj.hide_render = True
        ncc_obj.parent = ncc_root
        utils.selectAObject(ncc_obj)
        bpy.ops.rigidbody.constraint_add(type='GENERIC')
        rb = ncc_obj.rigid_body_constraint
        rb.disable_collisions = True
        self.__tempObjGroup.objects.link(ncc_obj)

        last_selected = [ncc_obj]
        while len(ncc_root.children) < total_len:
            bpy.ops.object.duplicate()
            remain = total_len - len(ncc_root.children) - len(bpy.context.selected_objects)
            if remain < 0:
                last_selected = bpy.context.selected_objects
                for i in range(-remain):
                    last_selected[i].select = False
            else:
                for i in range(min(remain, len(last_selected))):
                    last_selected[i].select = True
            last_selected = bpy.context.selected_objects
        logging.debug(' created %d ncc.', len(ncc_root.children))

        for ncc_obj, pair in zip(ncc_root.children, self.__nonCollisionJointTable):
            rbc = ncc_obj.rigid_body_constraint
            rbc.object1, rbc.object2 = pair
            ncc_obj.hide = True

        ncc_root.hide_render = True
        ncc_root.hide = True
        logging.debug(' finish in %f seconds.', time.time() - start_time)
        logging.debug('-'*60)

    def __makeSpring(self, target, base_obj, spring_stiffness):
        utils.selectAObject(target)
        bpy.ops.object.duplicate()
        spring_target = bpy.context.scene.objects.active
        spring_target.is_mmd_spring_goal = True
        spring_target.rigid_body.kinematic = True
        spring_target.rigid_body.collision_groups = (False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True)
        bpy.context.scene.objects.active = base_obj
        bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)
        self.__rigidObjGroup.objects.unlink(spring_target)
        self.__tempObjGroup.objects.link(spring_target)

        obj = bpy.data.objects.new(
            'S.'+target.name,
            None)
        bpy.context.scene.objects.link(obj)
        obj.location = target.location
        obj.empty_draw_size = 0.5 * self.__scale
        obj.empty_draw_type = 'ARROWS'
        obj.hide_render = True
        obj.is_mmd_spring_joint = True
        obj.parent = self.__root
        self.__tempObjGroup.objects.link(obj)
        utils.selectAObject(obj)
        bpy.ops.rigidbody.constraint_add(type='GENERIC_SPRING')
        rbc = obj.rigid_body_constraint
        rbc.object1 = target
        rbc.object2 = spring_target

        rbc.use_spring_x = True
        rbc.use_spring_y = True
        rbc.use_spring_z = True

        rbc.spring_stiffness_x = spring_stiffness[0]
        rbc.spring_stiffness_y = spring_stiffness[1]
        rbc.spring_stiffness_z = spring_stiffness[2]

    def __importJoints(self):
        if self.__onlyCollisions:
            self.__createNonCollisionConstraint()
            return
        self.__jointTable = []
        for joint in self.__model.joints:
            loc = mathutils.Vector(joint.location) * self.TO_BLE_MATRIX * self.__scale
            rot = mathutils.Vector(joint.rotation) * self.TO_BLE_MATRIX * -1
            obj = bpy.data.objects.new(
                'J.'+joint.name,
                None)
            bpy.context.scene.objects.link(obj)
            obj.location = loc
            obj.rotation_euler = rot
            obj.empty_draw_size = 0.5 * self.__scale
            obj.empty_draw_type = 'ARROWS'
            obj.hide_render = True
            obj.is_mmd_joint = True
            obj.parent = self.__root
            self.__jointObjGroup.objects.link(obj)

            utils.selectAObject(obj)
            bpy.ops.rigidbody.constraint_add(type='GENERIC_SPRING')
            rbc = obj.rigid_body_constraint

            rigid1 = self.__rigidTable[joint.src_rigid]
            rigid2 = self.__rigidTable[joint.dest_rigid]
            rbc.object1 = rigid1
            rbc.object2 = rigid2

            if not self.__ignoreNonCollisionGroups:
                non_collision_joint = frozenset((rigid1, rigid2))
                if non_collision_joint not in self.__nonCollisionJointTable:
                    rbc.disable_collisions = False
                else:
                    self.__nonCollisionJointTable.remove(non_collision_joint)
                    rbc.disable_collisions = True
            elif rigid1.rigid_body.kinematic and not rigid2.rigid_body.kinematic or not rigid1.rigid_body.kinematic and rigid2.rigid_body.kinematic:
                rbc.disable_collisions = False

            rbc.use_limit_ang_x = True
            rbc.use_limit_ang_y = True
            rbc.use_limit_ang_z = True
            rbc.use_limit_lin_x = True
            rbc.use_limit_lin_y = True
            rbc.use_limit_lin_z = True
            rbc.use_spring_x = True
            rbc.use_spring_y = True
            rbc.use_spring_z = True

            max_loc = mathutils.Vector(joint.maximum_location) * self.TO_BLE_MATRIX * self.__scale
            min_loc = mathutils.Vector(joint.minimum_location) * self.TO_BLE_MATRIX * self.__scale
            rbc.limit_lin_x_upper = max_loc[0]
            rbc.limit_lin_y_upper = max_loc[1]
            rbc.limit_lin_z_upper = max_loc[2]

            rbc.limit_lin_x_lower = min_loc[0]
            rbc.limit_lin_y_lower = min_loc[1]
            rbc.limit_lin_z_lower = min_loc[2]

            max_rot = mathutils.Vector(joint.maximum_rotation) * self.TO_BLE_MATRIX
            min_rot = mathutils.Vector(joint.minimum_rotation) * self.TO_BLE_MATRIX
            rbc.limit_ang_x_upper = -min_rot[0]
            rbc.limit_ang_y_upper = -min_rot[1]
            rbc.limit_ang_z_upper = -min_rot[2]

            rbc.limit_ang_x_lower = -max_rot[0]
            rbc.limit_ang_y_lower = -max_rot[1]
            rbc.limit_ang_z_lower = -max_rot[2]

            # spring_damp = mathutils.Vector(joint.spring_constant) * self.TO_BLE_MATRIX
            # rbc.spring_damping_x = spring_damp[0]
            # rbc.spring_damping_y = spring_damp[1]
            # rbc.spring_damping_z = spring_damp[2]

            self.__jointTable.append(obj)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select = True
            bpy.context.scene.objects.active = self.__armObj
            bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

            # spring_stiff = mathutils.Vector()
            # rbc.spring_stiffness_x = spring_stiff[0]
            # rbc.spring_stiffness_y = spring_stiff[1]
            # rbc.spring_stiffness_z = spring_stiff[2]

            if rigid1.rigid_body.kinematic:
                self.__makeSpring(rigid2, rigid1, mathutils.Vector(joint.spring_rotation_constant) * self.TO_BLE_MATRIX)
            if rigid2.rigid_body.kinematic:
                self.__makeSpring(rigid1, rigid2, mathutils.Vector(joint.spring_rotation_constant) * self.TO_BLE_MATRIX)

        self.__createNonCollisionConstraint()




    def __importMaterials(self):
        self.__importTextures()

        pmxModel = self.__model

        self.__materialTable = []
        self.__materialFaceCountTable = []
        for i in pmxModel.materials:
            mat = bpy.data.materials.new(name=i.name)
            mat.diffuse_color = i.diffuse[0:3]
            mat.alpha = i.diffuse[3]
            mat.ambient_color = i.ambient
            mat.specular_color = i.specular[0:3]
            mat.specular_alpha = i.specular[3]
            mat.use_shadows = i.enabled_self_shadow
            mat.use_transparent_shadows = i.enabled_self_shadow
            mat.use_cast_buffer_shadows = i.enabled_self_shadow_map # only buffer shadows
            if hasattr(mat, 'use_cast_shadows'):
                # "use_cast_shadows" is not supported in older Blender (< 2.71),
                # so we still use "use_cast_buffer_shadows".
                mat.use_cast_shadows = i.enabled_self_shadow_map
            if mat.alpha < 1.0 or mat.specular_alpha < 1.0 or i.texture != -1:
                mat.use_transparency = True
                mat.transparency_method = 'Z_TRANSPARENCY'
            self.__materialFaceCountTable.append(int(i.vertex_count/3))
            self.__meshObj.data.materials.append(mat)
            if i.texture != -1:
                texture_slot = mat.texture_slots.add()
                texture_slot.use_map_alpha = True
                texture_slot.texture = self.__textureTable[i.texture]
                texture_slot.texture.use_mipmap = self.__use_mipmap
                texture_slot.texture_coords = 'UV'
                texture_slot.blend_type = 'MULTIPLY'
            if i.sphere_texture_mode == 2:
                amount = self.__spa_blend_factor
                blend = 'ADD'
            else:
                amount = self.__sph_blend_factor
                blend = 'MULTIPLY'
            if i.sphere_texture != -1 and amount != 0.0:
                texture_slot = mat.texture_slots.add()
                texture_slot.texture = self.__textureTable[i.sphere_texture]
                if isinstance(texture_slot.texture.image, bpy.types.Image):
                    texture_slot.texture.image.use_alpha = False
                texture_slot.texture_coords = 'NORMAL'
                texture_slot.diffuse_color_factor = amount
                texture_slot.blend_type = blend

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

    def __hideRigidsAndJoints(self, obj):
        if obj.is_mmd_rigid or obj.is_mmd_joint or obj.is_mmd_non_collision_constraint or obj.is_mmd_spring_joint or obj.is_mmd_spring_goal:
            obj.hide = True

        for i in obj.children:
            self.__hideRigidsAndJoints(i)

    def __hideObjectsByDefault(self):
        utils.selectAObject(self.__root)
        bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')
        self.__root.select = False
        self.__armObj.select = False
        self.__meshObj.select = False
        bpy.ops.object.hide_view_set()

    def __addArmatureModifier(self, meshObj, armObj):
        armModifier = meshObj.modifiers.new(name='Armature', type='ARMATURE')
        armModifier.object = armObj
        armModifier.use_vertex_groups = True

    def __renameLRBones(self):
        pose_bones = self.__armObj.pose.bones
        for i in pose_bones:
            if i.is_mmd_shadow_bone:
                continue
            i.mmd_bone_name_j = i.name
            i.name = utils.convertNameToLR(i.name)
            self.__meshObj.vertex_groups[i.mmd_bone_name_j].name = i.name

    def execute(self, **args):
        if 'pmx' in args:
            self.__model = args['pmx']
        else:
            self.__model = pmx.load(args['filepath'])

        self.__scale = args.get('scale', 1.0)
        self.__onlyCollisions = args.get('only_collisions', False)
        self.__ignoreNonCollisionGroups = args.get('ignore_non_collision_groups', True)
        self.__distance_of_ignore_collisions = args.get('distance_of_ignore_collisions', 1) # 衝突を考慮しない距離（非衝突グループ設定を無視する距離）
        self.__distance_of_ignore_collisions /= 2
        self.__use_mipmap = args.get('use_mipmap', True)
        self.__sph_blend_factor = args.get('sph_blend_factor', 1.0)
        self.__spa_blend_factor = args.get('spa_blend_factor', 1.0)

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

        if args.get('rename_LR_bones', False):
            self.__renameLRBones()

        self.__addArmatureModifier(self.__meshObj, self.__armObj)
        self.__meshObj.data.update()

        if args.get('hide_rigids', False):
            self.__hideObjectsByDefault()
        self.__armObj.pmx_import_scale = self.__scale

        for i in [self.__rigidObjGroup.objects, self.__jointObjGroup.objects, self.__tempObjGroup.objects]:
            for j in i:
                self.__allObjGroup.objects.link(j)

        bpy.context.scene.gravity[2] = -9.81 * 10 * self.__scale

        logging.info(' Finished importing the model in %f seconds.', time.time() - start_time)
        logging.info('----------------------------------------')
        logging.info(' mmd_tools.import_pmx module')
        logging.info('****************************************')
