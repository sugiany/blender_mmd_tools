# -*- coding: utf-8 -*-
import struct
import os
import logging

class InvalidFileError(Exception):
    pass
class UnsupportedVersionError(Exception):
    pass

class FileStream:
    def __init__(self, path, file_obj, pmx_header):
        self.__path = path
        self.__file_obj = file_obj
        self.__header = pmx_header

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def path(self):
        return self.__path

    def header(self):
        if self.__header is None:
            raise Exception
        return self.__header

    def setHeader(self, pmx_header):
        self.__header = pmx_header

    def close(self):
        if self.__file_obj is not None:
            logging.debug('close the file("%s")', self.__path)
            self.__file_obj.close()
            self.__file_obj = None

class FileReadStream(FileStream):
    def __init__(self, path, pmx_header=None):
        self.__fin = open(path, 'rb')
        FileStream.__init__(self, path, self.__fin, pmx_header)

    def __readIndex(self, size, typedict):
        index = None
        if size in typedict :
            index, = struct.unpack(typedict[size], self.__fin.read(size))
        else:
            raise ValueError('invalid data size %s'%str(size))
        return index

    def __readSignedIndex(self, size):
        return self.__readIndex(size, { 1 :"<b", 2 :"<h", 4 :"<i"})

    def __readUnsignedIndex(self, size):
        return self.__readIndex(size, { 1 :"<B", 2 :"<H", 4 :"<I"})


    # READ methods for indexes
    def readVertexIndex(self):
        return self.__readUnsignedIndex(self.header().vertex_index_size)

    def readBoneIndex(self):
        return self.__readSignedIndex(self.header().bone_index_size)

    def readTextureIndex(self):
        return self.__readSignedIndex(self.header().texture_index_size)

    def readMorphIndex(self):
        return self.__readSignedIndex(self.header().morph_index_size)

    def readRigidIndex(self):
        return self.__readSignedIndex(self.header().rigid_index_size)

    def readMaterialIndex(self):
        return self.__readSignedIndex(self.header().material_index_size)

    # READ / WRITE methods for general types
    def readInt(self):
        v, = struct.unpack('<i', self.__fin.read(4))
        return v

    def readShort(self):
        v, = struct.unpack('<h', self.__fin.read(2))
        return v

    def readUnsignedShort(self):
        v, = struct.unpack('<H', self.__fin.read(2))
        return v

    def readStr(self):
        length = self.readInt()
        fmt = '<' + str(length) + 's'
        buf, = struct.unpack(fmt, self.__fin.read(length))
        return str(buf, self.header().encoding.charset)

    def readFloat(self):
        v, = struct.unpack('<f', self.__fin.read(4))
        return v

    def readVector(self, size):
        fmt = '<'
        for i in range(size):
            fmt += 'f'
        return list(struct.unpack(fmt, self.__fin.read(4*size)))

    def readByte(self):
        v, = struct.unpack('<B', self.__fin.read(1))
        return v

    def readBytes(self, length):
        return self.__fin.read(length)

    def readSignedByte(self):
        v, = struct.unpack('<b', self.__fin.read(1))
        return v

class FileWriteStream(FileStream):
    def __init__(self, path, pmx_header=None):
        self.__fout = open(path, 'wb')
        FileStream.__init__(self, path, self.__fout, pmx_header)

    def __writeIndex(self, index, size, typedict):
        if size in typedict :
            self.__fout.write(struct.pack(typedict[size], int(index)))
        else:
            raise ValueError('invalid data size %s'%str(size))
        return

    def __writeSignedIndex(self, index, size):
        return self.__writeIndex(index, size, { 1 :"<b", 2 :"<h", 4 :"<i"})

    def __writeUnsignedIndex(self, index, size):
        return self.__writeIndex(index, size, { 1 :"<B", 2 :"<H", 4 :"<I"})

    # WRITE methods for indexes
    def writeVertexIndex(self, index):
        return self.__writeUnsignedIndex(index, self.header().vertex_index_size)

    def writeBoneIndex(self, index):
        return self.__writeSignedIndex(index, self.header().bone_index_size)

    def writeTextureIndex(self, index):
        return self.__writeSignedIndex(index, self.header().texture_index_size)

    def writeMorphIndex(self, index):
        return self.__writeSignedIndex(index, self.header().morph_index_size)

    def writeRigidIndex(self, index):
        return self.__writeSignedIndex(index, self.header().rigid_index_size)

    def writeMaterialIndex(self, index):
        return self.__writeSignedIndex(index, self.header().material_index_size)


    def writeInt(self, v):
        self.__fout.write(struct.pack('<i', int(v)))

    def writeShort(self, v):
        self.__fout.write(struct.pack('<h', int(v)))

    def writeUnsignedShort(self, v):
        self.__fout.write(struct.pack('<H', int(v)))

    def writeStr(self, v):
        data = v.encode(self.header().encoding.charset)
        self.writeInt(len(data))
        self.__fout.write(data)

    def writeFloat(self, v):
        self.__fout.write(struct.pack('<f', float(v)))

    def writeVector(self, v):
        l = len(v)
        fmt = '<'
        for i in range(l):
            fmt += 'f'
        self.__fout.write(struct.pack(fmt, *v))

    def writeByte(self, v):
        self.__fout.write(struct.pack('<B', int(v)))

    def writeBytes(self, v):
        self.__fout.write(v)

    def writeSignedByte(self, v):
        self.__fout.write(struct.pack('<b', int(v)))

