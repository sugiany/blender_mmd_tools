# -*- coding: utf-8 -*-

from . import import_pmx
from . import pmd
from . import pmx

import mathutils

import os
import re


def import_pmd(**kwargs):
    """ Import pmd file
    """
    target_path = kwargs['filepath']
    pmd_model = pmd.load(target_path)

    pmx_model = pmx.Model()

    pmx_model.name = pmd_model.name
    pmd_model.name_e = pmd_model.name_e
    pmx_model.comment = pmd_model.comment
    pmd_model.comment_e = pmd_model.comment_e

    pmx_model.vertices = []

    # convert vertices
    for v in pmd_model.vertices:
        pmx_v = pmx.Vertex()
        pmx_v.co = v.position
        pmx_v.normal = v.normal
        pmx_v.uv = v.uv
        pmx_v.additional_uvs= []
        pmx_v.edge_scale = 1

        weight = pmx.BoneWeight()
        if v.bones[0] != v.bones[1]:
            weight.type = pmx.BoneWeight.BDEF2
            weight.bones = v.bones
            weight.weights = [float(v.weight)/100.0]
        else:
            weight.type = pmx.BoneWeight.BDEF1
            weight.bones = [v.bones[0]]
            weight.weights = [float(v.weight)/100.0]

        pmx_v.weight = weight

        pmx_model.vertices.append(pmx_v)

    # convert faces
    for f in pmd_model.faces:
        pmx_model.faces.append(f)

    knee_bones = []
    # convert bones
    for i, bone in enumerate(pmd_model.bones):
        pmx_bone = pmx.Bone()
        pmx_bone.name = bone.name
        pmx_bone.location = bone.position
        pmx_bone.parent = bone.parent
        if bone.type != 9:
            pmx_bone.displayConnection = bone.tail_bone
        else:
            pmx_bone.displayConnection = -1
        if pmx_bone.displayConnection <= 0:
            pmx_bone.displayConnection = [0.0, 0.0, 0.0]
        pmx_bone.isIK = False #(bone.ik_bone != 0)
        if bone.type == 0:
            pmx_bone.isMovable = False
        elif bone.type == 1:
            pass
        elif bone.type == 4:
            pmx_bone.isControllable = False
        elif bone.type == 5:
            pmx_bone.hasAdditionalRotate = True
            pmx_bone.additionalTransform = (bone.ik_bone, 1.0)
        elif bone.type == 7:
            pmx_bone.visible = False
        elif bone.type == 9:
            pmx_bone.hasAdditionalRotate = True
            pmx_bone.additionalTransform = (bone.tail_bone, float(bone.ik_bone)/100.0)

        pmx_model.bones.append(pmx_bone)

        if re.search(u'ひざ$', pmx_bone.name):
            knee_bones.append(i)

    # convert ik
    for ik in pmd_model.iks:
        pmx_bone = pmx_model.bones[ik.bone]
        pmx_bone.isIK = True
        pmx_bone.target = ik.target_bone
        pmx_bone.loopCount = ik.ik_chain
        for i in ik.ik_child_bones:
            ik_link = pmx.IKLink()
            ik_link.target = i
            if i in knee_bones:
                ik_link.maximumAngle = [-0.5, 0.0, 0.0]
                ik_link.minimumAngle = [-180.0, 0.0, 0.0]
            pmx_bone.ik_links.append(ik_link)

    # convert materials
    texture_map = {}
    for i, mat in enumerate(pmd_model.materials):
        pmx_mat = pmx.Material()
        pmx_mat.name = 'Material%d'%i
        pmx_mat.diffuse = mat.diffuse
        pmx_mat.specular = mat.specular + [mat.specular_intensity]
        pmx_mat.ambient = mat.ambient
        pmx_mat.vertex_count = mat.vertex_count
        if len(mat.texture_path) > 0:
            tex_path = mat.texture_path
            if tex_path not in texture_map:
                tex = pmx.Texture()
                tex.path = os.path.normpath(os.path.join(os.path.dirname(target_path), tex_path))
                pmx_model.textures.append(tex)
                texture_map[tex_path] = len(pmx_model.textures) - 1
            pmx_mat.texture = texture_map[tex_path]
        pmx_model.materials.append(pmx_mat)

    # convert vertex morphs
    vertex_map = None

    for morph in filter(lambda x: x.type == 0, pmd_model.morphs):
        vertex_map = []
        for i in morph.data:
            vertex_map.append(i.index)

    for morph in pmd_model.morphs:
        if morph.type == 0:
            continue
        pmx_morph = pmx.VertexMorph(morph.name, '', morph.type)
        for i in morph.data:
            mo = pmx.VertexMorphOffset()
            mo.index = vertex_map[i.index]
            mo.offset = i.offset
            pmx_morph.offsets.append(mo)
        pmx_model.morphs.append(pmx_morph)

    # convert rigid bodies
    for rigid in pmd_model.rigid_bodies:
        pmx_rigid = pmx.Rigid()

        pmx_rigid.name = rigid.name

        pmx_rigid.bone = rigid.bone
        pmx_rigid.collision_group_number = rigid.collision_group_number
        pmx_rigid.collision_group_mask = rigid.collision_group_mask
        pmx_rigid.type = rigid.type

        pmx_rigid.size = rigid.size

        # a location parameter of pmd.RigidBody is the offset from the relational bone or the center bone.
        if rigid.bone == -1:
            t = 0
        else:
            t = rigid.bone
        pmx_rigid.location = mathutils.Vector(pmx_model.bones[t].location) + mathutils.Vector(rigid.location)
        pmx_rigid.rotation = rigid.rotation

        pmx_rigid.mass = rigid.mass
        pmx_rigid.velocity_attenuation = rigid.velocity_attenuation
        pmx_rigid.rotation_attenuation = rigid.rotation_attenuation
        pmx_rigid.bounce = rigid.bounce
        pmx_rigid.friction = rigid.friction
        pmx_rigid.mode = rigid.mode

        pmx_model.rigids.append(pmx_rigid)

    # convert joints
    for joint in pmd_model.joints:
        pmx_joint = pmx.Joint()

        pmx_joint.name = joint.name
        pmx_joint.src_rigid = joint.src_rigid
        pmx_joint.dest_rigid = joint.dest_rigid

        pmx_joint.location = joint.location
        pmx_joint.rotation = joint.rotation

        pmx_joint.maximum_location = joint.minimum_location
        pmx_joint.minimum_location = joint.maximum_location
        pmx_joint.maximum_rotation = joint.minimum_rotation
        pmx_joint.minimum_rotation = joint.maximum_rotation

        pmx_joint.spring_constant = joint.spring_constant
        pmx_joint.spring_rotation_constant = joint.spring_rotation_constant

        pmx_model.joints.append(pmx_joint)


    importer = import_pmx.PMXImporter()
    kwargs['pmx'] = pmx_model
    importer.execute(**kwargs)
