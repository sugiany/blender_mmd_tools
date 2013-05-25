# -*- coding: utf-8 -*-

import bpy


class __EditMode:
    def __init__(self, obj):
        if not isinstance(obj, bpy.types.Object):
            raise ValueError
        self.__prevMode = obj.mode
        select_object(obj)
        if obj.mode != 'EIDT':
            bpy.ops.object.mode_set(mode='EDIT')

    def __enter__(self):
        return self

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
