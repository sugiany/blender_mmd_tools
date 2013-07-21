# -*- coding: utf-8 -*-

import bpy

class __EditMode:
    def __init__(self, obj):
        if not isinstance(obj, bpy.types.Object):
            raise ValueError
        self.__prevMode = obj.mode
        self.__obj = obj
        select_object(obj)
        if obj.mode != 'EIDT':
            bpy.ops.object.mode_set(mode='EDIT')

    def __enter__(self):
        return self.__obj.data

    def __exit__(self, type, value, traceback):
        bpy.ops.object.mode_set(mode=self.__prevMode)


def select_object(obj):
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active = obj
    obj.select=True


def edit_object(obj):
    """ Set the object interaction mode to 'EDIT'

    It is recommended to use 'edit_object' with 'with' statement like the following code.
    @code{.py}
    with edit_object:
        some functions...
    @endcode
    """
    return __EditMode(obj)

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