class Encoding:
    _MAP = [
        (0, 'utf-16-le'),
        (1, 'utf-8'),
        ]

    def __init__(self, arg):
        self.index = 0
        self.charset = ''
        t = None
        if isinstance(arg, str):
            t = list(filter(lambda x: x[1]==arg, self._MAP))
            if len(t) == 0:
                raise ValueError('invalid charset %s'%arg)
        elif isinstance(arg, int):
            t = list(filter(lambda x: x[0]==arg, self._MAP))
            if len(t) == 0:
                raise ValueError('invalid index %d'%arg)
        else:
            raise ValueError('invalid argument type')
        t = t[0]
        self.index = t[0]
        self.charset  = t[1]

    def __repr__(self):
        return '<Encoding charset %s>'%self.charset

class Coordinate:
    """ """
    def __init__(self, xAxis, zAxis):
        self.x_axis = xAxis
        self.z_axis = zAxis

class Header:
    PMX_SIGN = b'PMX '
    VERSION = 2.0
    def __init__(self, model=None):
        self.sign = self.PMX_SIGN
        self.version = 0

        self.encoding = Encoding('utf-8')
        self.additional_uvs = 0

        self.vertex_index_size = 1
        self.vertex_index_size = 1
        self.material_index_size = 1
        self.bone_index_size = 1
        self.morph_index_size = 1
        self.rigid_index_size = 1

        if model is not None:
            self.updateIndexSizes(model)

    def updateIndexSizes(self, model):
        self.vertex_index_size = self.__getIndexSize(len(model.vertices), False)
        self.texture_index_size = self.__getIndexSize(len(model.textures), True)
        self.material_index_size = self.__getIndexSize(len(model.materials), True)
        self.bone_index_size = self.__getIndexSize(len(model.bones), True)
        self.morph_index_size = self.__getIndexSize(len(model.morphs), True)
        self.rigid_index_size = self.__getIndexSize(len(model.rigids), True)

    @staticmethod
    def __getIndexSize(num, signed):
        s = 1
        if signed:
            s = 2
        if (1<<8)/s > num:
            return 1
        elif (1<<16)/s > num:
            return 2
        else:
            return 4

    def load(self, fs):
        logging.info('loading pmx header information...')
        self.sign = fs.readBytes(4)
        logging.debug('File signature is %s', self.sign)
        if self.sign != self.PMX_SIGN:
            raise InvalidFileError('File signature is invalid.')
        self.version = fs.readFloat()
        if self.version != self.VERSION:
            raise UnsupportedVersionError('unsupported version: %f'%self.version)
        if fs.readByte() != 8:
            raise InvalidFileError
        self.encoding = Encoding(fs.readByte())
        self.additional_uvs = fs.readByte()
        self.vertex_index_size = fs.readByte()
        self.texture_index_size = fs.readByte()
        self.material_index_size = fs.readByte()
        self.bone_index_size = fs.readByte()
        self.morph_index_size = fs.readByte()
        self.rigid_index_size = fs.readByte()

        logging.info('''pmx header information:
pmx version: %.1f
encoding: %s
number of uvs: %d
type sizes of index:
  vertex index: %d
  texture index: %d
  material index: %d
  bone index: %d
  morph index: %d
  rigid index: %d''',
                     self.version,
                     str(self.encoding),
                     self.additional_uvs,
                     self.vertex_index_size,
                     self.texture_index_size,
                     self.material_index_size,
                     self.bone_index_size,
                     self.morph_index_size,
                     self.rigid_index_size)

    def save(self, fs):
        fs.writeBytes(self.PMX_SIGN)
        fs.writeFloat(self.VERSION)
        fs.writeByte(8)
        fs.writeByte(self.encoding.index)
        fs.writeByte(self.additional_uvs)
        fs.writeByte(self.vertex_index_size)
        fs.writeByte(self.texture_index_size)
        fs.writeByte(self.material_index_size)
        fs.writeByte(self.bone_index_size)
        fs.writeByte(self.morph_index_size)
        fs.writeByte(self.rigid_index_size)

    def __repr__(self):
        return '<Header encoding %s, uvs %d, vtx %d, tex %d, mat %d, bone %d, morph %d, rigid %d>'%(
            str(self.encoding),
            self.additional_uvs,
            self.vertex_index_size,
            self.texture_index_size,
            self.material_index_size,
            self.bone_index_size,
            self.morph_index_size,
            self.rigid_index_size,
            )

