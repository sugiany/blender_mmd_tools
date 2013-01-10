import bpy
import mathutils
import math

from . import utils

class MMDLamp:
    def __init__(self, obj):
        if obj.type != 'EMPTY':
            if obj.parent is None or not obj.type in ['LAMP', 'ARMATURE']:
                raise ValueError('%s is not MMDLamp'%str(obj))
            obj = obj.parent
        if obj.type == 'EMPTY' and obj.get('is_mmd_lamp', False):
            self.__emptyObj = obj
        else:
            raise ValueError('%s is not MMDLamp'%str(obj))


    @staticmethod
    def isMMDLamp(obj):
        if obj.type != 'EMPTY':
            if obj.parent is None or not obj.type in ['LAMP', 'ARMATURE']:
                return False
            obj = obj.parent
        return obj.type == 'EMPTY' and obj.get('is_mmd_lamp', False)


    @staticmethod
    def __setConstraints(empty, armature, poseBone, lamp):
        constraints = lamp.constraints

        constraint = constraints.new(type='COPY_LOCATION')
        constraint.name = 'mmd_lamp_location'
        constraint.target = armature
        constraint.subtarget = poseBone.name

        constraint = constraints.new(type='TRACK_TO')
        constraint.name = 'mmd_lamp_track'
        constraint.target = empty
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'

        constraints = poseBone.constraints

        constraint = constraints.new(type='TRACK_TO')
        constraint.name = 'mmd_lamp_track'
        constraint.target = empty
        constraint.track_axis = 'TRACK_NEGATIVE_Y'
        constraint.up_axis = 'UP_Z'


    @staticmethod
    def convertToMMDLamp(lampObj):
        import bpy
        import mathutils
        if MMDLamp.isMMDLamp(lampObj):
            return MMDLamp(lampObj)

        name = lampObj.name + '_mmd_target'
        empty = bpy.data.objects.new(name=name, object_data=None)
        bpy.context.scene.objects.link(empty)

        name = lampObj.name + '_mmd_source'
        armature = bpy.data.armatures.new(name=name)
        armatureObj = bpy.data.objects.new(name=name, object_data=armature)
        bpy.context.scene.objects.link(armatureObj)

        utils.enterEditMode(armatureObj)
        bone = armature.edit_bones.new(name='handle')
        bone.head = mathutils.Vector((0,0,0))
        bone.tail = mathutils.Vector((0,0.2,0))
        bpy.ops.object.mode_set(mode='POSE')

        empty.rotation_mode = 'XYZ'
        empty.is_mmd_lamp = True

        armatureObj.parent = empty
        armatureObj.location = mathutils.Vector((0,0,0))
        armatureObj.rotation_mode = 'XYZ'
        armatureObj.rotation_euler = mathutils.Vector((0,0,0))
        armatureObj.scale = mathutils.Vector((4.0, 4.0, 4.0))
        armatureObj.lock_location = (True, True, True)
        armatureObj.lock_rotation = (True, True, True)
        armatureObj.lock_scale = (False, False, False)
        armatureObj.draw_type = 'WIRE'
        armature.draw_type = 'BBONE'

        poseBone = armatureObj.pose.bones[0]
        poseBone.location =  mathutils.Vector((0,0,0))
        poseBone.rotation_mode = 'QUATERNION'
        poseBone.rotation_quaternion = mathutils.Quaternion((1,0,0,0))
        poseBone.scale =  mathutils.Vector((0.2,1.0,0.2))
        poseBone.lock_location = (False, False, False)
        poseBone.lock_rotation = (True, True, True)
        poseBone.lock_rotations_4d = False
        poseBone.lock_scale = (False, False, False)

        lampObj.parent = empty
        lampObj.location = mathutils.Vector((0,0,0))
        lampObj.rotation_mode = 'XYZ'
        lampObj.rotation_euler = mathutils.Vector((0,0,0))

        MMDLamp.__setConstraints(empty, armatureObj, poseBone, lampObj)

        return MMDLamp(empty)

    def object(self):
        return self.__emptyObj

