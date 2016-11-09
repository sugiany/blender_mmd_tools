# -*- coding: utf-8 -*-
import mathutils
import bpy
import math
import re
import os
import logging

import mmd_tools.core.camera as mmd_camera
import mmd_tools.core.lamp as mmd_lamp
import mmd_tools.core.vmd as vmd
from mmd_tools import utils
from mmd_tools import translations


class RenamedBoneMapper:
    def __init__(self, armObj=None, rename_LR_bones=True, use_underscore=False, translate_to_english=False):
        self.__pose_bones = armObj.pose.bones if armObj else None
        self.__rename_LR_bones = rename_LR_bones
        self.__use_underscore = use_underscore
        self.__translate_to_english = translate_to_english

    def init(self, armObj):
        self.__pose_bones = armObj.pose.bones
        return self

    def get(self, bone_name, default=None):
        bl_bone_name = bone_name
        if self.__rename_LR_bones:
            bl_bone_name = utils.convertNameToLR(bl_bone_name, self.__use_underscore)
        if self.__translate_to_english:
            bl_bone_name = translations.translateFromJp(bl_bone_name)
        return self.__pose_bones.get(bl_bone_name, default)


class VMDImporter:
    def __init__(self, filepath, scale=1.0, bone_mapper=None, convert_mmd_camera=True, convert_mmd_lamp=True, frame_margin=5):
        self.__vmdFile = vmd.File()
        self.__vmdFile.load(filepath=filepath)
        self.__scale = scale
        self.__convert_mmd_camera = convert_mmd_camera
        self.__convert_mmd_lamp = convert_mmd_lamp
        self.__bone_mapper = bone_mapper
        self.__frame_margin = frame_margin + 1


    @staticmethod
    def makeVMDBoneLocationToBlenderMatrix(blender_bone):
        #mat = mathutils.Matrix([
        #        [blender_bone.x_axis.x, blender_bone.x_axis.y, blender_bone.x_axis.z, 0.0],
        #        [blender_bone.y_axis.x, blender_bone.y_axis.y, blender_bone.y_axis.z, 0.0],
        #        [blender_bone.z_axis.x, blender_bone.z_axis.y, blender_bone.z_axis.z, 0.0],
        #        [0.0, 0.0, 0.0, 1.0]
        #        ])
        mat = blender_bone.bone.matrix_local.to_3x3().transposed().to_4x4()
        mat2 = mathutils.Matrix([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]])
        return mat * mat2

    @staticmethod
    def convertVMDBoneRotationToBlender(blender_bone, rotation):
        if not isinstance(rotation, mathutils.Quaternion):
            rot = mathutils.Quaternion()
            rot.x, rot.y, rot.z, rot.w = rotation
            rotation = rot
        #mat = mathutils.Matrix()
        #mat[0][0], mat[1][0], mat[2][0] = blender_bone.x_axis.x, blender_bone.y_axis.x, blender_bone.z_axis.x
        #mat[0][1], mat[1][1], mat[2][1] = blender_bone.x_axis.y, blender_bone.y_axis.y, blender_bone.z_axis.y
        #mat[0][2], mat[1][2], mat[2][2] = blender_bone.x_axis.z, blender_bone.y_axis.z, blender_bone.z_axis.z
        mat = blender_bone.bone.matrix_local.to_3x3().transposed().to_4x4()
        (vec, angle) = rotation.to_axis_angle()
        v = mathutils.Vector((-vec.x, -vec.z, -vec.y))
        return mathutils.Quaternion(mat*v, angle).normalized()

    @staticmethod
    def __minRotationDiff(prev_q, curr_q):
        pq, q = prev_q, curr_q
        nq = q.copy()
        nq.negate()
        t1 = (pq.w-q.w)**2+(pq.x-q.x)**2+(pq.y-q.y)**2+(pq.z-q.z)**2
        t2 = (pq.w-nq.w)**2+(pq.x-nq.x)**2+(pq.y-nq.y)**2+(pq.z-nq.z)**2
        #t1 = pq.rotation_difference(q).angle
        #t2 = pq.rotation_difference(nq).angle
        if t2 < t1:
            return nq
        return q

    @staticmethod
    def __setInterpolation(bezier, kp0, kp1):
        if bezier[0] == bezier[1] and bezier[2] == bezier[3]:
            kp0.interpolation = 'LINEAR'
        else:
            kp0.interpolation = 'BEZIER'
            kp0.handle_right_type = 'FREE'
            kp1.handle_left_type = 'FREE'
            d = (kp1.co - kp0.co) / 127.0
            kp0.handle_right = kp0.co + mathutils.Vector((d.x * bezier[0], d.y * bezier[1]))
            kp1.handle_left = kp0.co + mathutils.Vector((d.x * bezier[2], d.y * bezier[3]))

    def __assignToArmature(self, armObj, action_name=None):
        if action_name is not None:
            act = bpy.data.actions.new(name=action_name)
            a = armObj.animation_data_create()
            a.action = act

        boneAnim = self.__vmdFile.boneAnimation
        extra_frame = 1 if self.__frame_margin > 1 else 0

        action = armObj.animation_data.action
        pose_bones = armObj.pose.bones
        if self.__bone_mapper:
            pose_bones = self.__bone_mapper(armObj)
        bone_name_table = {}
        for name, keyFrames in boneAnim.items():
            num_frame = len(keyFrames)
            if num_frame < 1:
                continue
            bone = pose_bones.get(name, None)
            if bone is None:
                logging.warning('WARNING: not found bone %s', name)
                continue
            logging.info('(bone) frames:%5d  name: %s', len(keyFrames), name)
            assert(bone_name_table.get(bone.name, name) == name)
            bone_name_table[bone.name] = name

            fcurves = [None]*7 # x, y, z, rw, rx, ry, rz
            default_values = [0]*7
            data_path = 'pose.bones["%s"].location'%bone.name
            for axis_i in range(3):
                fcurves[axis_i] = action.fcurves.new(data_path=data_path, index=axis_i, action_group=bone.name)
                default_values[axis_i] = bone.location[axis_i]
            data_path = 'pose.bones["%s"].rotation_quaternion'%bone.name
            for axis_i in range(4):
                fcurves[3+axis_i] = action.fcurves.new(data_path=data_path, index=axis_i, action_group=bone.name)
                default_values[3+axis_i] = bone.rotation_quaternion[axis_i]

            for i, c in enumerate(fcurves):
                c.keyframe_points.add(extra_frame+num_frame)
                kp_iter = iter(c.keyframe_points)
                if extra_frame:
                    kp = next(kp_iter)
                    kp.co = (1, default_values[i])
                    kp.interpolation = 'LINEAR'
                fcurves[i] = kp_iter

            mat = self.makeVMDBoneLocationToBlenderMatrix(bone)
            prev_rot = None
            prev_kps = None
            vmd_frames = sorted(keyFrames, key=lambda x:x.frame_number)
            for k, x, y, z, rw, rx, ry, rz in zip(vmd_frames, *fcurves):
                frame = k.frame_number + self.__frame_margin
                loc = mat * mathutils.Vector(k.location) * self.__scale
                curr_rot = self.convertVMDBoneRotationToBlender(bone, k.rotation)
                if prev_rot is not None:
                    curr_rot = self.__minRotationDiff(prev_rot, curr_rot)
                prev_rot = curr_rot

                x.co = (frame, loc[0])
                y.co = (frame, loc[1])
                z.co = (frame, loc[2])
                rw.co = (frame, curr_rot[0])
                rx.co = (frame, curr_rot[1])
                ry.co = (frame, curr_rot[2])
                rz.co = (frame, curr_rot[3])

                curr_kps = (x, y, z, rw, rx, ry, rz)
                if prev_kps is not None:
                    interps = [k.interp[idx:idx+16:4] for idx in (0, 32, 16, 48, 48, 48, 48)] # x, z, y, rw, rx, ry, rz
                    for interp, prev_kp, kp in zip(interps, prev_kps, curr_kps):
                        self.__setInterpolation(interp, prev_kp, kp)
                prev_kps = curr_kps

    def __assignToMesh(self, meshObj, action_name=None):
        if meshObj.data.shape_keys is None:
            logging.warning('WARNING: mesh object %s does not have any shape key', meshObj.name)
            return

        if action_name is not None:
            act = bpy.data.actions.new(name=action_name)
            a = meshObj.data.shape_keys.animation_data_create()
            a.action = act

        shapeKeyAnim = self.__vmdFile.shapeKeyAnimation

        shapeKeyDict = {}
        for i in meshObj.data.shape_keys.key_blocks:
            shapeKeyDict[i.name] = i

        for name, keyFrames in shapeKeyAnim.items():
            if name not in shapeKeyDict:
                logging.warning('WARNING: not found shape key %s', name)
                continue
            logging.info('(mesh) frames:%5d  name: %s', len(keyFrames), name)
            shapeKey = shapeKeyDict[name]
            for i in keyFrames:
                shapeKey.value = i.weight
                shapeKey.keyframe_insert(data_path='value',
                                         group=name,
                                         frame=i.frame_number+self.__frame_margin)

    @staticmethod
    def detectCameraChange(fcurve, threshold=10.0):
        frames = list(fcurve.keyframe_points)
        frameCount = len(frames)
        frames.sort(key=lambda x:x.co[0])
        for i, f in enumerate(frames):
            if i+1 < frameCount:
                n = frames[i+1]
                if n.co[0] - f.co[0] <= 1.0 and abs(f.co[1] - n.co[1]) > threshold:
                    f.interpolation = 'CONSTANT'

    def __assignToCamera(self, cameraObj, action_name=None):
        mmdCameraInstance = mmd_camera.MMDCamera.convertToMMDCamera(cameraObj)
        mmdCamera = mmdCameraInstance.object()
        if action_name is not None:
            act = bpy.data.actions.new(name=action_name)
            a = mmdCamera.animation_data_create()
            a.action = act

        cameraObj = mmdCameraInstance.camera()
        cameraAnim = self.__vmdFile.cameraAnimation
        cameraAnim.sort(key=lambda x:x.frame_number)
        logging.info('(camera) frames:%5d  name: %s', len(cameraAnim), mmdCamera.name)
        for keyFrame in cameraAnim:
            mmdCamera.mmd_camera.angle = math.radians(keyFrame.angle)
            mmdCamera.mmd_camera.is_perspective = keyFrame.persp
            cameraObj.location[1] = keyFrame.distance * self.__scale
            mmdCamera.location = mathutils.Vector((keyFrame.location[0], keyFrame.location[2], keyFrame.location[1])) * self.__scale
            mmdCamera.rotation_euler = mathutils.Vector((keyFrame.rotation[0], keyFrame.rotation[2], keyFrame.rotation[1]))
            mmdCamera.keyframe_insert(data_path='mmd_camera.angle',
                                      frame=keyFrame.frame_number+self.__frame_margin)
            mmdCamera.keyframe_insert(data_path='mmd_camera.is_perspective',
                                      frame=keyFrame.frame_number+self.__frame_margin)
            cameraObj.keyframe_insert(data_path='location', index=1,
                                      frame=keyFrame.frame_number+self.__frame_margin)
            mmdCamera.keyframe_insert(data_path='location',
                                      frame=keyFrame.frame_number+self.__frame_margin)
            mmdCamera.keyframe_insert(data_path='rotation_euler',
                                      frame=keyFrame.frame_number+self.__frame_margin)

        paths = ['rotation_euler', 'location', 'mmd_camera.angle']
        for fcurve in cameraObj.animation_data.action.fcurves:
            if fcurve.data_path == 'location' and fcurve.array_index == 1:
                frames = list(fcurve.keyframe_points)
                frames.sort(key=lambda kp:kp.co.x)
                for i in range(1, len(cameraAnim)):
                    interp = cameraAnim[i].interp
                    self.__setInterpolation([interp[16 + j] for j in [0, 2, 1, 3]], frames[i - 1], frames[i])
        for fcurve in act.fcurves:
            if fcurve.data_path in paths:
                if fcurve.data_path =='location':
                    idx = [0, 2, 1][fcurve.array_index] * 4
                else:
                    idx = (paths.index(fcurve.data_path) + 3) * 4
                frames = list(fcurve.keyframe_points)
                frames.sort(key=lambda kp:kp.co.x)
                for i in range(1, len(cameraAnim)):
                    interp = cameraAnim[i].interp
                    self.__setInterpolation([interp[idx + j] for j in [0, 2, 1, 3]], frames[i - 1], frames[i])

        for fcurve in mmdCamera.animation_data.action.fcurves:
            if fcurve.data_path == 'rotation_euler':
                self.detectCameraChange(fcurve)

    @staticmethod
    def detectLampChange(fcurve, threshold=0.1):
        frames = list(fcurve.keyframe_points)
        frameCount = len(frames)
        frames.sort(key=lambda x:x.co[0])
        for i, f in enumerate(frames):
            if i+1 < frameCount:
                n = frames[i+1]
                if n.co[0] - f.co[0] <= 1.0 and abs(f.co[1] - n.co[1]) > threshold:
                    f.interpolation = 'CONSTANT'

    def __assignToLamp(self, lampObj, action_name=None):
        mmdLamp = mmd_lamp.MMDLamp.convertToMMDLamp(lampObj).object()
        mmdLamp.scale = mathutils.Vector((self.__scale, self.__scale, self.__scale)) * 4.0
        for obj in mmdLamp.children:
            if obj.type == 'LAMP':
                lamp = obj
            elif obj.type == 'ARMATURE':
                armature = obj
                bone = armature.pose.bones[0]
                bone_data_path = 'pose.bones["' + bone.name + '"].location'

        if action_name is not None:
            act = bpy.data.actions.new(name=action_name + '_color')
            a = lamp.data.animation_data_create()
            a.action = act
            act = bpy.data.actions.new(name=action_name + '_location')
            a = armature.animation_data_create()
            a.action = act

        lampAnim = self.__vmdFile.lampAnimation
        for keyFrame in lampAnim:
            lamp.data.color = mathutils.Vector(keyFrame.color)
            bone.location = -(mathutils.Vector((keyFrame.direction[0], keyFrame.direction[2], keyFrame.direction[1])))
            lamp.data.keyframe_insert(data_path='color',
                                      frame=keyFrame.frame_number+self.__frame_margin)
            bone.keyframe_insert(data_path='location',
                                 frame=keyFrame.frame_number+self.__frame_margin)

        for fcurve in armature.animation_data.action.fcurves:
            if fcurve.data_path == bone_data_path:
                self.detectLampChange(fcurve)



    def assign(self, obj, action_name=None):
        if action_name is None:
            action_name = os.path.splitext(os.path.basename(self.__vmdFile.filepath))[0]

        if mmd_camera.MMDCamera.isMMDCamera(obj):
            self.__assignToCamera(obj, action_name+'_camera')
        elif mmd_lamp.MMDLamp.isMMDLamp(obj):
            self.__assignToLamp(obj, action_name+'_lamp')
        elif obj.type == 'MESH':
            self.__assignToMesh(obj, action_name+'_facial')
        elif obj.type == 'ARMATURE':
            self.__assignToArmature(obj, action_name+'_bone')
        elif obj.type == 'CAMERA' and self.__convert_mmd_camera:
            obj = mmd_camera.MMDCamera.convertToMMDCamera(obj)
            self.__assignToCamera(obj.object(), action_name+'_camera')
        elif obj.type == 'LAMP' and self.__convert_mmd_lamp:
            obj = mmd_lamp.MMDLamp.convertToMMDLamp(obj)
            self.__assignToLamp(obj.object(), action_name+'_lamp')
        else:
            pass

