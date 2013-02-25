# -*- coding: utf-8 -*-
import bpy

def create_MMDBasicShader():
    bpy.context.scene.render.engine = 'CYCLES'

    if 'MMDBasicShader' in bpy.data.node_groups:
        return bpy.data.node_groups['MMDBasicShader']

    shader = bpy.data.node_groups.new(name='MMDBasicShader', type='SHADER')

    dif = shader.nodes.new('BSDF_DIFFUSE')
    glo = shader.nodes.new('BSDF_GLOSSY')
    mix = shader.nodes.new('MIX_SHADER')

    shader.links.new(mix.inputs[1], dif.outputs['BSDF'])
    shader.links.new(mix.inputs[2], glo.outputs['BSDF'])

    shader.inputs.expose(dif.inputs['Color'], True).name = 'diffuse'
    shader.inputs.expose(glo.inputs['Color'], True).name = 'glossy'
    shader.inputs.expose(glo.inputs['Roughness'], True).name = 'glossy_rough'
    shader.inputs.expose(mix.inputs['Fac'], True).name = 'reflection'
    shader.outputs.expose(mix.outputs['Shader'], True).name = 'shader'

    shader.inputs['diffuse'].default_value = [1.0, 1.0, 1.0, 1.0]
    shader.inputs['glossy'].default_value = [1.0, 1.0, 1.0, 1.0]
    shader.inputs['glossy_rough'].default_value = 0.0
    shader.inputs['reflection'].default_value = 0.02

    return shader

def convertToCyclesShader(obj):
    mmd_basic_shader_grp = create_MMDBasicShader()

    for i in obj.material_slots:
        i.material.use_nodes = True
        i.material.node_tree.links.clear()
        shader = i.material.node_tree.nodes.new('GROUP', mmd_basic_shader_grp)
        i.material.node_tree.links.new(i.material.node_tree.nodes['Material Output'].inputs['Surface'], shader.outputs['shader'])
        texture = None
        for j in i.material.texture_slots:
            if j is not None and isinstance(j.texture, bpy.types.ImageTexture):
                texture = i.material.node_tree.nodes.new('TEX_IMAGE')
                texture.image = j.texture.image
        if texture is not None:
            i.material.node_tree.links.new(shader.inputs['diffuse'], texture.outputs['Color'])
        else:
            shader.inputs['diffuse'].default_value = list(i.material.diffuse_color) + [1.0]