class Model:
    def __init__(self):
        self.header = None

        self.name = ''
        self.name_e = ''
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

    def load(self, fs):
        self.name = fs.readStr()
        self.name_e = fs.readStr()

        self.comment = fs.readStr()
        self.comment_e = fs.readStr()

        logging.info('''importing pmx model data...
name: %s
name(english): %s
comment:
%s
comment(english):
%s
''', self.name, self.name_e, self.comment, self.comment_e)

        logging.info('importing vertices...')
        num_vertices = fs.readInt()
        self.vertices = []
        for i in range(num_vertices):
            v = Vertex()
            v.load(fs)
            self.vertices.append(v)
        logging.info('the number of vetices: %d', len(self.vertices))
        logging.info('finished importing vertices.')

        logging.info('importing faces...')
        num_faces = fs.readInt()
        self.faces = []
        for i in range(int(num_faces/3)):
            f1 = fs.readVertexIndex()
            f2 = fs.readVertexIndex()
            f3 = fs.readVertexIndex()
            self.faces.append((f3, f2, f1))
        logging.info('the number of faces: %d', len(self.faces))
        logging.info('finished importing faces.')

        logging.info('importing textures...')
        num_textures = fs.readInt()
        self.textures = []
        for i in range(num_textures):
            t = Texture()
            t.load(fs)
            self.textures.append(t)
        logging.info('the number of textures: %d', len(self.textures))
        logging.info('finished importing textures.')

        logging.info('importing materials...')
        num_materials = fs.readInt()
        self.materials = []
        for i in range(num_materials):
            m = Material()
            m.load(fs)
            self.materials.append(m)
        logging.info('the number of materials: %d', len(self.materials))
        logging.info('finished importing materials.')

        logging.info('importing bones...')
        num_bones = fs.readInt()
        self.bones = []
        for i in range(num_bones):
            b = Bone()
            b.load(fs)
            self.bones.append(b)
        logging.info('the number of bones: %d', len(self.bones))
        logging.info('finished importing bones.')

        logging.info('importing morphs...')
        num_morph = fs.readInt()
        self.morphs = []
        for i in range(num_morph):
            m = Morph.create(fs)
            self.morphs.append(m)
        logging.info('the number of morphs: %d', len(self.morphs))
        logging.info('finished importing morphs.')

        logging.info('importing display items...')
        num_disp = fs.readInt()
        self.display = []
        for i in range(num_disp):
            d = Display()
            d.load(fs)
            self.display.append(d)
        logging.info('the number of display items: %d', len(self.display))
        logging.info('finished importing display items.')

        logging.info('importing rigid bodies...')
        num_rigid = fs.readInt()
        self.rigids = []
        for i in range(num_rigid):
            r = Rigid()
            r.load(fs)
            self.rigids.append(r)
        logging.info('the number of rigid bodies: %d', len(self.display))
        logging.info('finished importing rigid bodies.')

        logging.info('importing joints...')
        num_joints = fs.readInt()
        self.joints = []
        for i in range(num_joints):
            j = Joint()
            j.load(fs)
            self.joints.append(j)
        logging.info('the number of joints: %d', len(self.display))
        logging.info('finished importing joints.')
        logging.info('finished importing the model.')

    def save(self, fs):
        fs.writeStr(self.name)
        fs.writeStr(self.name_e)

        fs.writeStr(self.comment)
        fs.writeStr(self.comment_e)

        logging.info('''exportings pmx model data...
name: %s
name(english): %s
comment:
%s
comment(english):
%s
''', self.name, self.name_e, self.comment, self.comment_e)

        logging.info('exporting vertices...')
        fs.writeInt(len(self.vertices))
        for i in self.vertices:
            i.save(fs)
        logging.info('the number of vetices: %d', len(self.vertices))
        logging.info('finished exporting vertices.')

        logging.info('exporting faces...')
        fs.writeInt(len(self.faces)*3)
        for f3, f2, f1 in self.faces:
            fs.writeVertexIndex(f1)
            fs.writeVertexIndex(f2)
            fs.writeVertexIndex(f3)
        logging.info('the number of faces: %d', len(self.faces))
        logging.info('finished exporting faces.')

        logging.info('exporting textures...')
        fs.writeInt(len(self.textures))
        for i in self.textures:
            i.save(fs)
        logging.info('the number of textures: %d', len(self.textures))
        logging.info('finished exporting textures.')

        logging.info('exporting materials...')
        fs.writeInt(len(self.materials))
        for i in self.materials:
            i.save(fs)
        logging.info('the number of materials: %d', len(self.materials))
        logging.info('finished exporting materials.')

        logging.info('exporting bones...')
        fs.writeInt(len(self.bones))
        for i in self.bones:
            i.save(fs)
        logging.info('the number of bones: %d', len(self.bones))
        logging.info('finished exporting bones.')

        logging.info('exporting morphs...')
        fs.writeInt(len(self.morphs))
        for i in self.morphs:
            i.save(fs)
        logging.info('the number of morphs: %d', len(self.morphs))
        logging.info('finished exporting morphs.')

        logging.info('exporting display items...')
        fs.writeInt(len(self.display))
        for i in self.display:
            i.save(fs)
        logging.info('the number of display items: %d', len(self.display))
        logging.info('finished exporting display items.')

        logging.info('exporting rigid bodies...')
        fs.writeInt(len(self.rigids))
        for i in self.rigids:
            i.save(fs)
        logging.info('the number of rigid bodies: %d', len(self.display))
        logging.info('finished exporting rigid bodies.')

        logging.info('exporting joints...')
        fs.writeInt(len(self.joints))
        for i in self.joints:
            i.save(fs)
        logging.info('the number of joints: %d', len(self.display))
        logging.info('finished exporting joints.')
        logging.info('finished exporting the model.')


    def __repr__(self):
        return '<Model name %s, name_e %s, comment %s, comment_e %s, textures %s>'%(
            self.name,
            self.name_e,
            self.comment,
            self.comment_e,
            str(self.textures),
            )

