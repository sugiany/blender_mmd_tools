# -*- coding: utf-8 -*-
import struct
import os
import logging
import collections

class InvalidFileError(Exception):
    pass
class UnsupportedVersionError(Exception):
    pass

class FileStream:
    def __init__(self, path, file_obj):
        self.__path = path
        self.__file_obj = file_obj

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


class  FileReadStream(FileStream):
    def __init__(self, path, pmx_header=None):
        self.__fin = open(path, 'rb')
        FileStream.__init__(self, path, self.__fin)


    # READ / WRITE methods for general types
    def readInt(self):
        v, = struct.unpack('<i', self.__fin.read(4))
        return v

    def readUnsignedInt(self):
        v, = struct.unpack('<I', self.__fin.read(4))
        return v

    def readShort(self):
        v, = struct.unpack('<h', self.__fin.read(2))
        return v

    def readUnsignedShort(self):
        v, = struct.unpack('<H', self.__fin.read(2))
        return v

    def readStr(self, size):
        buf = self.__fin.read(size)
        try:
            index = buf.index(b'\x00')
            t = buf[:index]
            return t.decode('shift-jis')
        except ValueError:
            if buf[0] == b'\xfd':
                return ''
            try:
                return buf.decode('shift-jis')
            except UnicodeDecodeError:
                logging.warning('found a invalid shift-jis string.')
                return ''

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


class Header:
    PMD_SIGN = b'Pmd'
    VERSION = 1.0

    def __init__(self):
        self.sign = self.PMD_SIGN
        self.version = self.VERSION
        self.model_name = ''
        self.comment = ''

    def load(self, fs):
        sign = fs.readBytes(3)
        if sign != self.PMD_SIGN:
            raise InvalidFileError('Not PMD file')
        version = fs.readFloat()
        if version != self.version:
            raise InvalidFileError('Not suppored version')

        self.model_name = fs.readStr(20)
        self.comment = fs.readStr(256)

class Vertex:
    def __init__(self):
        self.position = [0.0, 0.0, 0.0]
        self.normal = [1.0, 0.0, 0.0]
        self.uv = [0.0, 0.0]
        self.bones = [-1, -1]
        self.weight = 0 # min:0, max:100
        self.enable_edge = 0 # 0: on, 1: off

    def load(self, fs):
        self.position = fs.readVector(3)
        self.normal = fs.readVector(3)
        self.uv = fs.readVector(2)
        self.bones[0] = fs.readUnsignedShort()
        self.bones[1] = fs.readUnsignedShort()
        self.weight = fs.readByte()
        self.enable_edge = fs.readByte()

class Material:
    def __init__(self):
        self.diffuse = []
        self.specular_intensity = 0.5
        self.specular = []
        self.ambient = []
        self.toon_inde = 0
        self.edge_flag = 0
        self.vertex_count = 0
        self.texture_path = ''
        self.sphere_path = ''

    def load(self, fs):
        self.diffuse = fs.readVector(4)
        self.specular_intensity = fs.readFloat()
        self.specular = fs.readVector(3)
        self.ambient = fs.readVector(3)
        self.toon_index = fs.readByte()
        self.edge_flag = fs.readByte()
        self.vertex_count = fs.readUnsignedInt()
        tex_path = fs.readStr(20)
        t = tex_path.split('*')
        self.texture_path = t.pop(0)
        if len(t) > 0:
            self.sphere_path = t.pop(0)

class Bone:
    def __init__(self):
        self.name = ''
        self.name_e = ''
        self.parent = 0xffff
        self.tail_bone = 0xffff
        self.type = 1
        self.ik_bone = 0
        self.position = []

    def load(self, fs):
        self.name = fs.readStr(20)
        self.parent = fs.readUnsignedShort()
        if self.parent == 0xffff:
            self.parent = -1
        self.tail_bone = fs.readUnsignedShort()
        if self.tail_bone == 0xffff:
            self.tail_bone = -1
        self.type = fs.readByte()
        self.ik_bone = fs.readUnsignedShort()
        self.position = fs.readVector(3)

