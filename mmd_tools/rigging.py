# -*- coding: utf-8 -*-

import bpy

import re

def isRigidBodyObject(obj):
    return obj.is_mmd_rigid and not (obj.is_mmd_rigid_track_target or obj.is_mmd_spring_goal or obj.is_mmd_spring_joint)

def isJointObject(obj):
    return obj.is_mmd_joint

def isTemporaryObject(obj):
    return obj.is_mmd_rigid_track_target or obj.is_mmd_spring_goal or obj.is_mmd_spring_joint or obj.is_mmd_non_collision_constraint

def findRididBodyObjects():
    return filter(isRigidBodyObject, bpy.context.scene.objects)

def findJointObjects():
    return filter(isJointObject, bpy.context.scene.objects)

def findTemporaryObjects():
    return filter(isTemporaryObject, bpy.context.scene.objects)


