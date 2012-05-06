# -*- coding: utf-8 -*-
import struct

class Encoding:
    UTF_16 = 0
    UTF_8  = 1

class File:
    def __init__(self):
        pass

class Coordinate:
    """ """
    def __init__(self, xAxis, zAxis):
        self.x_axis = []
        self.z_axis = []

class Header:
    def __init__(self):
        self.sign = "PMX "
        self.version = '2.0'

        self.encoding = encoding.UTF8
        self.additional_uvs = 0

        self.vertex_index_size = 1
        self.material_index_size = 1
        self.bone_index_size = 1
        self.morph_index_size = 1
        self.rigid_index_size = 1
        self.model_vertices = 0

class Model:
    def __init__(self):
        self.model_name = ''
        self.model_name_e = ''
        self.comment = ''
        self.comment_e = ''

        self.vertices = []
        self.faces = []
        self.textures = []
        self.materials = []
        self.bones = []
        self.morphs = []

        self.display = []

        self.rigids = []
        self.joints = []

class Vertex:
    def __init__(self):
        self.co = [0.0, 0.0, 0.0]
        self.normal = [0.0, 0.0, 0.0]
        self.uv = [0.0, 0.0]
        self.additional_uvs = []
        self.weight = None
        self.edge_scale = 1

class BoneWeight:
    BDEF1 = 0
    BDEF2 = 1
    BDEF4 = 2
    SDEF  = 3

    def __init__(self):
        self.type = BDEF1
        self.bones = []
        self.weights = []

class Face:
    def __init__(self):
        self.vertices = []

class Texture:
    def __init__(self):
        self.path = ''

class SharedTexture(Texture):
    def __init__(self):
        self.number = 0
        self.prefix = ''

class Material:
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.diffuse = []
        self.specular = []
        self.ambient = []

        self.isDoulbeSided = False
        self.enabledDropShadow = False
        self.enabledSelfShadowMap = False
        self.enabledSelfShadow = False
        self.enabledToonEdge = False

        self.edge_color = []
        self.edge_size = 1

        self.texture = None
        self.sphere_texture = None
        self.toon_texture = None

        self.comment = ''

class Bone:
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.location = []
        self.parent = None
        self.offset = []
        self.depth = 0

        # 接続先表示方法
        # 座標オフセット(float3)または、Boneオブジェクト
        self.displayConnection = None

        self.isRotatable = True
        self.isMovable = True
        self.visible = True
        self.isEditable = True

        self.ik = False

        # 回転付与
        # (Boneオブジェクト, 付与率float)のタプル
        self.externalTrans = None

        # 移動付与
        # (Boneオブジェクト, 付与率float)のタプル
        self.externalTrans = None

        # 軸固定
        # 軸ベクトルfloat3
        self.axis = None

        # ローカル軸
        self.localCoordinate = None

        self.transAfterPhis = False

        # 外部親変形
        self.externalTransKey = None

class IKLink:
    def __init__(self):
        self.target = None
        self.maximunAngle = None
        self.minimumAngle = None

class IKBone(Bone):
    def __init__(self):
        Bone.__init__(self)

        self.target = None
        self.loopCount = 0
        # IKループ計三時の1回あたりの制限角度(ラジアン)
        self.rotationConstraint = 0

        # IKLinkオブジェクトの配列
        self.ik_links = []


class Morph:
    """ """
    CATEGORY_SYSTEM = 0
    CATEGORY_EYEBROW = 1
    CATEGORY_EYE = 2
    CATEGORY_MOUTH = 3
    CATEGORY_OHTER = 4

    def __init__(self):
        self.name = ''
        self.name_e = ''

class VertexMorphData:
    def __init_(self):
        self.vertex = None
        self.offset = []

class UVMorphData:
    def __init__(self):
        self.vertex = None
        self.offset = []

class BoneMorphData:
    def __init__(self):
        self.bone = None
        self.location_offset = []
        self.rotation_offset = []

class MaterialMorphData:
    TYPE_MULT = 0
    TYPE_ADD = 1
    
    def __init__(self):
        self.material = None
        self.offset_type = TYPE_MULT
        self.diffuse_offset = []
        self.specular_offset = []
        self.ambient_offset = []
        self.edge_color_offset = []
        self.edge_size_offset = []
        self.texture_factor = []
        self.sphere_texture_factor = []
        self.toon_texture_factor = []

class GroupMorphData:
    def __init__(self):
        self.morph = None
        self.factor = 0.0

class VertexMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []

class UVMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []

class BoneMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []

class MaterialMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []

class GroupMorph(Morph):
    def __init__(self):
        Morph.__init__(self)

        self.data = []


class Display:
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.isSpecial = False

        self.data = []

class Rigid:
    TYPE_SPHERE = 0
    TYPE_BOX = 1
    TYPE_CAPSULE = 2

    MODE_STATIC = 0
    MODE_DYNAMIC = 1
    MODE_DYNAMIC_BONE = 2
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.bone = None
        self.collision_group_number = 0
        self.non_collision_group_number = 0

        self.type = TYPE_SPHERE
        self.size = []

        self.location = []
        self.rotation = []

        self.mass = 1
        self.velocity_attenuation = []
        self.rotation_attenuation = []
        self.bounce = []
        self.friction = []

        self.mode = MODE_STATIC

class Joint:
    MODE_SPRING6DOF = 0
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.mode = MODE_SPRING6DOF

        self.src_rigid = None
        self.dest_rigid = None

        self.location = []
        self.rotation = []

        self.maximum_location = []
        self.minimum_location = []
        self.maximum_rotation = []
        self.minimum_rotation = []

        self.spring_constant = []
        self.spring_rotaion_constant = []