class IK:
    def __init__(self):
        self.bone = 0
        self.target_bone = 0
        self.ik_chain = 0
        self.iterations = 0
        self.control_weight = 0.0
        self.ik_child_bones = []

    def __str__(self):
        return '<IK bone: %d, target: %d, chain: %s, iter: %d, weight: %f, ik_children: %s'%(
            self.bone,
            self.target_bone,
            self.ik_chain,
            self.iterations,
            self.control_weight,
            self.ik_child_bones)

    def load(self, fs):
        self.bone = fs.readUnsignedShort()
        self.target_bone = fs.readUnsignedShort()
        self.ik_chain = fs.readByte()
        self.iterations = fs.readUnsignedShort()
        self.control_weight = fs.readFloat()
        self.ik_child_bones = []
        for i in range(self.ik_chain):
            self.ik_child_bones.append(fs.readUnsignedShort())

class MorphData:
    def __init__(self):
        self.index = 0
        self.offset = []

    def load(self, fs):
        self.index = fs.readUnsignedInt()
        self.offset = fs.readVector(3)

class VertexMorph:
    def __init__(self):
        self.name = ''
        self.type = 0
        self.data = []

    def load(self, fs):
        self.name = fs.readStr(20)
        data_size = fs.readUnsignedInt()
        self.type = fs.readByte()
        for i in range(data_size):
            t = MorphData()
            t.load(fs)
            self.data.append(t)

class RigidBody:
    def __init__(self):
        self.name = ''
        self.bone = -1
        self.collision_group_number = 0
        self.collision_group_mask = 0
        self.type = 0
        self.size = []
        self.location = []
        self.rotation = []
        self.mass = 0.0
        self.velocity_attenuation = 0.0
        self.rotation_attenuation = 0.0
        self.friction = 0.0
        self.bounce = 0.0
        self.mode = 0

    def load(self, fs):
        self.name = fs.readStr(20)
        self.bone = fs.readUnsignedShort()
        if self.bone == 0xffff:
            self.bone = -1
        self.collision_group_number = fs.readByte()
        self.collision_group_mask = fs.readUnsignedShort()
        self.type = fs.readByte()
        self.size = fs.readVector(3)
        self.location = fs.readVector(3)
        self.rotation = fs.readVector(3)
        self.mass = fs.readFloat()
        self.velocity_attenuation = fs.readFloat()
        self.rotation_attenuation = fs.readFloat()
        self.bounce = fs.readFloat()
        self.friction = fs.readFloat()
        self.mode = fs.readByte()

class Joint:
    def __init__(self):
        self.name = ''
        self.src_rigid = 0
        self.dest_rigid = 0

        self.location = []
        self.rotation = []

        self.maximum_location = []
        self.minimum_location = []
        self.maximum_rotation = []
        self.minimum_rotation = []

        self.spring_constant = []
        self.spring_rotation_constant = []

    def load(self, fs):
        self.name = fs.readStr(20)

        self.src_rigid = fs.readUnsignedInt()
        self.dest_rigid = fs.readUnsignedInt()

        self.location = fs.readVector(3)
        self.rotation = fs.readVector(3)

        self.maximum_location = fs.readVector(3)
        self.minimum_location = fs.readVector(3)
        self.maximum_rotation = fs.readVector(3)
        self.minimum_rotation = fs.readVector(3)

        self.spring_constant = fs.readVector(3)
        self.spring_rotation_constant = fs.readVector(3)

