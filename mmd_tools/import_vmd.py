 # -*- coding: utf-8 -*-
import struct
import collections
import mathutils
import bpy
import math
import re
import os



class VMDImporter:
    def __init__(self, filepath, scale=1.0, use_pmx_bonename=True):
        self.__vmdFile = vmd.File()
        self.__vmdFile.load(filepath)
        self.__scale = scale
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
        mat = mathutils.Matrix()
        mat[0][0], mat[1][0], mat[2][0] = blender_bone.x_axis.x, blender_bone.y_axis.x, blender_bone.z_axis.x
        mat[0][1], mat[1][1], mat[2][1] = blender_bone.x_axis.y, blender_bone.y_axis.y, blender_bone.z_axis.y
        mat[0][2], mat[1][2], mat[2][2] = blender_bone.x_axis.z, blender_bone.y_axis.z, blender_bone.z_axis.z
        (vec, angle) = rotation.to_axis_angle()
        v = mathutils.Vector((-vec.x, -vec.z, -vec.y))
        return mathutils.Quaternion(mat*v, angle)

    @staticmethod
    def __fixRotations(rotation_ary):
        rotation_ary = list(rotation_ary)
        if len(rotation_ary) == 0:
            return rotation_ary

        pq = rotation_ary.pop(0)
        res = [pq]
        for q in rotation_ary:
            nq = -q
            t1 = (pq.w-q.w)**2+(pq.x-q.x)**2+(pq.y-q.y)**2+(pq.z-q.z)**2
            t2 = (pq.w-nq.w)**2+(pq.x-nq.x)**2+(pq.y-nq.y)**2+(pq.z-nq.z)**2
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
            a = meshObj.animation_data_create()
            a.action = act

        boneAnim = self._vmdFile.boneAnimation

        pose_bones = armObj.pose.bones
        if self.__use_pmx_bonename:
            pose_bones = utils.makePmxBoneMap(pose_bones)
        for name, keyFrames in boneAnim.items():
            if name not in pose.bones.keys():
                print("WARINIG: not found bone %s"%str(name))
                continue

            bone = pose_bones[name]
            frameNumbers = map(lambda x: x.frame_number, keyFrames)
            mat = makeVMDBoneLocationToBlenderMatrix(bone)
            locations = map(lambda x: mat * x.location, keyFrames)
            rotations = map(lambda x: convertVMDBoneRotationToBlender(bone, x.rotation), keyFrames)
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
            a = meshObj.animation_data_create()
            a.action = act

        shapeKeyAnim = self.__vmdFile.shapeKeyAnimation

        shapeKeyDict = {}
        for i in obj.data.shape_keys.key_blocks:
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


    def __assignToCamera(self, cameraObj):
        pass

    def assign(self, obj):
        if obj.type == 'MESH':
            self.__assignToMesh(obj)
        elif obj.type == 'ARMATURE':
            self.__assignToArmature(self, obj)
        elif utils.MMDCamera.isMMDCamera(obj):
            self.__assignToCamera(self, obj)
        else:
            raise ValueError('unsupport object type: %s'%obj.type)        



def fixRotations(rotation_ary):
    rotation_ary = list(rotation_ary)
    if len(rotation_ary) == 0:
        return rotation_ary

    pq = rotation_ary.pop(0)
    res = [pq]
    for q in rotation_ary:
        nq = -q
        t1 = (pq.w-q.w)**2+(pq.x-q.x)**2+(pq.y-q.y)**2+(pq.z-q.z)**2
        t2 = (pq.w-nq.w)**2+(pq.x-nq.x)**2+(pq.y-nq.y)**2+(pq.z-nq.z)**2
        if t2 < t1:
            res.append(nq)
            pq = nq
        else:
            res.append(q)
            pq = q
    return res

def assignSelectedObject(obj, vmd_file, scale=0.2, frame_offset=0, name_filter=lambda x: x):

    arm = obj.data
    pose = obj.pose
    for name, frames in vmd_file.bones().items():
        name = name_filter(name)
        if name not in pose.bones.keys():
            print("WARINIG: not found bone %s"%str(name))
            continue
        bone = pose.bones[name]

        frameNumbers = map(lambda x: x.frame, frames)
        locations = map(lambda x: convertVMDBoneLocationToBlender(bone, x.location) * scale, frames)
        rotations = map(lambda x: convertVMDBoneRotationToBlender(bone, x.rotation), frames)

        rotations = fixRotations(rotations)
        for frame, location, rotation in zip(frameNumbers, locations, rotations):
            bone.location = location
            bone.rotation_quaternion = rotation
            bone.keyframe_insert(data_path='location',
                                 group=name,
                                 frame=frame+frame_offset)
            bone.keyframe_insert(data_path='rotation_quaternion',
                                 group=name,
                                 frame=frame+frame_offset)