class Vertex:
    def __init__(self):
        self.co = [0.0, 0.0, 0.0]
        self.normal = [0.0, 0.0, 0.0]
        self.uv = [0.0, 0.0]
        self.additional_uvs = []
        self.weight = None
        self.edge_scale = 1

    def __repr__(self):
        return '<Vertex co %s, normal %s, uv %s, additional_uvs %s, weight %s, edge_scale %s>'%(
            str(self.co),
            str(self.normal),
            str(self.uv),
            str(self.additional_uvs),
            str(self.weight),
            str(self.edge_scale),
            )

    def load(self, fs):
        self.co = fs.readVector(3)
        self.normal = fs.readVector(3)
        self.uv = fs.readVector(2)
        self.additional_uvs = []
        for i in range(fs.header().additional_uvs):
            self.additional_uvs.append(fs.readVector(4))
        self.weight = BoneWeight()
        self.weight.load(fs)
        self.edge_scale = fs.readFloat()

    def save(self, fs):
        fs.writeVector(self.co)
        fs.writeVector(self.normal)
        fs.writeVector(self.uv)
        for i in self.additional_uvs:
            fs.writeVector(i)
        self.weight.save(fs)
        fs.writeFloat(self.edge_scale)

class BoneWeightSDEF:
    def __init__(self, weight=0, c=None, r0=None, r1=None):
        self.weight = weight
        self.c = c
        self.r0 = r0
        self.r1 = r1

class BoneWeight:
    BDEF1 = 0
    BDEF2 = 1
    BDEF4 = 2
    SDEF  = 3

    TYPES = [
        (BDEF1, 'BDEF1'),
        (BDEF2, 'BDEF2'),
        (BDEF4, 'BDEF4'),
        (SDEF, 'SDEF'),
        ]

    def __init__(self):
        self.bones = []
        self.weights = []

    def convertIdToName(self, type_id):
        t = list(filter(lambda x: x[0]==type_id, TYPES))
        if len(t) > 0:
            return t[0][1]
        else:
            return None

    def convertNameToId(self, type_name):
        t = list(filter(lambda x: x[1]==type_name, TYPES))
        if len(t) > 0:
            return t[0][0]
        else:
            return None

    def load(self, fs):
        self.type = fs.readByte()
        self.bones = []
        self.weights = []

        if self.type == self.BDEF1:
            self.bones.append(fs.readBoneIndex())
        elif self.type == self.BDEF2:
            self.bones.append(fs.readBoneIndex())
            self.bones.append(fs.readBoneIndex())
            self.weights.append(fs.readFloat())
        elif self.type == self.BDEF4:
            self.bones.append(fs.readBoneIndex())
            self.bones.append(fs.readBoneIndex())
            self.bones.append(fs.readBoneIndex())
            self.bones.append(fs.readBoneIndex())
            self.weights = fs.readVector(4)
        elif self.type == self.SDEF:
            self.bones.append(fs.readBoneIndex())
            self.bones.append(fs.readBoneIndex())
            self.weights = BoneWeightSDEF()
            self.weights.weight = fs.readFloat()
            self.weights.c = fs.readVector(3)
            self.weights.r0 = fs.readVector(3)
            self.weights.r1 = fs.readVector(3)
        else:
            raise ValueError('invalid weight type %s'%str(self.type))

    def save(self, fs):
        fs.writeByte(self.type)
        if self.type == self.BDEF1:
            fs.writeBoneIndex(self.bones[0])
        elif self.type == self.BDEF2:
            for i in range(2):
                fs.writeBoneIndex(self.bones[i])
            fs.writeFloat(self.weights[0])
        elif self.type == self.BDEF4:
            for i in range(4):
                fs.writeBoneIndex(self.bones[i])
            fs.writeFloat(self.weights[0])
        elif self.type == self.SDEF:
            for i in range(2):
                fs.writeBoneIndex(self.bones[i])
            if not isinstance(self.weights, BoneWeightSDEF):
                raise ValueError
            fs.writeFloat(self.weights.weight)
            fs.writeVector(self.weight.c)
            fs.writeVector(self.weight.r0)
            fs.writeVector(self.weight.r1)
        else:
            raise ValueError('invalid weight type %s'%str(self.type))


class Texture:
    def __init__(self):
        self.path = ''

    def __repr__(self):
        return '<Texture path %s>'%str(self.path)

    def load(self, fs):
        self.path = fs.readStr()
        if not os.path.isabs(self.path):
            self.path = os.path.normpath(os.path.join(os.path.dirname(fs.path()), self.path))

    def save(self, fs):
        fs.writeStr(self.path)

class SharedTexture(Texture):
    def __init__(self):
        self.number = 0
        self.prefix = ''

