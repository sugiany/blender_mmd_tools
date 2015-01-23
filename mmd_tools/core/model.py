# -*- coding: utf-8 -*-

import bpy
from bpy.types import Operator
import mathutils

from mmd_tools import bpyutils
from mmd_tools.core import rigid_body
from mmd_tools.core.bone import FnBone

import logging
import time


def isRigidBodyObject(obj):
    return obj.mmd_type == 'RIGID_BODY'

def isJointObject(obj):
    return obj.mmd_type == 'JOINT'

def isTemporaryObject(obj):
    return obj.mmd_type in ['TRACK_TARGET', 'NON_COLLISION_CONSTRAINT', 'SPRING_CONSTRAINT', 'SPRING_GOAL']


def getRigidBodySize(obj):
    if not isRigidBodyObject(obj):
        raise ValueError

    if obj.mmd_rigid.shape == 'SPHERE':
        max_z = 0
        for v in obj.data.vertices:
            vc = v.co
            if vc.z > max_z:
                max_z = vc.z
        return (max_z, 0.0, 0.0)
    elif obj.mmd_rigid.shape == 'BOX':
        v = obj.data.vertices[0].co
        x, y, z = map(abs, v)
        return (x, y, z)
    elif obj.mmd_rigid.shape == 'CAPSULE':
        max_z = 0
        max_x = 0
        for v in obj.data.vertices:
            vc = v.co
            if vc.z > max_z:
                max_z = vc.z
            if vc.x > max_x:
                max_x = vc.x
        radius = max_x
        height = (max_z - radius) * 2
        return (radius, height, 0.0)
    else:
        raise Exception('Invalid shape type.')

class InvalidRigidSettingException(ValueError):
    pass

