# -*- coding: utf-8 -*-
import mathutils
import bpy
import math
import re
import os

import mmd_tools.core.camera as mmd_camera
import mmd_tools.core.lamp as mmd_lamp
import mmd_tools.core.vmd as vmd
from mmd_tools import utils

class VMDImporter:
    def __init__(self, filepath, scale=1.0, use_pmx_bonename=True, convert_mmd_camera=True, convert_mmd_lamp=True, frame_margin=5):
        self.__vmdFile = vmd.File()
        self.__vmdFile.load(filepath=filepath)
        self.__scale = scale
        self.__convert_mmd_camera = convert_mmd_camera
        self.__convert_mmd_lamp = convert_mmd_lamp
        self.__use_pmx_bonename = use_pmx_bonename
        self.__frame_margin = frame_margin + 1


    @staticmethod
    def makeVMDBoneLocationToBlenderMatrix(blender_bone):
        mat = mathutils.Matrix([
                [blender_bone.x_axis.x, blender_bone.x_axis.y, blender_bone.x_axis.z, 0.0],
                [blender_bone.y_axis.x, blender_bone.y_axis.y, blender_bone.y_axis.z, 0.0],
                [blender_bone.z_axis.x, blender_bone.z_axis.y, blender_bone.z_axis.z, 0.0],
                [0.0, 0.0, 0.0, 1.0]
                ])
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
        mat = mathutils.Matrix()
        mat[0][0], mat[1][0], mat[2][0] = blender_bone.x_axis.x, blender_bone.y_axis.x, blender_bone.z_axis.x
        mat[0][1], mat[1][1], mat[2][1] = blender_bone.x_axis.y, blender_bone.y_axis.y, blender_bone.z_axis.y
        mat[0][2], mat[1][2], mat[2][2] = blender_bone.x_axis.z, blender_bone.y_axis.z, blender_bone.z_axis.z
        (vec, angle) = rotation.to_axis_angle()
        v = mathutils.Vector((-vec.x, -vec.z, -vec.y))
        return mathutils.Quaternion(mat*v, angle).normalized()

    @staticmethod
    def __fixRotations(rotation_ary):
        rotation_ary = list(rotation_ary)
        if len(rotation_ary) == 0:
            return rotation_ary

        pq = rotation_ary.pop(0)
        res = [pq]
        for q in rotation_ary:
            nq = q.copy()
            nq.negate()
            t1 = (pq.w-q.w)**2+(pq.x-q.x)**2+(pq.y-q.y)**2+(pq.z-q.z)**2
            t2 = (pq.w-nq.w)**2+(pq.x-nq.x)**2+(pq.y-nq.y)**2+(pq.z-nq.z)**2
            # t1 = pq.axis.dot(q.axis)
            # t2 = pq.axis.dot(nq.axis)
            if t2 < t1:
                res.append(nq)
                pq = nq
            else:
                res.append(q)
                pq = q
        return res

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

        if self.__frame_margin > 1:
            utils.selectAObject(armObj)
            bpy.context.scene.frame_current = 1
            bpy.ops.object.mode_set(mode='POSE')
            hiddenBones = []
            for i in armObj.data.bones:
                if i.hide:
                    hiddenBones.append(i)
                    i.hide = False
                i.select = True
            bpy.ops.pose.transforms_clear()
            bpy.ops.anim.keyframe_insert_menu(type='LocRotScale', confirm_success=False, always_prompt=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            for i in hiddenBones:
                i.hide = True
            
        boneAnim = self.__vmdFile.boneAnimation

        pose_bones = armObj.pose.bones
        if self.__use_pmx_bonename:
            pose_bones = utils.makePmxBoneMap(armObj)
        for name, keyFrames in boneAnim.items():
            if name not in pose_bones:
                print("WARNING: not found bone %s"%str(name))
                continue

            keyFrames.sort(key=lambda x:x.frame_number)
            bone = pose_bones[name]
            frameNumbers = map(lambda x: x.frame_number, keyFrames)
            mat = self.makeVMDBoneLocationToBlenderMatrix(bone)
            locations = map(lambda x: mat * mathutils.Vector(x.location) * self.__scale, keyFrames)
            rotations = map(lambda x: self.convertVMDBoneRotationToBlender(bone, x.rotation), keyFrames)
            rotations = self.__fixRotations(rotations)

            for frame, location, rotation in zip(frameNumbers, locations, rotations):
                bone.location = location
                bone.rotation_quaternion = rotation
                bone.keyframe_insert(data_path='location',
                                     group=name,
                                     frame=frame+self.__frame_margin)
                bone.keyframe_insert(data_path='rotation_quaternion',
                                     group=name,
                                     frame=frame+self.__frame_margin)

        rePath = re.compile(r'^pose\.bones\["(.+)"\]\.([a-z_]+)$')
        for fcurve in act.fcurves:
            m = rePath.match(fcurve.data_path)
            if m and m.group(2) in ['location', 'rotation_quaternion']:
                bone = armObj.pose.bones[m.group(1)]
                keyFrames = boneAnim[bone.get('name_j', bone.name)]
                if m.group(2) == 'location':
                    idx = [0, 2, 1][fcurve.array_index]
                else:
                    idx = 3
                frames = list(fcurve.keyframe_points)
                frames.sort(key=lambda kp:kp.co.x)
                if self.__frame_margin > 1:
                    del frames[0]
                for i in range(1, len(keyFrames)):
                    self.__setInterpolation(keyFrames[i].interp[idx:16:4], frames[i - 1], frames[i])

    def __assignToMesh(self, meshObj, action_name=None):
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
                print("WARNING: not found shape key %s"%str(name))
                continue
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
        for keyFrame in cameraAnim:
            mmdCamera.mmd_camera.angle = math.radians(keyFrame.angle)
            cameraObj.location[1] = keyFrame.distance * self.__scale
            mmdCamera.location = mathutils.Vector((keyFrame.location[0], keyFrame.location[2], keyFrame.location[1])) * self.__scale
            mmdCamera.rotation_euler = mathutils.Vector((keyFrame.rotation[0], keyFrame.rotation[2], keyFrame.rotation[1]))
            mmdCamera.keyframe_insert(data_path='mmd_camera.angle',
                                           frame=keyFrame.frame_number+self.__frame_margin)
            cameraObj.keyframe_insert(data_path='location', index=1,
                                      frame=keyFrame.frame_number+self.__frame_margin)
            mmdCamera.keyframe_insert(data_path='location',
                                      frame=keyFrame.frame_number+self.__frame_margin)
            mmdCamera.keyframe_insert(data_path='rotation_euler',
                                      frame=keyFrame.frame_number+self.__frame_margin)

        paths = ['rotation_euler', 'mmd_camera.angle', 'location']
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

