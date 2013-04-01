# -*- coding: utf-8 -*-
from . import pmx
from . import utils

import math

import bpy
import os
import mathutils


class PMXImporter:
    TO_BLE_MATRIX = mathutils.Matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]])

    def __init__(self):
        self.__pmxFile = None
        self.__targetScene = bpy.context.scene

        self.__scale = None
        self.__deleteTipBones = False

        self.__root = None
        self.__armObj = None
        self.__meshObj = None

        self.__vertexTable = None
        self.__vertexGroupTable = None
        self.__textureTable = None

        self.__rigidTable = []
        self.__jointTable = []

        self.__materialFaceCountTable = None

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

    ## 必要なオブジェクトを生成し、ターゲットシーンにリンク
    def __createObjects(self):
        pmxModel = self.__pmxFile.model

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

    def __importVertexGroup(self):
        self.__vertexGroupTable = []
        for i in self.__pmxFile.model.bones:
            self.__vertexGroupTable.append(self.__meshObj.vertex_groups.new(name=i.name))

    def __importVertices(self):
        self.__importVertexGroup()

        pmxModel = self.__pmxFile.model
        mesh = self.__meshObj.data

        mesh.vertices.add(count=len(self.__pmxFile.model.vertices))
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
        pmxModel = self.__pmxFile.model

        self.__textureTable = []
        for i in pmxModel.textures:
            name = os.path.basename(i.path).split('.')[0]
            tex = bpy.data.textures.new(name=name, type='IMAGE')
            try:
                tex.image = bpy.data.images.load(filepath=i.path)
            except Exception:
                print('WARNING: failed to load %s'%str(i.path))
            self.__textureTable.append(tex)


    def __importBones(self):

        pmxModel = self.__pmxFile.model

        utils.enterEditMode(self.__armObj)
        try:
            editBoneTable = []
            tipBones = []
            self.__boneTable = []
            for i in pmxModel.bones:
                bone = self.__armObj.data.edit_bones.new(name=i.name)
                loc = mathutils.Vector(i.location) * self.__scale * self.TO_BLE_MATRIX
                bone.head = loc
                editBoneTable.append(bone)
                self.__boneTable.append(i.name)

            for b_bone, m_bone in zip(editBoneTable, pmxModel.bones):
                if m_bone.parent != -1:
                    b_bone.parent = editBoneTable[m_bone.parent]

            for b_bone, m_bone in zip(editBoneTable, pmxModel.bones):
                if isinstance(m_bone.displayConnection, int):
                    if m_bone.displayConnection != -1:
                        b_bone.tail = editBoneTable[m_bone.displayConnection].head
                    else:
                        b_bone.tail = b_bone.head
                else:
                    loc = mathutils.Vector(m_bone.displayConnection) * self.TO_BLE_MATRIX * self.__scale
                    b_bone.tail = b_bone.head + loc

            for b_bone in editBoneTable:
                if b_bone.length  < 0.001:
                    loc = mathutils.Vector([0, 0, 1]) * self.__scale
                    b_bone.tail = b_bone.head + loc
                    if len(b_bone.children) == 0:
                        tipBones.append(b_bone.name)

            for b_bone, m_bone in zip(editBoneTable, pmxModel.bones):
                if b_bone.parent is not None and b_bone.parent.tail == b_bone.head:
                    if not m_bone.isMovable:
                        b_bone.use_connect = True

        finally:
            bpy.ops.object.mode_set(mode='OBJECT')

        pose_bones = self.__armObj.pose.bones
        bpy.types.PoseBone.isTipBone = bpy.props.BoolProperty(name='isTipBone', default=False)
        bpy.types.PoseBone.name_j = bpy.props.StringProperty(name='name_j', description='the bone name in japanese.')
        bpy.types.PoseBone.name_e = bpy.props.StringProperty(name='name_e', description='the bone name in english.')
        for p_bone in pmxModel.bones:
            b_bone = pose_bones[p_bone.name]
            b_bone.name_e = p_bone.name_e
            if not p_bone.isRotatable:
                b_bone.lock_rotation = [True, True, True]
            if not p_bone.isMovable:
                b_bone.lock_location =[True, True, True]

            if p_bone.isIK:
                if p_bone.target != -1:
                    bone = pose_bones[self.__boneTable[p_bone.target]].parent
                    ikConst = bone.constraints.new('IK')
                    ikConst.chain_count = len(p_bone.ik_links)
                    ikConst.target = self.__armObj
                    ikConst.subtarget = p_bone.name
                    if p_bone.isRotatable and not p_bone.isMovable :
                        ikConst.use_location = p_bone.isMovable
                        ikConst.use_rotation = p_bone.isRotatable
                    for i in p_bone.ik_links:
                        if i.maximumAngle is not None:
                            bone = pose_bones[self.__boneTable[i.target]]
                            bone.use_ik_limit_x = True
                            bone.use_ik_limit_y = True
                            bone.use_ik_limit_z = True
                            bone.ik_max_x = -i.minimumAngle[0]
                            bone.ik_max_y = i.maximumAngle[1]
                            bone.ik_max_z = i.maximumAngle[2]
                            bone.ik_min_x = -i.maximumAngle[0]
                            bone.ik_min_y = i.minimumAngle[1]
                            bone.ik_min_z = i.minimumAngle[2]

        if not self.__deleteTipBones:
            for i in tipBones:
                b = pose_bones[i]
                b.isTipBone = True
                b.lock_rotation = [True, True, True]
                b.lock_location = [True, True, True]
                b.lock_scale = [True, True, True]
                b.bone.hide = True

        else:
            utils.enterEditMode(self.__armObj)
            try:
                edit_bones = self.__armObj.data.edit_bones
                for i in tipBones:
                    edit_bone = edit_bones[i]
                    if edit_bone.parent is not None:
                        utils.mergeVertexGroup(self.__meshObj, edit_bone.name, edit_bone.parent.name)
                    edit_bones.remove(edit_bone)
            finally:
                bpy.ops.object.mode_set(mode='OBJECT')


    def __importRigids(self):
        self.__rigidTable = []
        for rigid in self.__pmxFile.model.rigids:
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
            utils.selectAObject(obj)
            bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
            obj.location = loc
            obj.rotation_euler = rot
            bpy.ops.rigidbody.object_add(type='ACTIVE')
            if rigid.mode == pmx.Rigid.MODE_STATIC and rigid.bone is not None:
                bpy.ops.object.modifier_add(type='COLLISION')
                utils.setParentToBone(obj, self.__armObj, self.__boneTable[rigid.bone])
            elif rigid.bone is not None:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select = True
                bpy.context.scene.objects.active = self.__root
                bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)

                target_bone = self.__armObj.pose.bones[self.__boneTable[rigid.bone]]
                bpy.ops.object.add(type='EMPTY',
                                   view_align=False,
                                   enter_editmode=False,
                                   location=target_bone.tail
                                   )
                empty = bpy.context.selected_objects[0]
                empty.name = 'mmd_bonetrack'
                empty.empty_draw_size = 0.5 * self.__scale
                empty.empty_draw_type = 'ARROWS'

                bpy.context.scene.objects.active = obj
                bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=False)

                empty.hide = True


                for i in target_bone.constraints:
                    if i.type == 'IK':
                        i.influence = 0
                const = target_bone.constraints.new('DAMPED_TRACK')
                const.target = empty
            else:
                obj.parent = self.__armObj
                bpy.ops.object.select_all(action='DESELECT')
                obj.select = True

            obj.rigid_body.collision_shape = rigid_type
            group_flags = []
            for i in range(20):
                group_flags.append(i==rigid.collision_group_number or (rigid.collision_group_mask & (1<<i) != 0))
            rb = obj.rigid_body
            rb.collision_groups = group_flags
            rb.friction = rigid.friction
            rb.mass = rigid.mass
            rb.angular_damping = rigid.rotation_attenuation
            rb.linear_damping = rigid.velocity_attenuation
            rb.restitution = rigid.bounce
            if rigid.mode == pmx.Rigid.MODE_STATIC:
                rb.kinematic = True

            self.__rigidTable.append(obj)

    def __importJoints(self):
        if self.__onlyCollisions:
            return
        self.__jointTable = []
        for joint in self.__pmxFile.model.joints:
            loc = mathutils.Vector(joint.location) * self.TO_BLE_MATRIX * self.__scale
            rot = mathutils.Vector(joint.rotation) * self.TO_BLE_MATRIX * -1
            bpy.ops.object.add(type='EMPTY',
                               view_align=False,
                               enter_editmode=False,
                               location=loc,
                               rotation=rot
                               )
            obj = bpy.context.selected_objects[0]
            obj.name = 'J.'+joint.name
            obj.empty_draw_size = 0.5 * self.__scale
            obj.empty_draw_type = 'ARROWS'
            obj.hide_render = True
            obj.is_mmd_joint = True
            bpy.ops.rigidbody.constraint_add(type='GENERIC_SPRING')
            rbc = obj.rigid_body_constraint

            rigid1 = self.__rigidTable[joint.src_rigid]
            rigid2 = self.__rigidTable[joint.dest_rigid]
            rbc.object1 = rigid1
            rbc.object2 = rigid2

            if rigid1.rigid_body.kinematic and not rigid2.rigid_body.kinematic or not rigid1.rigid_body.kinematic and rigid2.rigid_body.kinematic:
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
            rbc.limit_ang_x_upper = max_rot[0]
            rbc.limit_ang_y_upper = -min_rot[1]
            rbc.limit_ang_z_upper = -min_rot[2]

            rbc.limit_ang_x_lower = min_rot[0]
            rbc.limit_ang_y_lower = -max_rot[1]
            rbc.limit_ang_z_lower = -max_rot[2]

            # spring_damp = mathutils.Vector(joint.spring_constant) * self.TO_BLE_MATRIX
            # rbc.spring_damping_x = spring_damp[0]
            # rbc.spring_damping_y = spring_damp[1]
            # rbc.spring_damping_z = spring_damp[2]

            # spring_stiff = mathutils.Vector()
            # rbc.spring_stiffness_x = spring_stiff[0]
            # rbc.spring_stiffness_y = spring_stiff[1]
            # rbc.spring_stiffness_z = spring_stiff[2]

            self.__jointTable.append(obj)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select = True
            bpy.context.scene.objects.active = self.__armObj
            bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=True)


    def __importMaterials(self):
        self.__importTextures()
        bpy.types.Material.ambient_color = bpy.props.FloatVectorProperty(name='ambient color')

        pmxModel = self.__pmxFile.model

        self.__materialTable = []
        self.__materialFaceCountTable = []
        for i in pmxModel.materials:
            mat = bpy.data.materials.new(name=i.name)
            mat.diffuse_color = i.diffuse[0:3]
            mat.alpha = i.diffuse[3]
            mat.ambient_color = i.ambient
            mat.specular_color = i.specular[0:3]
            mat.specular_alpha = i.specular[3]
            self.__materialFaceCountTable.append(int(i.vertex_count/3))
            self.__meshObj.data.materials.append(mat)
            if i.texture != -1:
                texture_slot = mat.texture_slots.add()
                texture_slot.texture = self.__textureTable[i.texture]
                texture_slot.texture_coords = 'UV'


    def __importFaces(self):
        pmxModel = self.__pmxFile.model
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
        pmxModel = self.__pmxFile.model

        utils.selectAObject(self.__meshObj)
        bpy.ops.object.shape_key_add()

        for morph in filter(lambda x: isinstance(x, pmx.VertexMorph), pmxModel.morphs):
            shapeKey = self.__meshObj.shape_key_add(morph.name)
            for md in morph.data:
                shapeKeyPoint = shapeKey.data[md.vertex]
                offset = mathutils.Vector(md.offset) * self.TO_BLE_MATRIX
                shapeKeyPoint.co = shapeKeyPoint.co + offset * self.__scale

    def __hideRigidsAndJoints(self, obj):
        if obj.is_mmd_rigid:
            obj.hide = True
        elif obj.is_mmd_joint:
            obj.hide = True

        for i in obj.children:
            self.__hideRigidsAndJoints(i)

    def __addArmatureModifier(self, meshObj, armObj):
        armModifier = meshObj.modifiers.new(name='Armature', type='ARMATURE')
        armModifier.object = armObj
        armModifier.use_vertex_groups = True

    def __renameLRBones(self):
        pose_bones = self.__armObj.pose.bones
        for i in pose_bones:
            i.name_j = i.name
            i.name = utils.convertNameToLR(i.name)
            self.__meshObj.vertex_groups[i.name_j].name = i.name

    def execute(self, **args):
        self.__pmxFile = pmx.File()
        self.__pmxFile.load(args['filepath'])

        self.__scale = args.get('scale', 1.0)
        renameLRBones = args.get('rename_LR_bones', False)
        self.__deleteTipBones = args.get('delete_tip_bones', False)
        self.__onlyCollisions = args.get('only_collisions', False)

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
        if args.get('hide_rigids', False):
            self.__hideRigidsAndJoints(self.__root)
        self.__armObj.pmx_import_scale = self.__scale