class Material:
    SPHERE_MODE_OFF = 0
    SPHERE_MODE_MULT = 1
    SPHERE_MODE_ADD = 2
    SPHERE_MODE_SUB = 3

    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.diffuse = []
        self.specular = []
        self.ambient = []

        self.is_doulbe_sided = False
        self.enabled_drop_shadow = False
        self.enabled_self_shadow_map = False
        self.enabled_self_shadow = False
        self.enabled_toon_edge = False

        self.edge_color = []
        self.edge_size = 1

        self.texture = None
        self.sphere_texture = None
        self.sphere_texture_mode = 0
        self.is_shared_toon_texture = True
        self.toon_texture = None

        self.comment = ''
        self.vertex_count = 0

    def __repr__(self):
        return '<Material name %s, name_e %s, diffuse %s, specular %s, ambient %s, double_side %s, drop_shadow %s, self_shadow_map %s, self_shadow %s, toon_edge %s, edge_color %s, edge_size %s, toon_texture %s, comment %s>'%(
            self.name,
            self.name_e,
            str(self.diffuse),
            str(self.specular),
            str(self.ambient),
            str(self.is_doulbe_sided),
            str(self.enabled_drop_shadow),
            str(self.enabled_self_shadow_map),
            str(self.enabled_self_shadow),
            str(self.enabled_toon_edge),
            str(self.edge_color),
            str(self.edge_size),
            str(self.texture),
            str(self.sphere_texture),
            str(self.toon_texture),
            str(self.comment),)

    def load(self, fs):
        self.name = fs.readStr()
        self.name_e = fs.readStr()
        logging.info('material: %s', self.name)

        self.diffuse = fs.readVector(4)
        self.specular = fs.readVector(4)
        self.ambient = fs.readVector(3)

        flags = fs.readByte()
        self.is_doulbe_sided = bool(flags & 1)
        self.enabled_drop_shadow = bool(flags & 2)
        self.enabled_self_shadow_map = bool(flags & 4)
        self.enabled_self_shadow = bool(flags & 8)
        self.enabled_toon_edge = bool(flags & 16)

        self.edge_color = fs.readVector(4)
        self.edge_size = fs.readFloat()

        self.texture = fs.readTextureIndex()
        self.sphere_texture = fs.readTextureIndex()
        self.sphere_texture_mode = fs.readSignedByte()

        self.is_shared_toon_texture = fs.readSignedByte()
        self.is_shared_toon_texture = (self.is_shared_toon_texture == 1)
        if self.is_shared_toon_texture:
            self.toon_texture = fs.readSignedByte()
        else:
            self.toon_texture = fs.readTextureIndex()

        self.comment = fs.readStr()
        self.vertex_count = fs.readInt()

    def save(self, fs):
        fs.writeStr(self.name)
        fs.writeStr(self.name)

        fs.writeVector(self.diffuse)
        fs.writeVector(self.specular)
        fs.writeVector(self.ambient)

        flags = 0
        flags |= int(self.is_doulbe_sided)
        flags |= int(self.enabled_drop_shadow) << 1
        flags |= int(self.enabled_self_shadow_map) << 2
        flags |= int(self.enabled_self_shadow) << 3
        flags |= int(self.enabled_toon_edge) << 4
        fs.writeByte(flags)

        fs.writeVector(self.edge_color)
        fs.writeFloat(self.edge_size)

        fs.writeTextureIndex(self.texture)
        fs.writeTextureIndex(self.sphere_texture)
        fs.writeSignedByte(self.sphere_texture_mode)

        fs.writeSignedByte(int(self.is_shared_toon_texture))
        if self.is_shared_toon_texture:
            fs.writeSignedByte(self.toon_texture)
        else:
            fs.writeTextureIndex(self.toon_texture)

        fs.writeStr(self.comment)
        fs.writeInt(self.vertex_count)