class Model:
    def __init__(self):
        self.header = None
        self.vertices = []
        self.faces = []
        self.materials = []
        self.iks = []
        self.morphs = []
        self.facial_disp_names = []
        self.bone_disp_names = []
        self.bone_disp_lists = {}
        self.name = ''
        self.comment = ''
        self.name_e = ''
        self.comment_e = ''
        self.toon_textures = []
        self.rigid_bodies = []
        self.joints = []


    def load(self, fs):
        logging.info('importing pmd model from %s...', fs.path())

        header = Header()
        header.load(fs)

        self.name = header.model_name
        self.comment = header.comment

        logging.info('model name: %s', self.name)
        logging.info('comment: %s', self.comment)

        logging.info('importing vertices...')
        self.vertices = []
        vert_count = fs.readUnsignedInt()
        for i in range(vert_count):
            v = Vertex()
            v.load(fs)
            self.vertices.append(v)
        logging.info('the number of vetices: %d', len(self.vertices))
        logging.info('finished importing vertices.')

        logging.info('importing faces...')
        self.faces = []
        face_vert_count = fs.readUnsignedInt()
        for i in range(int(face_vert_count/3)):
            f1 = fs.readUnsignedShort()
            f2 = fs.readUnsignedShort()
            f3 = fs.readUnsignedShort()
            self.faces.append((f3, f2, f1))
        logging.info('the number of faces: %d', len(self.faces))
        logging.info('finished importing faces.')

        logging.info('importing materials...')
        self.materials = []
        material_count = fs.readUnsignedInt()
        for i in range(material_count):
            mat = Material()
            mat.load(fs)
            self.materials.append(mat)
        logging.info('the number of materials: %d', len(self.materials))
        logging.info('finished importing materials.')

        logging.info('importing bones...')
        self.bones = []
        bone_count = fs.readUnsignedShort()
        for i in range(bone_count):
            bone = Bone()
            bone.load(fs)
            self.bones.append(bone)
        logging.info('the number of bones: %d', len(self.bones))
        logging.info('finished importing bones.')

        logging.info('importing IKs...')
        self.iks = []
        ik_count = fs.readUnsignedShort()
        for i in range(ik_count):
            ik = IK()
            ik.load(fs)
            logging.debug(ik)
            self.iks.append(ik)
        logging.info('the number of IKs: %d', len(self.iks))
        logging.info('finished importing IKs.')

        logging.info('importing morphs...')
        self.morphs = []
        morph_count = fs.readUnsignedShort()
        for i in range(morph_count):
            morph = VertexMorph()
            morph.load(fs)
            self.morphs.append(morph)
        logging.info('the number of morphs: %d', len(self.morphs))
        logging.info('finished importing morphs.')

        logging.info('importing display items...')
        self.facial_disp_morphs = []
        t = fs.readByte()
        for i in range(t):
            self.facial_disp_morphs.append(fs.readUnsignedShort())

        self.bone_disp_lists = collections.OrderedDict()
        bone_disps = []
        t = fs.readByte()
        for i in range(t):
            name = fs.readStr(50)
            self.bone_disp_lists[name] = []
            bone_disps.append(name)

        t = fs.readUnsignedInt()
        for i in range(t):
            bone_index = fs.readUnsignedShort()
            disp_index = fs.readByte()
            self.bone_disp_lists[bone_disps[disp_index-1]].append(bone_index)

        logging.info('try to load extended data sections...')
        # try to load extended data sections.
        try:
            eng_flag = fs.readByte()
        except e:
            logging.info('found no extended data sections')
            return

        if eng_flag:
            logging.info('found a extended data for english.')
            self.name_e = fs.readStr(20)
            self.comment_e = fs.readStr(256)
            for i in range(len(self.bones)):
                self.bones[i].name_e = fs.readStr(20)

            for i in range(1, len(self.morphs)):
                self.morphs[i].name_e = fs.readStr(20)

            bone_disps_e = []
            for i in range(len(bone_disps)):
                bone_disps_e.append(fs.readStr(50))
            logging.info('''name_e: %s
comment_e: %s''', self.name_e, self.comment_e)

        logging.info('importing toon textures...')
        self.toon_textures = []
        for i in range(10):
            self.toon_textures.append(fs.readStr(100))
        logging.info('the number of joints: %d', len(self.toon_textures))
        logging.info('finished importing joints.')

        logging.info('importing rigid bodies...')
        rigid_count = fs.readUnsignedInt()
        self.rigid_bodies = []
        for i in range(rigid_count):
            rigid = RigidBody()
            rigid.load(fs)
            self.rigid_bodies.append(rigid)
        logging.info('the number of rigid bodies: %d', len(self.rigid_bodies))
        logging.info('finished importing rigid bodies.')

        logging.info('importing joints...')
        joint_count = fs.readUnsignedInt()
        self.joints = []
        for i in range(joint_count):
            joint = Joint()
            joint.load(fs)
            self.joints.append(joint)
        logging.info('the number of joints: %d', len(self.joints))
        logging.info('finished importing joints.')
        logging.info('finished importing the model.')

def load(path):
    with FileReadStream(path) as fs:
        model = Model()
        model.load(fs)
        return model
