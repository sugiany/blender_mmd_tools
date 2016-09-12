# -*- coding: utf-8 -*-

import mathutils


class VMDExporter:

    @staticmethod
    def makeVMDBoneLocationMatrix(blender_bone):
        #mat = mathutils.Matrix([
        #        [blender_bone.x_axis.x, blender_bone.x_axis.y, blender_bone.x_axis.z, 0.0],
        #        [blender_bone.y_axis.x, blender_bone.y_axis.y, blender_bone.y_axis.z, 0.0],
        #        [blender_bone.z_axis.x, blender_bone.z_axis.y, blender_bone.z_axis.z, 0.0],
        #        [0.0, 0.0, 0.0, 1.0]
        #        ])
        mat = blender_bone.bone.matrix_local.to_3x3().transposed().to_4x4()
        mat2 = mathutils.Matrix([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]])
        return mat2 * mat.inverted()

    @staticmethod
    def convertToVMDBoneRotation(blender_bone, rotation):
        #mat = mathutils.Matrix()
        #mat[0][0], mat[1][0], mat[2][0] = blender_bone.x_axis.x, blender_bone.y_axis.x, blender_bone.z_axis.x
        #mat[0][1], mat[1][1], mat[2][1] = blender_bone.x_axis.y, blender_bone.y_axis.y, blender_bone.z_axis.y
        #mat[0][2], mat[1][2], mat[2][2] = blender_bone.x_axis.z, blender_bone.y_axis.z, blender_bone.z_axis.z
        mat = blender_bone.bone.matrix_local.to_3x3().transposed().to_4x4()
        (vec, angle) = rotation.to_axis_angle()
        vec = mat.inverted() * vec
        v = mathutils.Vector((-vec.x, -vec.z, -vec.y))
        return mathutils.Quaternion(v, angle).normalized()