class Bone:
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.location = []
        self.parent = None
        self.depth = 0

        # 接続先表示方法
        # 座標オフセット(float3)または、boneIndex(int)
        self.displayConnection = None

        self.isRotatable = True
        self.isMovable = True
        self.visible = True
        self.isControllable = True

        self.isIK = False

        # 回転付与
        self.hasAdditionalRotate = False

        # 移動付与
        self.hasAdditionalLocation = False

        # 回転付与および移動付与の付与量
        self.additionalTransform = None

        # 軸固定
        # 軸ベクトルfloat3
        self.axis = None

        # ローカル軸
        self.localCoordinate = None

        self.transAfterPhis = False

        # 外部親変形
        self.externalTransKey = None

        # 以下IKボーンのみ有効な変数
        self.target = None
        self.loopCount = 0
        # IKループ計三時の1回あたりの制限角度(ラジアン)
        self.rotationConstraint = 0

        # IKLinkオブジェクトの配列
        self.ik_links = []

    def __repr__(self):
        return '<Bone name %s, name_e %s>'%(
            self.name,
            self.name_e,)

    def load(self, fs):
        self.name = fs.readStr()
        self.name_e = fs.readStr()
        logging.debug('bone: %s', self.name)

        self.location = fs.readVector(3)
        self.parent = fs.readBoneIndex()
        self.depth = fs.readInt()

        flags = fs.readShort()
        if flags & 0x0001:
            self.displayConnection = fs.readBoneIndex()
        else:
            self.displayConnection = fs.readVector(3)

        self.isRotatable    = ((flags & 0x0002) != 0)
        self.isMovable      = ((flags & 0x0004) != 0)
        self.visible        = ((flags & 0x0008) != 0)
        self.isControllable = ((flags & 0x0010) != 0)

        self.isIK           = ((flags & 0x0020) != 0)

        self.hasAdditionalRotate = ((flags & 0x0100) != 0)
        self.hasAdditionalLocation = ((flags & 0x0200) != 0)
        if self.hasAdditionalRotate or self.hasAdditionalLocation:
            t = fs.readBoneIndex()
            v = fs.readFloat()
            self.additionalTransform = (t, v)
        else:
            self.additionalTransform = None


        if flags & 0x0400:
            self.axis = fs.readVector(3)
        else:
            self.axis = None

        if flags & 0x0800:
            xaxis = fs.readVector(3)
            zaxis = fs.readVector(3)
            self.localCoordinate = Coordinate(xaxis, zaxis)
        else:
            self.localCoordinate = None

        self.transAfterPhis = ((flags & 0x1000) != 0)

        if flags & 0x2000:
            self.externalTransKey = fs.readInt()
        else:
            self.externalTransKey = None

        if self.isIK:
            self.target = fs.readBoneIndex()
            self.loopCount = fs.readInt()
            self.rotationConstraint = fs.readFloat()

            iklink_num = fs.readInt()
            self.ik_links = []
            for i in range(iklink_num):
                link = IKLink()
                link.load(fs)
                self.ik_links.append(link)

    def save(self, fs):
        fs.writeStr(self.name)
        fs.writeStr(self.name_e)

        fs.writeVector(self.location)
        fs.writeBoneIndex(self.parent)
        fs.writeInt(self.depth)

        flags = 0
        flags |= int(isinstance(self.displayConnection, int))
        flags |= int(self.isRotatable) << 1
        flags |= int(self.isMovable) << 2
        flags |= int(self.visible) << 3
        flags |= int(self.isControllable) << 4
        flags |= int(self.isIK) << 5

        flags |= int(self.hasAdditionalRotate) << 8
        flags |= int(self.hasAdditionalLocation) << 9
        flags |= int(self.axis is not None) << 10
        flags |= int(self.localCoordinate is not None) << 11

        flags |= int(self.externalTransKey is not None) << 13

        fs.writeShort(flags)

        if flags & 0x0001:
            fs.writeBoneIndex(self.displayConnection)
        else:
            fs.writeVector(self.displayConnection)

        if self.hasAdditionalRotate or self.hasAdditionalLocation:
            fs.writeBoneIndex(self.additionalTransform[0])
            fs.writeFloat(self.additionalTransform[1])

        if flags & 0x0400:
            fs.writeVector(self.axis)

        if flags & 0x0800:
            fs.writeVector(self.localCoordinate.x_axis)
            fs.writeVector(self.localCoordinate.z_axis)

        if flags & 0x2000:
            fs.writeInt(self.externalTransKey)

        if self.isIK:
            fs.writeBoneIndex(self.target)
            fs.writeInt(self.loopCount)
            fs.writeFloat(self.rotationConstraint)

            fs.writeInt(len(self.ik_links))
            for i in self.ik_links:
                i.save(fs)


class IKLink:
    def __init__(self):
        self.target = None
        self.maximumAngle = None
        self.minimumAngle = None

    def __repr__(self):
        return '<IKLink target %s>'%(str(self.target))

    def load(self, fs):
        self.target = fs.readBoneIndex()
        flag = fs.readByte()
        if flag == 1:
            self.minimumAngle = fs.readVector(3)
            self.maximumAngle = fs.readVector(3)
        else:
            self.minimumAngle = None
            self.maximumAngle = None

    def save(self, fs):
        fs.writeBoneIndex(self.target)
        if isinstance(self.minimumAngle, list) and isinstance(self.maximumAngle, list):
            fs.writeByte(1)
            fs.writeVector(self.minimumAngle)
            fs.writeVector(self.maximumAngle)
        else:
            fs.writeByte(0)

class Morph:
    CATEGORY_SYSTEM = 0
    CATEGORY_EYEBROW = 1
    CATEGORY_EYE = 2
    CATEGORY_MOUTH = 3
    CATEGORY_OHTER = 4

    def __init__(self, name, name_e, category, **kwargs):
        self.offsets = []
        self.name = name
        self.name_e = name_e
        self.category = category

    def __repr__(self):
        return '<Morph name %s, name_e %s>'%(self.name, self.name_e)

    @staticmethod
    def create(fs):
        _CLASSES = {
            0: GroupMorph,
            1: VertexMorph,
            2: BoneMorph,
            3: UVMorph,
            4: UVMorph,
            5: UVMorph,
            6: UVMorph,
            7: UVMorph,
            8: MaterialMorph,
            }

        name = fs.readStr()
        name_e = fs.readStr()
        logging.debug('morph: %s', name)
        category = fs.readSignedByte()
        typeIndex = fs.readSignedByte()
        ret = _CLASSES[typeIndex](name, name_e, category, type_index = typeIndex)
        ret.load(fs)
        return ret

    def load(self, fs):
        """ Implement for loading morph data.
        """
        raise NotImplementedError

    def save(self, fs):
        fs.writeStr(self.name)
        fs.writeStr(self.name_e)
        fs.writeSignedByte(self.category)
        fs.writeSignedByte(self.type_index())
        fs.writeInt(len(self.offsets))
        for i in self.offsets:
            i.save(fs)

