# -*- coding: utf-8 -*-

import bpy

class __EditMode:
    def __init__(self, obj):
        if not isinstance(obj, bpy.types.Object):
            raise ValueError
        self.__prevMode = obj.mode
        self.__obj = obj
        with select_object(obj) as act_obj:
            if obj.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

    def __enter__(self):
        return self.__obj.data

    def __exit__(self, type, value, traceback):
        bpy.ops.object.mode_set(mode=self.__prevMode)

class __SelectObjects:
    def __init__(self, active_object, selected_objects=[]):
        if not isinstance(active_object, bpy.types.Object):
            raise ValueError
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        for i in bpy.context.selected_objects:
            i.select = False

        self.__active_object = active_object
        self.__selected_objects = [active_object]+selected_objects

        self.__hides = []
        for i in self.__selected_objects:
            self.__hides.append(i.hide)
            i.hide = False
            i.select = True
        bpy.context.scene.objects.active = active_object

    def __enter__(self):
        return self.__active_object

    def __exit__(self, type, value, traceback):
        for i, j in zip(self.__selected_objects, self.__hides):
            i.hide = j

def setParent(obj, parent):
    ho = obj.hide
    hp = parent.hide
    obj.hide = False
    parent.hide = False
    select_object(parent)
    obj.select = True
    bpy.ops.object.parent_set(type='OBJECT', xmirror=False, keep_transform=False)
    obj.hide = ho
    parent.hide = hp

def setParentToBone(obj, parent, bone_name):
    import bpy
    select_object(parent)
    bpy.ops.object.mode_set(mode='POSE')
    select_object(obj)
    bpy.context.scene.objects.active = parent
    parent.select = True
    bpy.ops.object.mode_set(mode='POSE')
    parent.data.bones.active = parent.data.bones[bone_name]
    bpy.ops.object.parent_set(type='BONE', xmirror=False, keep_transform=False)
    bpy.ops.object.mode_set(mode='OBJECT')

def edit_object(obj):
    """ Set the object interaction mode to 'EDIT'

     It is recommended to use 'edit_object' with 'with' statement like the following code.

        with edit_object:
            some functions...
    """
    return __EditMode(obj)

def select_object(obj, objects=[]):
    """ Select objects.

     It is recommended to use 'select_object' with 'with' statement like the following code.
     This function can select "hidden" objects safely.

        with select_object(obj):
            some functions...
    """
    return __SelectObjects(obj, objects)

def makeCapsule(segment=16, ring_count=8, radius=1.0, height=1.0, target_scene=None):
    import math
    if target_scene is None:
        target_scene = bpy.context.scene
    mesh = bpy.data.meshes.new(name='Capsule')
    meshObj = bpy.data.objects.new(name='Capsule', object_data=mesh)
    vertices = []
    top = (0, 0, height/2+radius)
    vertices.append(top)

    f = lambda i: radius*i/ring_count
    for i in range(ring_count, 0, -1):
        z = f(i-1)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            vertices.append((x,y,z+height/2))

    for i in range(ring_count):
        z = -f(i)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            vertices.append((x,y,z-height/2))

    bottom = (0, 0, -(height/2+radius))
    vertices.append(bottom)

    faces = []
    for i in range(1, segment):
        faces.append([0, i, i+1])
    faces.append([0, segment, 1])
    offset = segment + 1
    for i in range(ring_count*2-1):
        for j in range(segment-1):
            t = offset + j
            faces.append([t-segment, t, t+1, t-segment+1])
        faces.append([offset-1, offset+segment-1, offset, offset-segment])
        offset += segment
    for i in range(segment-1):
        t = offset + i
        faces.append([t-segment, offset, t-segment+1])
    faces.append([offset-1, offset, offset-segment])

    mesh.from_pydata(vertices, [], faces)
    target_scene.objects.link(meshObj)
    return meshObj