def assignShapeKeys(obj, vmd_file, frame_offset=0, action_name=''):
    linkActionForShapeKey(action_name+'_shape', [obj])
    shapeKeyDict = {}
    for i in obj.data.shape_keys.key_blocks:
        shapeKeyDict[i.name] = i

    for name, frames in vmd_file.shapes().items():
        if name not in shapeKeyDict:
            print("WARINIG: not found bone %s"%str(name))
            continue
        shapeKey = shapeKeyDict[name]
        for frame, weight in map(lambda x: (x.frame, x.weight), frames):
            shapeKey.value = weight
            shapeKey.keyframe_insert(data_path='value',
                                     group=name,
                                     frame=frame+frame_offset)

def createMMDCamera(camera):
    empty = bpy.data.objects.new(_MMD_CAMERA_NAME, None)
    empty.rotation_mode = 'XYZ'
    camera.data.sensor_fit = 'AUTO'
    camera.location = mathutils.Vector((0,0,0))
    camera.rotation_mode = 'XYZ'
    camera.rotation_euler = mathutils.Vector((0,0,0))
    camera.parent = empty
    bpy.context.scene.objects.link(empty)
    return camera

def detectSceneChange(fcurve, threshold):
    frames = list(fcurve.keyframe_points)
    frameCount = len(frames)
    frames.sort(key=lambda x:x.co[0])
    for i, f in enumerate(frames):
        if i+1 < frameCount:
            n = frames[i+1]
            if n.co[0] - f.co[0] <= 1.0 and abs(f.co[1] - n.co[1]) > threshold:
                f.interpolation = 'CONSTANT'


def assignCameraMotion(camera, vmd_file, scale=0.2, frame_offset=0, cut_detection_threshold=0.5, action_name=''):
    if camera.parent is None or camera.parent.name != _MMD_CAMERA_NAME:
        camera = createMMDCamera(camera)
    cameraFrames = vmd_file.camera()
    frameCount = len(cameraFrames)
    linkAction(action_name+'_cam',  [camera])
    linkAction(action_name+'_came',  [camera.parent])

    camera.data.sensor_fit='VERTICAL'
    d = camera.data.sensor_height

    for n, i in enumerate(cameraFrames):

        camera.data.lens = d/(2*math.tan(math.radians(i.angle)/2))
        camera.location = mathutils.Vector((0, 0, -i.length)) * scale
        camera.parent.location = mathutils.Vector((i.location.x, i.location.z, i.location.y)) * scale
        camera.parent.rotation_euler = mathutils.Vector((i.rotation.x+math.radians(90.0), i.rotation.z, i.rotation.y))
        camera.data.keyframe_insert(data_path='lens',
                                    frame=i.frame+frame_offset)
        camera.keyframe_insert(data_path='location',
                               frame=i.frame+frame_offset)
        camera.parent.keyframe_insert(data_path='location',
                                      frame=i.frame+frame_offset)
        camera.parent.keyframe_insert(data_path='rotation_euler',
                                      frame=i.frame+frame_offset)

    for fcurve in camera.parent.animation_data.action.fcurves:
        if fcurve.data_path == 'rotation_euler':
            detectSceneChange(fcurve, cut_detection_threshold)

def linkAction(name, objects):
    act = bpy.data.actions.new(name=name)
    for i in objects:
        a = i.animation_data_create()
        a.action = act

def linkActionForShapeKey(name, objects):
    act = bpy.data.actions.new(name=name)
    for i in objects:
        a = i.data.shape_keys.animation_data_create()
        a.action = act

def execute():
    #filepath = 'D:/primary/program files/MMD/MikuMikuDance_v739dot/UserFile/Motion/Yellowモーションせっと2/Yellowモーションデータ.vmd'
    filepath = 'D:/primary/program files/MMD/MikuMikuDance_v739dot/UserFile/Motion/DMC3-romecin/test.vmd'
    enabled_bone_key = True
    enabled_shape_key = True
    enabled_camera_key = True
    scale = 1.0
    frameOffset = 0

    vmd = VMDFile()
    vmd.load(filepath)

    actionName = os.path.splitext(os.path.basename(filepath))[0]

    armature = None
    for i in bpy.context.selected_objects:
        if i.type == 'ARMATURE':
            armature = i
            break
    if enabled_bone_key and armature is not None:
        linkAction(actionName+'_arm',  [armature])
        assignSelectedObject(armature, vmd, scale=scale, frame_offset=frameOffset)

    mesh = None
    for i in bpy.context.selected_objects:
        if i.type == 'MESH':
            mesh = i
            break

    if enabled_shape_key and mesh is not None:
        assignShapeKeys(mesh, vmd, frame_offset=frameOffset, action_name=actionName)

    camera = None
    try:
        for i in bpy.data.objects[_MMD_CAMERA_NAME].children:
            if i.type == 'CAMERA':
                camera = i
                break
    except KeyError:
        for i in bpy.context.selected_objects:
            if i.type == 'CAMERA':
                camera = i
                break

    if enabled_camera_key and camera is not None:
        assignCameraMotion(camera, vmd, scale=scale, frame_offset=frameOffset, action_name=actionName)
