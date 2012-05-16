# -*- coding: utf-8 -*-
import struct
import collections


## vmd仕様の文字列をstringに変換
def _toShiftJisString(byteString):
    try:
        eindex = byteString.index(b"\x00")
    except Exception:
        eindex = -1
    if eindex < len(byteString):
        byteString = byteString[0:eindex]
    return byteString.decode("shift_jis")


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
        self.interp = list(struct.unpack('<64s', fin.read(64)))

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
        self.length = 0.0
        self.location = []
        self.rotation = []
        self.interp = []
        self.angle = 0.0
        self.persp = True

    def load(self, fin):
        self.frame_number, = struct.unpack('<L', fin.read(4))
        self.length, = struct.unpack('<f', fin.read(4))
        self.location = list(struct.unpack('<fff', fin.read(4*3)))
        self.rotation = list(struct.unpack('<fff', fin.read(4*3)))
        self.interp = list(struct.unpack('<24s', fin.read(24)))
        self.angle, = struct.unpack('<f', fin.read(4))
        self.persp, = struct.unpack('<b', fin.read(1))
        self.persp = (self.persp == 1)

    def __repr__(self):
        return '<CameraKeyFrameKey frame %s, length %s, loc %s, rot %s, angle %s, persp %s>'%(
            str(self.frame_number),
            str(self.length),
            str(self.location),
            str(self.rotation),
            str(self.angle),
            str(self.persp),
            )

class _AnimationBase(collections.defaultdict):
    def __init__(self):
        collections.defaultdict.__init__(self, list)

    def load(self, fin):
        count, = struct.unpack('<L', fin.read(4))
        for i in range(count):
            name = _toShiftJisString(struct.unpack('<15s', fin.read(15))[0])
            cls = self.frameClass()
            frameKey = cls()
            frameKey.load(fin)
            print(frameKey)
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


class CameraAnimation(_AnimationBase):
    def __init__(self):
        _AnimationBase.__init__(self)

    @staticmethod
    def frameClass():
        return CameraFrameKey


class File:
    def __init__(self):
        self.header = None
        self.boneAnimation = None
        self.shapeKeyAnimation = None
        self.CameraAnimation = None

    def load(self, **args):
        path = args['filepath']

        with open(path, 'rb') as fin:
            self.header = Header()
            self.boneAnimation = BoneAnimation()
            self.shapeKeyAnimation = ShapeKeyAnimation()
            self.cameraAnimetion = CameraAnimation()

            self.header.load(fin)
            self.boneAnimation.load(fin)
            self.shapeKeyAnimation.load(fin)
            self.cameraAnimetion.load(fin)

            print(self.boneAnimation)
            print(self.shapeKeyAnimation)
            print(self.cameraAnimetion)

if __name__ == '__main__':
    vmdFile = File()
    vmdFile.load(filepath='/Users/yoshinobu/cg/tmp/import_vmd/scenes/Yellow.vmd')
