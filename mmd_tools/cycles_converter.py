# -*- coding: utf-8 -*-
import bpy
import mathutils

def __exposeNodeTreeInput(in_socket, name, default_value, node_input, shader):
    t = len(node_input.outputs)-1
    i = node_input.outputs[t]
    shader.links.new(in_socket, i)
    if default_value is not None:
        shader.inputs[t].default_value = default_value
    shader.inputs[t].name = name

def __exposeNodeTreeOutput(out_socket, name, node_output, shader):
    t = len(node_output.inputs)-1
    i = node_output.inputs[t]
    shader.links.new(i, out_socket)
    shader.outputs[t].name = name

def create_MMDAlphaShader():
    bpy.context.scene.render.engine = 'CYCLES'

    if 'MMDAlphaShader' in bpy.data.node_groups:
        return bpy.data.node_groups['MMDAlphaShader']

    shader = bpy.data.node_groups.new(name='MMDAlphaShader', type='ShaderNodeTree')

    node_input = shader.nodes.new('NodeGroupInput')
    node_output = shader.nodes.new('NodeGroupOutput')

    trans = shader.nodes.new('ShaderNodeBsdfTransparent')
    mix = shader.nodes.new('ShaderNodeMixShader')

    shader.links.new(mix.inputs[1], trans.outputs['BSDF'])

    __exposeNodeTreeInput(mix.inputs[2], 'Shader', None, node_input, shader)
    __exposeNodeTreeInput(mix.inputs['Fac'], 'Alpha', 1.0, node_input, shader)
    __exposeNodeTreeOutput(mix.outputs['Shader'], 'Shader', node_output, shader)

    return shader


def create_MMDBasicShader():
    bpy.context.scene.render.engine = 'CYCLES'

    if 'MMDBasicShader' in bpy.data.node_groups:
        return bpy.data.node_groups['MMDBasicShader']

    shader = bpy.data.node_groups.new(name='MMDBasicShader', type='ShaderNodeTree')

    node_input = shader.nodes.new('NodeGroupInput')
    node_output = shader.nodes.new('NodeGroupOutput')

    dif = shader.nodes.new('ShaderNodeBsdfDiffuse')
    glo = shader.nodes.new('ShaderNodeBsdfGlossy')
    mix = shader.nodes.new('ShaderNodeMixShader')

    shader.links.new(mix.inputs[1], dif.outputs['BSDF'])
    shader.links.new(mix.inputs[2], glo.outputs['BSDF'])

    __exposeNodeTreeInput(dif.inputs['Color'], 'diffuse', [1.0, 1.0, 1.0, 1.0], node_input, shader)
    __exposeNodeTreeInput(glo.inputs['Color'], 'glossy', [1.0, 1.0, 1.0, 1.0], node_input, shader)
    __exposeNodeTreeInput(glo.inputs['Roughness'], 'glossy_rough', 0.0, node_input, shader)
    __exposeNodeTreeInput(mix.inputs['Fac'], 'reflection', 0.02, node_input, shader)
    __exposeNodeTreeOutput(mix.outputs['Shader'], 'shader', node_output, shader)

    return shader

def convertToCyclesShader(obj):
    mmd_basic_shader_grp = create_MMDBasicShader()
    mmd_alpha_shader_grp = create_MMDAlphaShader()

    for i in obj.material_slots:
        if i.material.use_nodes:
            continue

        i.material.use_nodes = True

        for j in i.material.node_tree.nodes:
            print(j)
        if any(filter(lambda x: isinstance(x, bpy.types.ShaderNodeGroup) and  x.node_tree.name in ['MMDBasicShader', 'MMDAlphaShader'], i.material.node_tree.nodes)):
            continue


        i.material.node_tree.links.clear()
        shader = i.material.node_tree.nodes.new('ShaderNodeGroup')
        shader.node_tree = mmd_basic_shader_grp
        texture = None
        outplug = shader.outputs[0]

        for j, use in zip(i.material.texture_slots, i.material.use_textures):
            if j is not None and isinstance(j.texture, bpy.types.ImageTexture) and use:
                if j.texture_coords == 'UV':  # don't use sphere maps for now
                    texture = i.material.node_tree.nodes.new('ShaderNodeTexImage')
                    texture.image = j.texture.image

        if texture is not None or i.material.alpha < 1.0:
            alpha_shader = i.material.node_tree.nodes.new('ShaderNodeGroup')
            alpha_shader.node_tree = mmd_alpha_shader_grp
            i.material.node_tree.links.new(alpha_shader.inputs[0], outplug)
            outplug = alpha_shader.outputs[0]

        if texture is not None:
            if i.material.diffuse_color == mathutils.Color((1.0, 1.0, 1.0)):
                i.material.node_tree.links.new(shader.inputs[0], texture.outputs['Color'])
            else:
                mix_rgb = i.material.node_tree.nodes.new('ShaderNodeMixRGB')
                mix_rgb.blend_type = 'MULTIPLY'
                mix_rgb.inputs[0].default_value = 1.0
                mix_rgb.inputs[1].default_value = list(i.material.diffuse_color) + [1.0]
                i.material.node_tree.links.new(mix_rgb.inputs[2], texture.outputs['Color'])
                i.material.node_tree.links.new(shader.inputs[0], mix_rgb.outputs['Color'])
            if i.material.alpha == 1.0:
                i.material.node_tree.links.new(alpha_shader.inputs[1], texture.outputs['Alpha'])
            else:
                mix_alpha = i.material.node_tree.nodes.new('ShaderNodeMath')
                mix_alpha.operation = 'MULTIPLY'
                mix_alpha.inputs[0].default_value = i.material.alpha
                i.material.node_tree.links.new(mix_alpha.inputs[1], texture.outputs['Alpha'])
                i.material.node_tree.links.new(alpha_shader.inputs[1], mix_alpha.outputs['Value'])
        else:
            shader.inputs[0].default_value = list(i.material.diffuse_color) + [1.0]
            if i.material.alpha < 1.0:
                alpha_shader.inputs[1].default_value = i.material.alpha

        i.material.node_tree.links.new(i.material.node_tree.nodes['Material Output'].inputs['Surface'], outplug)
