# -*- coding: utf-8 -*-

import bpy

def setupFrameRanges():
    s, e = 1, 1
    for i in bpy.data.actions:
        ts, te = i.frame_range
        s = min(s, ts)
        e = max(e, te)
    bpy.context.scene.frame_start = s
    bpy.context.scene.frame_end = e
    bpy.context.scene.rigidbody_world.point_cache.frame_start = s
    bpy.context.scene.rigidbody_world.point_cache.frame_end = e

def setupLighting():
    bpy.context.scene.world.light_settings.use_ambient_occlusion = True
    bpy.context.scene.world.light_settings.use_environment_light = True
    bpy.context.scene.world.light_settings.use_indirect_light = True

def setupFps():
    bpy.context.scene.render.fps = 30
    bpy.context.scene.render.fps_base = 1

def setupGLSLView(area):
    area.spaces[0].viewport_shade='TEXTURED'
    bpy.context.scene.game_settings.material_mode = 'GLSL'
    bpy.ops.object.lamp_add(type='HEMI', view_align=False, location=(0, 0, 0), rotation=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))

