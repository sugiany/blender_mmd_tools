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

def addon_preferences(attrname, default=None):
    addon = bpy.context.user_preferences.addons.get(__package__, None)
    return getattr(addon.preferences, attrname, default) if addon else default

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

def duplicateObject(obj, total_len):
    for i in bpy.context.selected_objects:
        i.select = False
    obj.select = True
    assert(len(bpy.context.selected_objects) == 1)
    assert(bpy.context.selected_objects[0] == obj)
    last_selected = objs = [obj]
    while len(objs) < total_len:
        bpy.ops.object.duplicate()
        objs.extend(bpy.context.selected_objects)
        remain = total_len - len(objs) - len(bpy.context.selected_objects)
        if remain < 0:
            last_selected = bpy.context.selected_objects
            for i in range(-remain):
                last_selected[i].select = False
        else:
            for i in range(min(remain, len(last_selected))):
                last_selected[i].select = True
        last_selected = bpy.context.selected_objects
    assert(len(objs) == total_len)
    return objs

def makeCapsuleBak(segment=16, ring_count=8, radius=1.0, height=1.0, target_scene=None):
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

def createObject(name='Object', object_data=None, target_scene=None):
    if target_scene is None:
        target_scene = bpy.context.scene
    obj = bpy.data.objects.new(name=name, object_data=object_data)
    target_scene.objects.link(obj)
    target_scene.objects.active = obj
    obj.select = True
    return obj

def makeSphere(segment=8, ring_count=5, radius=1.0, target_object=None):
    import bmesh
    if target_object is None:
        target_object = createObject(name='Sphere')

    mesh = target_object.data
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm,
        u_segments=segment,
        v_segments=ring_count,
        diameter=radius,
        )
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    return target_object

def makeBox(size=(1,1,1), target_object=None):
    import bmesh
    from mathutils import Matrix
    if target_object is None:
        target_object = createObject(name='Box')

    mesh = target_object.data
    bm = bmesh.new()
    bmesh.ops.create_cube(
        bm,
        size=2,
        matrix=Matrix([[size[0],0,0,0], [0,size[1],0,0], [0,0,size[2],0], [0,0,0,1]]),
        )
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    return target_object

def makeCapsule(segment=8, ring_count=2, radius=1.0, height=1.0, target_object=None):
    import bmesh
    import math
    if target_object is None:
        target_object = createObject(name='Capsule')
    height = max(height, 1e-3)

    mesh = target_object.data
    bm = bmesh.new()
    verts = bm.verts
    top = (0, 0, height/2+radius)
    verts.new(top)

    #f = lambda i: radius*i/ring_count
    f = lambda i: radius*math.sin(0.5*math.pi*i/ring_count)
    for i in range(ring_count, 0, -1):
        z = f(i-1)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            verts.new((x,y,z+height/2))

    for i in range(ring_count):
        z = -f(i)
        t = math.sqrt(radius**2 - z**2)
        for j in range(segment):
            theta = 2*math.pi/segment*j
            x = t * math.sin(-theta)
            y = t * math.cos(-theta)
            verts.new((x,y,z-height/2))

    bottom = (0, 0, -(height/2+radius))
    verts.new(bottom)
    if hasattr(verts, 'ensure_lookup_table'):
        verts.ensure_lookup_table()

    faces = bm.faces
    for i in range(1, segment):
        faces.new([verts[x] for x in (0, i, i+1)])
    faces.new([verts[x] for x in (0, segment, 1)])
    offset = segment + 1
    for i in range(ring_count*2-1):
        for j in range(segment-1):
            t = offset + j
            faces.new([verts[x] for x in (t-segment, t, t+1, t-segment+1)])
        faces.new([verts[x] for x in (offset-1, offset+segment-1, offset, offset-segment)])
        offset += segment
    for i in range(segment-1):
        t = offset + i
        faces.new([verts[x] for x in (t-segment, offset, t-segment+1)])
    faces.new([verts[x] for x in (offset-1, offset, offset-segment)])

    for f in bm.faces:
        f.smooth = True
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    return target_object