class VertexMorph(Morph):
    def __init__(self, *args, **kwargs):
        Morph.__init__(self, *args, **kwargs)

    def type_index(self):
        return 1

    def load(self, fs):
        num = fs.readInt()
        for i in range(num):
            t = VertexMorphOffset()
            t.load(fs)
            self.offsets.append(t)

class VertexMorphOffset:
    def __init__(self):
        self.index = 0
        self.offset = []

    def load(self, fs):
        self.index = fs.readVertexIndex()
        self.offset = fs.readVector(3)

    def save(self, fs):
        fs.writeVertexIndex(self.index)
        fs.writeVector(self.offset)

class UVMorph(Morph):
    def __init__(self, *args, **kwargs):
        self.uv_index = kwargs.get('type_index', 3) - 3
        Morph.__init__(self, *args, **kwargs)

    def type_index(self):
        return self.uv_index + 3

    def load(self, fs):
        self.offsets = []
        num = fs.readInt()
        for i in range(num):
            t = UVMorphOffset()
            t.load(fs)
            self.offsets.append(t)

class UVMorphOffset:
    def __init__(self):
        self.index = 0
        self.offset = []

    def load(self, fs):
        self.index = fs.readVertexIndex()
        self.offset = fs.readVector(4)

    def save(self, fs):
        fs.writeVertexIndex(self.index)
        fs.writeVector(self.offset)

class BoneMorph(Morph):
    def __init__(self, *args, **kwargs):
        Morph.__init__(self, *args, **kwargs)

    def type_index(self):
        return 2

    def load(self, fs):
        self.offsets = []
        num = fs.readInt()
        for i in range(num):
            t = BoneMorphOffset()
            t.load(fs)
            self.offsets.append(t)

class BoneMorphOffset:
    def __init__(self):
        self.index = None
        self.location_offset = []
        self.rotation_offset = []

    def load(self, fs):
        self.index = fs.readBoneIndex()
        self.location_offset = fs.readVector(3)
        self.rotation_offset = fs.readVector(4)

    def save(self, fs):
        fs.writeBoneIndex(self.index)
        fs.writeVector(self.location_offset)
        fs.writeVector(self.rotation_offset)

class MaterialMorph:
    def __init__(self, *args, **kwargs):
        Morph.__init__(self, *args, **kwargs)

    def type_index(self):
        return 8

    def load(self, fs):
        self.offsets = []
        num = fs.readInt()
        for i in range(num):
            t = MaterialMorphOffset()
            t.load(fs)
            self.offsets.append(t)

class MaterialMorphOffset:
    TYPE_MULT = 0
    TYPE_ADD = 1

    def __init__(self):
        self.index = 0
        self.offset_type = 0
        self.diffuse_offset = []
        self.specular_offset = []
        self.ambient_offset = []
        self.edge_color_offset = []
        self.edge_size_offset = []
        self.texture_factor = []
        self.sphere_texture_factor = []
        self.toon_texture_factor = []

    def load(self, fs):
        self.index = fs.readMaterialIndex()
        self.offset_type = fs.readSignedByte()
        self.diffuse_offset = fs.readVector(4)
        self.specular_offset = fs.readVector(4)
        self.ambient_offset = fs.readVector(3)
        self.edge_color_offset = fs.readVector(4)
        self.edge_size_offset = fs.readFloat()
        self.texture_factor = fs.readVector(4)
        self.sphere_texture_factor = fs.readVector(4)
        self.toon_texture_factor = fs.readVector(4)

    def save(self, fs):
        fs.writeMaterialIndex(self.index)
        fs.writeSignedByte(self.offset_type)
        fs.writeVector(self.diffuse_offset)
        fs.writeVector(self.specular_offset)
        fs.writeVector(self.ambient_offset)
        fs.writeVector(self.edge_color_offset)
        fs.writeFloat(self.edge_size_offset)
        fs.writeVector(self.texture_factor)
        fs.writeVector(self.sphere_texture_factor)
        fs.writeVector(self.toon_texture_factor)

class GroupMorph(Morph):
    def __init__(self, *args, **kwargs):
        Morph.__init__(self, *args, **kwargs)

    def type_index(self):
        return 0

    def load(self, fs):
        self.offsets = []
        num = fs.readInt()
        for i in range(num):
            t = GroupMorphOffset()
            t.load(fs)
            self.offsets.append(t)

class GroupMorphOffset:
    def __init__(self):
        self.morph = None
        self.factor = 0.0

    def load(self, fs):
        self.morph = fs.readMorphIndex()
        self.factor = fs.readFloat()

    def save(self, fs):
        fs.writeMorphIndex(self.morph)
        fs.writeFloat(self.factor)


