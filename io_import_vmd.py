 # -*- coding: utf-8 -*-
import struct
import collections
import mathutils
import bpy
import math
import re
import os

bl_info= {
    "name": "Import Vocaloid Motion Data file (.vmd)",
    "author": "sugiany",
    "version": (0, 1, 3),
    "blender": (2, 6, 2),
    "location": "File > Import > Import Vocaloid Motion Data file (.vmd)",
    "description": "Import a MikuMikuDance Motion data file (.vmd).",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"}

_MMD_CAMERA_NAME = 'MMD_Camera'

def _toShiftJisString(byteString):
    try:
        eindex = byteString.index(b"\x00")
    except Exception:
        eindex = -1
    if eindex < len(byteString):
        byteString = byteString[0:eindex]
    return byteString.decode("shift_jis")

class BoneFrame:
    def __init__(self, frame, location, rotation, interp):
        self.frame = int(frame)
        self.location = location
        self.rotation = rotation
        self.interp = interp

class ShapeKeyFrame:
    def __init__(self, frame, weight):
        self.frame = int(frame)
        self.weight = float(weight)

class CameraKeyFrame:
    def __init__(self, frame, length, location, rotation, interp, angle, persp):
        self.frame = int(frame)
        self.length = length
        self.location = location
        self.rotation = rotation
        self.interp = interp
        self.angle = angle
        self.persp = persp

class VMDFile:
    def __init__(self):
        self.__signature = ""
        self.__modelname = ""
        self.__bones = {}
        self.__shapes = {}
        self.__camera = []

    def bones(self):
        return self.__bones

    def shapes(self):
        return self.__shapes

    def camera(self):
        return self.__camera

    def load(self, path):
        fin = open(path, 'rb')
        try:
            self.__readHeader(fin)

            motionCount = self.__readCount(fin)
            self.__readMotionKeys(fin, motionCount)

            skinCount = self.__readCount(fin)
            self.__readSkinMotionKeys(fin, skinCount)

            cameraCount = self.__readCount(fin)
            self.__readCameraKeys(fin, cameraCount)
        finally:
            fin.close()

    def __readHeader(self, fin):
        (self.__signature, data) = struct.unpack('<30s20s', fin.read(30+20))
        self.__modelname = _toShiftJisString(data)

    def __readCount(self, fin):
        return int(struct.unpack('<L', fin.read(4))[0])

    def __readMotionKeys(self, fin, num):
        for i in range(num):
            loc = mathutils.Vector()
            rot = mathutils.Quaternion()
            (name, frame, loc.x, loc.y, loc.z, rot.x, rot.y, rot.z, rot.w, interp) = struct.unpack('<15sLfffffff64s', fin.read(15+4+4*3+4*4+64))
            name = _toShiftJisString(name)
            if not name in self.__bones:
                self.__bones[name] = []
            self.__bones[name].append(BoneFrame(frame, loc, rot, interp))

        for i in self.__bones.values():
            i.sort(key=lambda x:x.frame)

    def __readSkinMotionKeys(self, fin, num):
        res = []
        for i in range(num):
            (name, frame, weight) = struct.unpack('<15sLf', fin.read(15+4+4))
            name = _toShiftJisString(name)
            if not name in self.__shapes:
                self.__shapes[name] = []
            self.__shapes[name].append(ShapeKeyFrame(frame, weight))

        for i in self.__shapes.values():
            i.sort(key=lambda x:x.frame)

    def __readCameraKeys(self, fin, num):
        for i in range(num):
            loc = mathutils.Vector()
            rot = mathutils.Vector()
            (frame, length, loc.x, loc.y, loc.z, rot.x, rot.y, rot.z, interp, angle, persp) = struct.unpack('<Lfffffff24sL1s', fin.read(4+4+4*3+4*3+24+4+1))
            self.__camera.append(CameraKeyFrame(frame, length, loc, rot, interp, angle, persp))

        self.__camera.sort(key=lambda x:x.frame)

    def __translateMat(self, bone):
        mat = mathutils.Matrix()
        mat[0][0], mat[1][0], mat[2][0] = bone.x_axis.x, bone.x_axis.y, bone.x_axis.z
        mat[0][1], mat[1][1], mat[2][1] = bone.z_axis.x, bone.z_axis.y, bone.z_axis.z
        mat[0][2], mat[1][2], mat[2][2] = bone.y_axis.x, bone.y_axis.y, bone.y_axis.z
        return mat


def convertVMDBoneLocationToBlender(blender_bone, location):
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

    return mat2 * mat * location

def convertVMDBoneRotationToBlender(blender_bone, rotation):
    mat = mathutils.Matrix()
    mat[0][0], mat[1][0], mat[2][0] = blender_bone.x_axis.x, blender_bone.y_axis.x, blender_bone.z_axis.x
    mat[0][1], mat[1][1], mat[2][1] = blender_bone.x_axis.y, blender_bone.y_axis.y, blender_bone.z_axis.y
    mat[0][2], mat[1][2], mat[2][2] = blender_bone.x_axis.z, blender_bone.y_axis.z, blender_bone.z_axis.z
    (vec, angle) = rotation.to_axis_angle()
    v = mathutils.Vector((-vec.x, -vec.z, -vec.y))
    return mathutils.Quaternion(mat*v, angle)

def defaultNameFilter(name):
    m = re.match('左(.*)$', name)
    if m:
        name = m.group(1) + '_L'
    m = re.match('右(.*)$', name)
    if m:
        name = m.group(1) + '_R'
    return name

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
