# -*- coding: utf-8 -*-

__properties = {}

import bpy

def register_property(bpy_type=None, attrname=None):
    def _func(cls):
        global __properties

        if bpy_type not in __properties:
            __properties[bpy_type] = []
        if attrname in [ x[0] for x in __properties[bpy_type]]:
            raise ValueError
        __properties[bpy_type].append((attrname, cls))
        return cls
    return _func


def register():
    for typ, props in __properties.items():
        for attr, cls in props:
            prop = bpy.props.PointerProperty(type=cls)
            setattr(typ, attr, prop)

def unregister():
    for typ, t in __properties.items():
        for attr, cls in t:
            delattr(typ, attr)

from . import root, camera, material, bone, rigid_body