class Display:
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.isSpecial = False

        self.data = []

    def __repr__(self):
        return '<Display name %s, name_e %s>'%(
            self.name,
            self.name_e,
            )

    def load(self, fs):
        self.name = fs.readStr()
        self.name_e = fs.readStr()

        logging.debug('''importing display item...
name: %s
name(english): %s''', self.name, self.name_e)

        self.isSpecial = (fs.readByte() == 1)
        num = fs.readInt()
        self.data = []
        for i in range(num):
            disp_type = fs.readByte()
            index = None
            if disp_type == 0:
                index = fs.readBoneIndex()
            elif disp_type == 1:
                index = fs.readMorphIndex()
            else:
                raise Exception('invalid value.')
            self.data.append((disp_type, index))
        logging.debug('the number of display elements: %d', len(self.data))

    def save(self, fs):
        fs.writeStr(self.name)
        fs.writeStr(self.name_e)

        fs.writeByte(int(self.isSpecial))
        fs.writeInt(len(self.data))

        for disp_type, index in self.data:
            fs.writeByte(disp_type)
            if disp_type == 0:
                fs.writeBoneIndex(index)
            elif disp_type == 1:
                fs.writeMorphIndex(index)
            else:
                raise Exception('invalid value.')

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
        self.collision_group_mask = 0

        self.type = 0
        self.size = []

        self.location = []
        self.rotation = []

        self.mass = 1
        self.velocity_attenuation = []
        self.rotation_attenuation = []
        self.bounce = []
        self.friction = []

        self.mode = 0

    def __repr__(self):
        return '<Rigid name %s, name_e %s>'%(
            self.name,
            self.name_e,
            )

    def load(self, fs):
        self.name = fs.readStr()
        self.name_e = fs.readStr()

        boneIndex = fs.readBoneIndex()
        if boneIndex != -1:
            self.bone = boneIndex
        else:
            self.bone = None

        self.collision_group_number = fs.readSignedByte()
        self.collision_group_mask = fs.readUnsignedShort()

        self.type = fs.readSignedByte()
        self.size = fs.readVector(3)

        self.location = fs.readVector(3)
        self.rotation = fs.readVector(3)

        self.mass = fs.readFloat()
        self.velocity_attenuation = fs.readFloat()
        self.rotation_attenuation = fs.readFloat()
        self.bounce = fs.readFloat()
        self.friction = fs.readFloat()

        self.mode = fs.readSignedByte()

    def save(self, fs):
        fs.writeStr(self.name)
        fs.writeStr(self.name_e)

        if self.bone is None:
            fs.writeBoneIndex(-1)
        else:
            fs.writeBoneIndex(self.bone)

        fs.writeSignedByte(self.collision_group_number)
        fs.writeUnsignedShort(self.collision_group_mask)

        fs.writeSignedByte(self.type)
        fs.writeVector(self.size)

        fs.writeVector(self.location)
        fs.writeVector(self.rotation)

        fs.writeFloat(self.mass)
        fs.writeFloat(self.velocity_attenuation)
        fs.writeFloat(self.rotation_attenuation)
        fs.writeFloat(self.bounce)
        fs.writeFloat(self.friction)

        fs.writeSignedByte(self.mode)

class Joint:
    MODE_SPRING6DOF = 0
    def __init__(self):
        self.name = ''
        self.name_e = ''

        self.mode = 0

        self.src_rigid = None
        self.dest_rigid = None

        self.location = []
        self.rotation = []

        self.maximum_location = []
        self.minimum_location = []
        self.maximum_rotation = []
        self.minimum_rotation = []

        self.spring_constant = []
        self.spring_rotation_constant = []

    def load(self, fs):
        self.name = fs.readStr()
        self.name_e = fs.readStr()

        self.mode = fs.readSignedByte()

        self.src_rigid = fs.readRigidIndex()
        self.dest_rigid = fs.readRigidIndex()
        if self.src_rigid == -1:
            self.src_rigid = None
        if self.dest_rigid == -1:
            self.dest_rigid = None

        self.location = fs.readVector(3)
        self.rotation = fs.readVector(3)

        self.minimum_location = fs.readVector(3)
        self.maximum_location = fs.readVector(3)
        self.minimum_rotation = fs.readVector(3)
        self.maximum_rotation = fs.readVector(3)

        self.spring_constant = fs.readVector(3)
        self.spring_rotation_constant = fs.readVector(3)

    def save(self, fs):
        fs.writeStr(self.name)
        fs.writeStr(self.name_e)

        fs.writeSignedByte(self.mode)

        if self.src_rigid is not None:
            fs.writeRigidIndex(self.src_rigid)
        else:
            fs.writeRigidIndex(-1)
        if self.dest_rigid is not None:
            fs.writeRigidIndex(self.dest_rigid)
        else:
            fs.writeRigidIndex(-1)

        fs.writeVector(self.location)
        fs.writeVector(self.rotation)

        fs.writeVector(self.minimum_location)
        fs.writeVector(self.maximum_location)
        fs.writeVector(self.minimum_rotation)
        fs.writeVector(self.maximum_rotation)

        fs.writeVector(self.spring_constant)
        fs.writeVector(self.spring_rotation_constant)



def load(path):
    with FileReadStream(path) as fs:
        header = Header()
        header.load(fs)
        fs.setHeader(header)
        model = Model()
        model.load(fs)
        return model

def save(path, model):
    with FileWriteStream(path) as fs:
        header = Header(model)
        header.save(fs)
        fs.setHeader(header)
        model.save(fs)
