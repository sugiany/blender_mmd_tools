# -*- coding: utf-8 -*-

import math

import bpy
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, BoolProperty

from mmd_tools import mmd_camera
from . import register_property


def _getMMDCameraAngle(prop):
    empty = prop.id_data
    cam = mmd_camera.MMDCamera(empty).camera()
    return math.atan(cam.data.sensor_height/cam.data.lens/2) * 2

def _setMMDCameraAngle(prop, value):
    empty = prop.id_data
    cam = mmd_camera.MMDCamera(empty).camera()
    cam.data.lens = cam.data.sensor_height/math.tan(value/2)/2


@register_property(bpy.types.Object, 'mmd_camera')
class MMDCamera(PropertyGroup):
    angle = FloatProperty(
        name='Angle',
        subtype='ANGLE',
        get=_getMMDCameraAngle,
        set=_setMMDCameraAngle,
        min=0.1,
        max=math.radians(180),
        step=0.1,
        )

    is_perspective = BoolProperty(
        name='Perspective',
        default=True,
        )
