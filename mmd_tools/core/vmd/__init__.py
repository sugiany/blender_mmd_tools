# -*- coding: utf-8 -*-
import struct
import collections


## vmd仕様の文字列をstringに変換
def _toShiftJisString(byteString):
    byteString = byteString.split(b"\x00")[0]
    try:
        return byteString.decode("shift_jis")
    except UnicodeDecodeError:
        # discard truncated sjis char
        return byteString[:-1].decode("shift_jis")


class Header:
    def __init__(self):
        self.signature = None
        self.model_name = ''

    def load(self, fin):
        self.signature, = struct.unpack('<30s', fin.read(30))
        self.model_name = _toShiftJisString(struct.unpack('<20s', fin.read(20))[0])

    def __repr__(self):
        return '<Header model_name %s>'%(self.model_name)


class BoneFrameKey:
    def __init__(self):
        self.frame_number = 0
        self.location = []
        self.rotation = []
        self.interp = []

    def load(self, fin):
        self.frame_number, = struct.unpack('<L', fin.read(4))
        self.location = list(struct.unpack('<fff', fin.read(4*3)))
        self.rotation = list(struct.unpack('<ffff', fin.read(4*4)))
        self.interp = list(struct.unpack('<64b', fin.read(64)))

    def __repr__(self):
        return '<BoneFrameKey frame %s, loa %s, rot %s>'%(
            str(self.frame_number),
            str(self.location),
            str(self.rotation),
            )


class ShapeKeyFrameKey:
    def __init__(self):
        self.frame_number = 0
        self.weight = 0.0

    def load(self, fin):
        self.frame_number, = struct.unpack('<L', fin.read(4))
        self.weight, = struct.unpack('<f', fin.read(4))

    def __repr__(self):
        return '<ShapeKeyFrameKey frame %s, weight %s>'%(
            str(self.frame_number),
            str(self.weight),
            )


class CameraKeyFrameKey:
    def __init__(self):
        self.frame_number = 0
        self.distance = 0.0
        self.location = []
        self.rotation = []
        self.interp = []
        self.angle = 0.0
        self.persp = True

    def load(self, fin):
        self.frame_number, = struct.unpack('<L', fin.read(4))
        self.distance, = struct.unpack('<f', fin.read(4))
        self.location = list(struct.unpack('<fff', fin.read(4*3)))
        self.rotation = list(struct.unpack('<fff', fin.read(4*3)))
        self.interp = list(struct.unpack('<24b', fin.read(24)))
        self.angle, = struct.unpack('<L', fin.read(4))
        self.persp, = struct.unpack('<b', fin.read(1))
        self.persp = (self.persp == 1)

    def __repr__(self):
        return '<CameraKeyFrameKey frame %s, distance %s, loc %s, rot %s, angle %s, persp %s>'%(
            str(self.frame_number),
            str(self.distance),
            str(self.location),
            str(self.rotation),
            str(self.angle),
            str(self.persp),
            )


class LampKeyFrameKey:
    def __init__(self):
        self.frame_number = 0
        self.color = []
        self.direction = []

    def load(self, fin):
        self.frame_number, = struct.unpack('<L', fin.read(4))
        self.color = list(struct.unpack('<fff', fin.read(4*3)))
        self.direction = list(struct.unpack('<fff', fin.read(4*3)))

    def __repr__(self):
        return '<LampKeyFrameKey frame %s, color %s, direction %s>'%(
            str(self.frame_number),
            str(self.color),
            str(self.direction),
            )


class _AnimationBase(collections.defaultdict):
    def __init__(self):
        collections.defaultdict.__init__(self, list)

    @staticmethod
    def frameClass():
        raise NotImplementedError

    def load(self, fin):
        count, = struct.unpack('<L', fin.read(4))
        for i in range(count):
            name = _toShiftJisString(struct.unpack('<15s', fin.read(15))[0])
            cls = self.frameClass()
            frameKey = cls()
            frameKey.load(fin)
            self[name].append(frameKey)

            
class BoneAnimation(_AnimationBase):
    def __init__(self):
        _AnimationBase.__init__(self)

    @staticmethod
    def frameClass():
        return BoneFrameKey
        

class ShapeKeyAnimation(_AnimationBase):
    def __init__(self):
        _AnimationBase.__init__(self)

    @staticmethod
    def frameClass():
        return ShapeKeyFrameKey


class CameraAnimation(list):
    def __init__(self):
        list.__init__(self)
        self = []

    @staticmethod
    def frameClass():
        return CameraKeyFrameKey

    def load(self, fin):
        count, = struct.unpack('<L', fin.read(4))
        for i in range(count):
            cls = self.frameClass()
            frameKey = cls()
            frameKey.load(fin)
            self.append(frameKey)


class LampAnimation(list):
    def __init__(self):
        list.__init__(self)
        self = []

    @staticmethod
    def frameClass():
        return LampKeyFrameKey

    def load(self, fin):
        count, = struct.unpack('<L', fin.read(4))
        for i in range(count):
            cls = self.frameClass()
            frameKey = cls()
            frameKey.load(fin)
            self.append(frameKey)


class File:
    def __init__(self):
        self.filepath = None
        self.header = None
        self.boneAnimation = None
        self.shapeKeyAnimation = None
        self.cameraAnimation = None
        self.lampAnimation = None

    def load(self, **args):
        path = args['filepath']

        with open(path, 'rb') as fin:
            self.filepath = path
            self.header = Header()
            self.boneAnimation = BoneAnimation()
            self.shapeKeyAnimation = ShapeKeyAnimation()
            self.cameraAnimation = CameraAnimation()
            self.lampAnimation = LampAnimation()

            self.header.load(fin)
            self.boneAnimation.load(fin)
            self.shapeKeyAnimation.load(fin)
            try:
                self.cameraAnimation.load(fin)
                self.lampAnimation.load(fin)
            except struct.error:
                pass # no valid camera/lamp data
