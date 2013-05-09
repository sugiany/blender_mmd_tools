# -*- coding: utf-8 -*-
from . import pmx

import collections

import mathutils
import bpy
import bmesh
import copy

class PmxExporter:
    TO_PMX_MATRIX = mathutils.Matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]])

    def __init__(self):
        self.__model = None
        self.__targetMesh = None

    @staticmethod
    def flipUV_V(uv):
        u, v = uv
        return [u, 1.0-v]

    @staticmethod
    def __getVerticesTable(mesh):
        r = []
        for bv in mesh.vertices:
            pv = pmx.Vertex()
            pv.co = bv.co
            pv.normal = bv.normal
            pv.uv = None

            weight = pmx.BoneWeight()
            weight.type = pmx.BoneWeight.BDEF1
            weight.bones = [-1]
            pv.weight = weight
            r.append(pv)
        return r

    @staticmethod
    def __getFaceTable(mesh):
        verticesTable = PmxExporter.__getVerticesTable(mesh)
        r = []
        for f, uv in zip(mesh.tessfaces, mesh.tessface_uv_textures.active.data):
            if len(f.vertices) != 3:
                raise Exception
            t = []
            for i in f.vertices:
                t.append(verticesTable[i])
            r.append((f, uv, t))
        return r

    @staticmethod
    def __convertFaceUVToVertexUV(vertex, uv, cloneVertexMap):
        if vertex.uv is None:
            vertex.uv = uv
        elif (vertex.uv[0] - uv[0])**2 + (vertex.uv[1] - uv[1])**2 > 0.0001:
            for i in cloneVertexMap[vertex]:
                if (i.uv[0] - uv[0])**2 + (i.uv[1] - uv[1])**2 < 0.0001:
                    return i
            n = copy.deepcopy(vertex)
            n.uv = uv
            cloneVertexMap[vertex].append(n)
            return n
        return vertex

    def __exportFaces(self):
        self.__materialIndexDict = collections.defaultdict(list)
        cloneVertexMap = collections.defaultdict(list)
        mesh = self.__targetMesh

        faceTable = self.__getFaceTable(mesh)
        for f, uv, vertices in faceTable:
            vertices[0] = self.__convertFaceUVToVertexUV(vertices[0], self.flipUV_V(uv.uv1), cloneVertexMap)
            vertices[1] = self.__convertFaceUVToVertexUV(vertices[1], self.flipUV_V(uv.uv2), cloneVertexMap)
            vertices[2] = self.__convertFaceUVToVertexUV(vertices[2], self.flipUV_V(uv.uv3), cloneVertexMap)

        verticesSet = set()
        for f, uv, vertices in faceTable:
            verticesSet.update(set(vertices))

        self.__model.vertices = list(verticesSet)
        for f, uv, vertices in faceTable:
            v1 = self.__model.vertices.index(vertices[0])
            v2 = self.__model.vertices.index(vertices[1])
            v3 = self.__model.vertices.index(vertices[2])
            self.__materialIndexDict[f.material_index].append([v1, v2, v3])

        for i in sorted(self.__materialIndexDict.keys()):
            self.__model.faces.extend(self.__materialIndexDict[i])

    def __exportTexture(self, texture):
        if not isinstance(texture, bpy.types.ImageTexture):
            return -1
        t = pmx.Texture()
        t.path = texture.image.filepath
        self.__model.textures.append(t)
        return len(self.__model.textures) - 1

    def __exportMaterials(self):
        mesh = self.__targetMesh
        textureList = []
        for m_index, i in enumerate(mesh.materials):
            num_faces = len(self.__materialIndexDict[m_index])
            if num_faces == 0:
                continue
            p_mat = pmx.Material()
            p_mat.name = i.name
            p_mat.name_e = i.name
            p_mat.diffuse = list(i.diffuse_color) + [i.alpha]
            p_mat.ambient = i.ambient_color or [0.5, 0.5, 0.5]
            p_mat.specular = list(i.specular_color) + [i.specular_alpha]
            p_mat.edge_color = [0.25, 0.3, 0.5, 0.5]
            p_mat.vertex_count = num_faces * 3
            if len(i.texture_slots) > 0:
                tex = i.texture_slots[0].texture
                index = -1
                if tex not in textureList:
                    index = self.__exportTexture(tex)
                    textureList.append(tex)
                else:
                    index = textureList.index(tex)
                p_mat.texture = index
            self.__model.materials.append(p_mat)

    @staticmethod
    def __triangulate(mesh):
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()

    def execute(self, **args):
        self.__model = pmx.Model()
        self.__model.name = 'test'
        self.__model.name_e = 'test eng'

        self.__model.comment = 'exported by mmd_tools'

        target = args['object']
        self.__scale = args.get('scale', 1.0)


        mesh = target.to_mesh(bpy.context.scene, True, 'PREVIEW', False)
        mesh.transform(self.TO_PMX_MATRIX*(1.0/self.__scale))
        self.__triangulate(mesh)
        mesh.update(calc_tessface=True)

        self.__targetMesh = mesh
        outpath = args['path']


        self.__exportFaces()
        self.__exportMaterials()
        pmx.save(outpath, self.__model)
