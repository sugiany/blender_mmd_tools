 # -*- coding: utf-8 -*-
import struct
import collections
import mathutils
import bpy
import math
import re
import os

import vmd
import mmd_camera
import utils

class VMDImporter:
    def __init__(self, filepath, scale=1.0, use_pmx_bonename=True, convert_mmd_camera=True):
        self.__vmdFile = vmd.File()
        self.__vmdFile.load(filepath=filepath)
        self.__scale = scale
        self.__convert_mmd_camera = convert_mmd_camera
        self.__use_pmx_bonename = use_pmx_bonename


    @staticmethod
    def makeVMDBoneLocationToBlenderMatrix(blender_bone):
        mat = mathutils.Matrix([
                [blender_bone.x_axis.x, blender_bone.y_axis.x, blender_bone.z_axis.x, 0.0],
                [blender_bone.x_axis.y, blender_bone.y_axis.y, blender_bone.z_axis.y, 0.0],
                [blender_bone.x_axis.z, blender_bone.y_axis.z, blender_bone.z_axis.z, 0.0],
                [0.0, 0.0, 0.0, 1.0]
                ])
        mat2 = mathutils.Matrix([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]])
        return mat2 * mat

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

    def __assignToArmature(self, armObj, action_name=None):
        if action_name is not None:
            act = bpy.data.actions.new(name=action_name)
            a = armObj.animation_data_create()
            a.action = act

        boneAnim = self.__vmdFile.boneAnimation

        pose_bones = armObj.pose.bones
        if self.__use_pmx_bonename:
            pose_bones = utils.makePmxBoneMap(armObj)
        for name, keyFrames in boneAnim.items():
            if name not in pose_bones:
                print("WARINIG: not found bone %s"%str(name))
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
                                     frame=frame)
                bone.keyframe_insert(data_path='rotation_quaternion',
                                     group=name,
                                     frame=frame)


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
                print("WARINIG: not found bone %s"%str(name))
                continue
            shapeKey = shapeKeyDict[name]
            for i in keyFrames:
                shapeKey.value = i.weight
                shapeKey.keyframe_insert(data_path='value',
                                         group=name,
                                         frame=i.frame_number)

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
        mmdCamera = mmd_camera.MMDCamera.convertToMMDCamera(cameraObj).object()
        if action_name is not None:
            act = bpy.data.actions.new(name=action_name)
            a = mmdCamera.animation_data_create()
            a.action = act

        cameraAnim = self.__vmdFile.cameraAnimation
        for keyFrame in cameraAnim:
            mmdCamera.mmd_camera_angle = keyFrame.angle
            mmdCamera.mmd_camera_distance = -keyFrame.distance * self.__scale
            mmdCamera.location = mathutils.Vector((keyFrame.location[0], keyFrame.location[2], keyFrame.location[1])) * self.__scale
            mmdCamera.rotation_euler = mathutils.Vector((keyFrame.rotation[0], keyFrame.rotation[2], keyFrame.rotation[1]))
            mmdCamera.keyframe_insert(data_path='mmd_camera_angle',
                                           frame=keyFrame.frame_number)
            mmdCamera.keyframe_insert(data_path='mmd_camera_distance',
                                      frame=keyFrame.frame_number)
            mmdCamera.keyframe_insert(data_path='location',
                                      frame=keyFrame.frame_number)
            mmdCamera.keyframe_insert(data_path='rotation_euler',
                                      frame=keyFrame.frame_number)

        for fcurve in mmdCamera.animation_data.action.fcurves:
            if fcurve.data_path == 'rotation_euler':
                self.detectCameraChange(fcurve)



    def assign(self, obj, action_name=None):
        if action_name is None:
            action_name = os.path.splitext(os.path.basename(self.__vmdFile.filepath))[0]
        if obj.type == 'MESH':
            self.__assignToMesh(obj, action_name+'_facial')
        elif obj.type == 'ARMATURE':
            self.__assignToArmature(obj, action_name+'_bone')
        elif mmd_camera.MMDCamera.isMMDCamera(obj):
            self.__assignToCamera(obj, action_name+'_camera')
        elif obj.type == 'CAMERA' and self.__convert_mmd_camera:
            obj = mmd_camera.MMDCamera.convertToMMDCamera(obj)
            self.__assignToCamera(obj.object(), action_name+'_camera')
        else:
            raise ValueError('unsupport object type: %s'%obj.type)


def main():
    vmd_importer = VMDImporter("D:/primary/program files/MMD/MikuMikuDance_v739dot/UserFile/Motion/Yellowモーションせっと2/Yellowモーションデータ.vmd", scale=0.2)
    for i in bpy.context.selected_objects:
        vmd_importer.assign(i)
    #vmdFile.load(filepath='/Users/yoshinobu/cg/tmp/import_vmd/scenes/Yellow.vmd')