class Model:
    def __init__(self, root_obj):
        if root_obj.mmd_type != 'ROOT':
            raise ValueError('must be MMD ROOT type object')
        self.__root = root_obj
        self.__arm = None
        self.__rigid_grp = None
        self.__joint_grp = None
        self.__temporary_grp = None

    @staticmethod
    def create(name, name_e='', scale=1):
        scene = bpy.context.scene

        root = bpy.data.objects.new(name=name, object_data=None)
        root.mmd_type = 'ROOT'
        root.mmd_root.name = name
        root.mmd_root.name_e = name_e
        root.mmd_root.scale = scale
        root.lock_location = [True, True, True]
        root.lock_rotation = [True, True, True]
        root.lock_scale = [True, True, True]

        arm = bpy.data.armatures.new(name=name)
        armObj = bpy.data.objects.new(name=name+'_arm', object_data=arm)
        armObj.parent = root

        scene.objects.link(root)
        scene.objects.link(armObj)

        return Model(root)

    @classmethod
    def findRoot(cls, obj):
        if obj.mmd_type == 'ROOT':
            return obj
        elif obj.parent is not None:
            return cls.findRoot(obj.parent)
        else:
            return None

    def createRigidBody(self, **kwargs):
        ''' Create a object for MMD rigid body dynamics.
        ### Parameters ###
         @param shape_type the shape type.
         @param location location of the rigid body object.
         @param rotation rotation of the rigid body object.
         @param size
         @param dynamics_type the type of dynamics mode. (STATIC / DYNAMIC / DYNAMIC2)
         @param collision_group_number
         @param collision_group_mask list of boolean values. (length:16)
         @param name Object name (Optional)
         @param name_e English object name (Optional)
         @param bone
        '''

        shape_type = kwargs['shape_type']
        location = kwargs['location']
        rotation = kwargs['rotation']
        size = kwargs['size']
        dynamics_type = kwargs['dynamics_type']
        collision_group_number = kwargs.get('collision_group_number')
        collision_group_mask = kwargs.get('collision_group_mask')
        name = kwargs.get('name')
        name_e = kwargs.get('name_e')
        bone = kwargs.get('bone')

        friction = kwargs.get('friction')
        mass = kwargs.get('mass')
        angular_damping = kwargs.get('angular_damping')
        linear_damping = kwargs.get('linear_damping')
        bounce = kwargs.get('bounce')

        if shape_type == rigid_body.SHAPE_SPHERE:
            bpy.ops.mesh.primitive_uv_sphere_add(
                segments=16,
                ring_count=8,
                size=1,
                view_align=False,
                enter_editmode=False
                )
            size = mathutils.Vector([1,1,1]) * size[0]
            rigid_type = 'SPHERE'
            bpy.ops.object.shade_smooth()
        elif shape_type == rigid_body.SHAPE_BOX:
            bpy.ops.mesh.primitive_cube_add(
                view_align=False,
                enter_editmode=False
                )
            size = mathutils.Vector(size)
            rigid_type = 'BOX'
        elif shape_type == rigid_body.SHAPE_CAPSULE:
            obj = bpyutils.makeCapsule(radius=size[0], height=size[1])
            size = mathutils.Vector([1,1,1])
            rigid_type = 'CAPSULE'
            with bpyutils.select_object(obj):
                bpy.ops.object.shade_smooth()
        else:
            raise ValueError('Unknown shape type: %s'%(str(shape_type)))

        obj = bpy.context.active_object
        bpy.ops.rigidbody.object_add(type='ACTIVE')
        obj.location = location
        obj.rotation_mode = 'YXZ'
        obj.rotation_euler = rotation
        obj.scale = size
        obj.hide_render = True
        obj.mmd_type = 'RIGID_BODY'

        obj.mmd_rigid.shape = rigid_type
        obj.mmd_rigid.type = str(dynamics_type)
        obj.draw_type = 'WIRE'
        obj.show_wire = True

        with bpyutils.select_object(obj):
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        if collision_group_number is not None:
            obj.data.materials.append(RigidBodyMaterial.getMaterial(collision_group_number))
            obj.mmd_rigid.collision_group_number = collision_group_number
            obj.draw_type = 'SOLID'
            obj.show_transparent = True
        if collision_group_mask is not None:
            obj.mmd_rigid.collision_group_mask = collision_group_mask
        if name is not None:
            obj.name = name
            obj.mmd_rigid.name = name
        if name_e is not None:
            obj.mmd_rigid.name_e = name_e

        obj.rigid_body.collision_shape = rigid_type
        rb = obj.rigid_body
        if friction is not None:
            rb.friction = friction
        if mass is not None:
            rb.mass = mass
        if angular_damping is not None:
            rb.angular_damping = angular_damping
        if linear_damping is not None:
            rb.linear_damping = linear_damping
        if bounce:
            rb.restitution = bounce

        constraint = obj.constraints.new('CHILD_OF')
        constraint.target = self.armature()
        if bone is not None and bone != '':
            constraint.subtarget = bone
        constraint.name = 'mmd_tools_rigid_parent'
        constraint.mute = True

        obj.parent = self.rigidGroupObject()
        obj.select = False
        self.__root.mmd_root.is_built = False
        return obj

    def createJoint(self, **kwargs):
        ''' Create a joint object for MMD rigid body dynamics.
        ### Parameters ###
         @param shape_type the shape type.
         @param location location of the rigid body object.
         @param rotation rotation of the rigid body object.
         @param size
         @param dynamics_type the type of dynamics mode. (STATIC / DYNAMIC / DYNAMIC2)
         @param collision_group_number
         @param collision_group_mask list of boolean values. (length:16)
         @param name Object name
         @param name_e English object name (Optional)
         @param bone
        '''

        location = kwargs['location']
        rotation = kwargs['rotation']
        size = kwargs['size']

        rigid_a = kwargs['rigid_a']
        rigid_b = kwargs['rigid_b']

        max_loc = kwargs['maximum_location']
        min_loc = kwargs['minimum_location']
        max_rot = kwargs['maximum_rotation']
        min_rot = kwargs['minimum_rotation']
        spring_angular = kwargs['spring_angular']
        spring_linear = kwargs['spring_linear']

        name = kwargs['name']
        name_e = kwargs.get('name_e')

        obj = bpy.data.objects.new(
            'J.'+name,
            None)
        bpy.context.scene.objects.link(obj)
        obj.mmd_type = 'JOINT'
        obj.mmd_joint.name_j = name
        if name_e is not None:
            obj.mmd_joint.name_e = name_e

        obj.location = location
        obj.rotation_euler = rotation
        obj.empty_draw_size = size
        obj.empty_draw_type = 'ARROWS'
        obj.hide_render = True
        obj.parent = self.armature()

        with bpyutils.select_object(obj):
            bpy.ops.rigidbody.constraint_add(type='GENERIC_SPRING')
        rbc = obj.rigid_body_constraint

        rbc.object1 = rigid_a
        rbc.object2 = rigid_b

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

        rbc.limit_lin_x_upper = max_loc[0]
        rbc.limit_lin_y_upper = max_loc[1]
        rbc.limit_lin_z_upper = max_loc[2]

        rbc.limit_lin_x_lower = min_loc[0]
        rbc.limit_lin_y_lower = min_loc[1]
        rbc.limit_lin_z_lower = min_loc[2]

        rbc.limit_ang_x_upper = min_rot[0]
        rbc.limit_ang_y_upper = min_rot[1]
        rbc.limit_ang_z_upper = min_rot[2]

        rbc.limit_ang_x_lower = max_rot[0]
        rbc.limit_ang_y_lower = max_rot[1]
        rbc.limit_ang_z_lower = max_rot[2]

        obj.mmd_joint.spring_linear = spring_linear
        obj.mmd_joint.spring_angular = spring_angular

        obj.parent = self.jointGroupObject()
        obj.select = False
        self.__root.mmd_root.is_built = False
        return obj

    def create_ik_constraint(self, bone, ik_target, threshold=0.1):
        """ create IK constraint

        If the distance of the ik_target head and the bone tail is greater than threashold,
        then a dummy ik target bone is created.

         Args:
             bone: A pose bone to add a IK constraint
             id_target: A pose bone for IK target
             threshold: Threshold of creating a dummy bone

         Returns:
             The bpy.types.KinematicConstraint object created. It is set target
             and subtarget options.

        """
        ik_target_name = ik_target.name
        print((ik_target.head - bone.tail).length)
        if (ik_target.head - bone.tail).length > threshold:
            with bpyutils.edit_object(self.__arm) as data:
                dummy_target = data.edit_bones.new(name=ik_target.name + '.ik_target_dummy')
                dummy_target.head = bone.tail
                dummy_target.tail = dummy_target.head + mathutils.Vector([0, 0, 1])
                dummy_target.layers = (
                    False, False, False, False, False, False, False, False,
                    True, False, False, False, False, False, False, False,
                    False, False, False, False, False, False, False, False,
                    False, False, False, False, False, False, False, False
                    )
                dummy_target.parent = data.edit_bones[ik_target.name]
                ik_target_name = dummy_target.name
            dummy_ik_target = self.__arm.pose.bones[ik_target_name]
            dummy_ik_target.is_mmd_shadow_bone = True
            dummy_ik_target.mmd_shadow_bone_type = 'IK_TARGET'

        ik_const = bone.constraints.new('IK')
        ik_const.target = self.__arm
        ik_const.subtarget = ik_target_name
        return ik_const

    def __allObjects(self, obj):
        r = []
        for i in obj.children:
            r.append(i)
            r += self.__allObjects(i)
        return r

    def allObjects(self, obj=None):
        if obj is None:
            obj = self.__root
        return [obj] + self.__allObjects(obj)

    def rootObject(self):
        return self.__root

    def armature(self):
        if self.__arm is None:
            for i in filter(lambda x: x.type == 'ARMATURE', self.__root.children):
                self.__arm = i
                break
        return self.__arm

    def rigidGroupObject(self):
        if self.__rigid_grp is None:
            for i in filter(lambda x: x.mmd_type == 'RIGID_GRP_OBJ', self.__root.children):
                self.__rigid_grp = i
                break
            if self.__rigid_grp is None:
                rigids = bpy.data.objects.new(name='rigidbodies', object_data=None)
                rigids.mmd_type = 'RIGID_GRP_OBJ'
                rigids.parent = self.__root
                bpy.context.scene.objects.link(rigids)
                self.__rigid_grp = rigids
        return self.__rigid_grp
        
    def jointGroupObject(self):
        if self.__joint_grp is None:
            for i in filter(lambda x: x.mmd_type == 'JOINT_GRP_OBJ', self.__root.children):
                self.__joint_grp = i
                break
            if self.__joint_grp is None:
                joints = bpy.data.objects.new(name='joints', object_data=None)
                joints.mmd_type = 'JOINT_GRP_OBJ'
                joints.parent = self.__root
                bpy.context.scene.objects.link(joints)
                self.__joint_grp = joints
        return self.__joint_grp
        
    def temporaryGroupObject(self):
        if self.__temporary_grp is None:
            for i in filter(lambda x: x.mmd_type == 'TEMPORARY_GRP_OBJ', self.__root.children):
                self.__temporary_grp = i
                break
            if self.__temporary_grp is None:
                temporarys = bpy.data.objects.new(name='temporary', object_data=None)
                temporarys.mmd_type = 'TEMPORARY_GRP_OBJ'
                temporarys.parent = self.__root
                bpy.context.scene.objects.link(temporarys)
                self.__temporary_grp = temporarys
        return self.__temporary_grp

    def meshes(self):
        arm = self.armature()
        if arm is None:
            return []
        return filter(lambda x: x.type == 'MESH' and x.mmd_type == 'NONE', self.allObjects(arm))

    def rigidBodies(self):
        return filter(isRigidBodyObject, self.allObjects(self.rigidGroupObject()))

    def joints(self):
        return filter(isJointObject, self.allObjects(self.jointGroupObject()))

    def temporaryObjects(self):
        return filter(isTemporaryObject, self.allObjects(self.rigidGroupObject())+self.allObjects(self.temporaryGroupObject()))

    def renameBone(self, old_bone_name, new_bone_name):
        armature = self.armature()
        bone = armature.pose.bones[old_bone_name]

        mmd_root = self.rootObject().mmd_root
        for frame in mmd_root.display_item_frames:
            for item in frame.items:
                if item.type == 'BONE' and item.name == old_bone_name:
                    item.name = new_bone_name
        for mesh in self.meshes():
            if old_bone_name in mesh.vertex_groups:
                mesh.vertex_groups[old_bone_name].name = new_bone_name

        bone.name = new_bone_name

    def build(self):
        logging.info('****************************************')
        logging.info(' Build rig')
        logging.info('****************************************')
        self.buildRigids()
        self.buildJoints()
        self.__root.mmd_root.is_built = True

    def clean(self):
        pose_bones = []
        arm = self.armature()
        track_to_bone_map = {}
        if arm is not None:
            pose_bones = arm.pose.bones
        for i in pose_bones:
            if 'mmd_tools_rigid_track' in i.constraints:
                const = i.constraints['mmd_tools_rigid_track']
                track_to_bone_map[const.target] = i
                i.constraints.remove(const)

        for i in self.temporaryObjects():
            if i.mmd_type in ['NON_COLLISION_CONSTRAINT', 'SPRING_GOAL', 'SPRING_CONSTRAINT']:
                bpy.context.scene.objects.unlink(i)
                bpy.data.objects.remove(i)
            elif i.mmd_type == 'TRACK_TARGET':
                rigid = i.parent
                bone = track_to_bone_map.get(i)
                logging.info('Create a "CHILD_OF" constraint for %s', rigid.name)
                constraint = rigid.constraints.new('CHILD_OF')
                constraint.target = arm
                if bone is not None:
                    constraint.subtarget = bone.name
                constraint.name = 'mmd_tools_rigid_parent'
                constraint.mute = True
                bpy.context.scene.objects.unlink(i)
                bpy.data.objects.remove(i)
        self.rootObject().mmd_root.is_built = False

    def updateRigid(self, rigid_obj):
        if rigid_obj.mmd_type != 'RIGID_BODY':
            raise TypeError('rigid_obj must be a mmd_rigid object')

        rigid = rigid_obj.mmd_rigid
        relation = rigid_obj.constraints['mmd_tools_rigid_parent']
        arm = relation.target
        bone_name = relation.subtarget
        target_bone = None
        if arm is not None and bone_name != '':
            target_bone = arm.pose.bones[bone_name]

        if target_bone is not None:
            for i in target_bone.constraints:
                if i.name == 'mmd_tools_rigid_track':
                    target_bone.constraints.remove(i)

        if int(rigid.type) == rigid_body.MODE_STATIC:
            rigid_obj.rigid_body.kinematic = True
        else:
            rigid_obj.rigid_body.kinematic = False

        if int(rigid.type) == rigid_body.MODE_STATIC:
            if arm is not None and bone_name != '':
                relation.mute = False
                relation.inverse_matrix = mathutils.Matrix(target_bone.matrix).inverted()
            else:
                relation.mute = True
        else:
            relation.mute = True

        if int(rigid.type) in [rigid_body.MODE_DYNAMIC, rigid_body.MODE_DYNAMIC_BONE] and arm is not None and target_bone is not None:
            empty = bpy.data.objects.new(
                'mmd_bonetrack',
                None)
            bpy.context.scene.objects.link(empty)
            empty.location = target_bone.tail
            empty.empty_draw_size = 0.1
            empty.empty_draw_type = 'ARROWS'
            empty.mmd_type = 'TRACK_TARGET'
            empty.hide = True
            empty.parent = self.temporaryGroupObject()

            rigid_obj.mmd_rigid.bone = relation.subtarget
            rigid_obj.constraints.remove(relation)

            bpyutils.setParent(empty, rigid_obj)
            empty.select = False
            empty.hide = True

            for i in target_bone.constraints:
                if i.type == 'IK':
                    i.mute = True
            const = target_bone.constraints.new('DAMPED_TRACK')
            const.name='mmd_tools_rigid_track'
            const.target = empty

        t=rigid_obj.hide
        with bpyutils.select_object(rigid_obj):
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        rigid_obj.hide = t

        rigid_obj.rigid_body.collision_shape = rigid.shape

    def __getRigidRange(self, obj):
        return (mathutils.Vector(obj.bound_box[0]) - mathutils.Vector(obj.bound_box[6])).length

    def __createNonCollisionConstraint(self, nonCollisionJointTable):
        total_len = len(nonCollisionJointTable)
        if total_len < 1:
            return
            
        start_time = time.time()
        logging.debug('-'*60)
        logging.debug(' creating ncc, counts: %d', total_len)
                        
        ncc_obj = bpy.data.objects.new('ncc', None)
        bpy.context.scene.objects.link(ncc_obj)
        ncc_obj.location = [0, 0, 0]
        ncc_obj.empty_draw_size = 0.5
        ncc_obj.empty_draw_type = 'ARROWS'
        ncc_obj.mmd_type = 'NON_COLLISION_CONSTRAINT'
        ncc_obj.hide_render = True
        ncc_obj.parent = self.temporaryGroupObject()
        with bpyutils.select_object(ncc_obj):
            bpy.ops.rigidbody.constraint_add(type='GENERIC')
        rb = ncc_obj.rigid_body_constraint
        rb.disable_collisions = True
        
        ncc_objs = []
        last_selected = [ncc_obj]
        while len(ncc_objs) < total_len:
            bpy.ops.object.duplicate()
            ncc_objs.extend(bpy.context.selected_objects)
            remain = total_len - len(ncc_objs) - len(bpy.context.selected_objects)
            if remain < 0:
                last_selected = bpy.context.selected_objects
                for i in range(-remain):
                    last_selected[i].select = False
            else:
                for i in range(min(remain, len(last_selected))):
                    last_selected[i].select = True
            last_selected = bpy.context.selected_objects
        logging.debug(' created %d ncc.', len(ncc_objs))

        for i in range(total_len):
            rb = ncc_objs[i].rigid_body_constraint
            rb.object1, rb.object2 = nonCollisionJointTable[i]
        
        logging.debug(' finish in %f seconds.', time.time() - start_time)
        logging.debug('-'*60)

    def buildRigids(self, distance_of_ignore_collisions=1.5):
        logging.debug('--------------------------------')
        logging.debug(' Build riggings of rigid bodies')
        logging.debug('--------------------------------')
        rigid_objects = list(self.rigidBodies())
        for i in rigid_objects:
            logging.debug(' Updating rigid body %s', i.name)
            self.updateRigid(i)
        rigid_object_groups = [[] for i in range(16)]
        for i in rigid_objects:
            rigid_object_groups[i.mmd_rigid.collision_group_number].append(i)

        jointMap = {}
        for joint in self.joints():
            rbc = joint.rigid_body_constraint
            rbc.disable_collisions = False
            jointMap[frozenset((rbc.object1, rbc.object2))] = joint
            jointMap[frozenset((rbc.object2, rbc.object1))] = joint

        logging.info('Creating non collision constraints')
        # create non collision constraints
        nonCollisionJointTable = []
        non_collision_pairs = set()
        rigid_object_cnt = len(rigid_objects)
        for cnt, obj_a in enumerate(rigid_objects):
            logging.info('%3d/%3d: %s', cnt+1, rigid_object_cnt, obj_a.name)
            for n, ignore in enumerate(obj_a.mmd_rigid.collision_group_mask):
                if not ignore:
                    continue
                for obj_b in rigid_object_groups[n]:
                    pair = frozenset((obj_a, obj_b))
                    if pair in non_collision_pairs:
                        continue
                    if pair in jointMap:
                        joint = jointMap[pair]
                        joint.rigid_body_constraint.disable_collisions = True
                    else:
                        distance = (obj_a.location - obj_b.location).length
                        if distance < distance_of_ignore_collisions * (self.__getRigidRange(obj_a) + self.__getRigidRange(obj_b)) * 0.5:
                            nonCollisionJointTable.append((obj_a, obj_b))
                    non_collision_pairs.add(pair)
                    non_collision_pairs.add(frozenset((obj_b, obj_a)))
        
        self.__createNonCollisionConstraint(nonCollisionJointTable)
        return rigid_objects

    def __makeSpring(self, target, base_obj, spring_stiffness):
        with bpyutils.select_object(target):
            bpy.ops.object.duplicate()
            spring_target = bpy.context.scene.objects.active
        t = spring_target.constraints.get('mmd_tools_rigid_parent')
        if t is not None:
            spring_target.constraints.remove(t)
        spring_target.mmd_type = 'SPRING_GOAL'
        spring_target.rigid_body.kinematic = True
        spring_target.rigid_body.collision_groups = (False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True)
        spring_target.parent = base_obj
        spring_target.matrix_parent_inverse = mathutils.Matrix(base_obj.matrix_basis).inverted()
        spring_target.hide = True

        obj = bpy.data.objects.new(
            'S.'+target.name,
            None)
        bpy.context.scene.objects.link(obj)
        obj.location = target.location
        obj.empty_draw_size = 0.1
        obj.empty_draw_type = 'ARROWS'
        obj.hide_render = True
        obj.select = False
        obj.hide = True
        obj.mmd_type = 'SPRING_CONSTRAINT'
        obj.parent = self.temporaryGroupObject()

        with bpyutils.select_object(obj):
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

    def updateJoint(self, joint_obj):
        # TODO: This process seems to be an incorrect method for creating spring constraints. Fix or delete this.
        rbc = joint_obj.rigid_body_constraint
        if rbc.object1.rigid_body.kinematic:
            self.__makeSpring(rbc.object2, rbc.object1, joint_obj.mmd_joint.spring_angular)
        if rbc.object2.rigid_body.kinematic:
            self.__makeSpring(rbc.object1, rbc.object2, joint_obj.mmd_joint.spring_angular)

    def buildJoints(self):
        pass

    def applyAdditionalTransformConstraints(self, force=False):
        arm = self.armature()
        fnBone = FnBone()
        for bone in arm.pose.bones[:]:
            fnBone.pose_bone = bone
            fnBone.apply_additional_transformation()


class RigidBodyMaterial:
    COLORS = [
        0x7fddd4,
        0xf0e68c,
        0xee82ee,
        0xffe4e1,
        0x8feeee,
        0xadff2f,
        0xfa8072,
        0x9370db,

        0x40e0d0,
        0x96514d,
        0x5a964e,
        0xe6bfab,
        0xd3381c,
        0x165e83,
        0x701682,
        0x828216,
        ]
    @classmethod
    def getMaterial(cls, number):
        number = int(number)
        material_name = 'mmd_tools_rigid_%d'%(number)
        if material_name not in bpy.data.materials:
            mat = bpy.data.materials.new(material_name)
            color = cls.COLORS[number]
            mat.diffuse_color = [((0xff0000 & color) >> 16) / float(255), ((0x00ff00 & color) >> 8) / float(255), (0x0000ff & color) / float(255)]
            mat.diffuse_intensity = 1
            mat.specular_intensity = 0
            mat.alpha = 0.5
            mat.use_transparency = True
            mat.use_shadeless = True
        else:
            mat = bpy.data.materials[material_name]
        return mat
