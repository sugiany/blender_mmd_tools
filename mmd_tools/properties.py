# -*- coding: utf-8 -*-

import math

import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, BoolVectorProperty, CollectionProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, StringProperty, PointerProperty

from .pmx import Material, Rigid
from . import rigging
from . import mmd_camera


############################################
# Functions for MMD Root update callbacks. #
############################################
def _toggleVisibilityOfMeshes(self, context):
    root = self.id_data
    rig = rigging.Rig(root)
    objects = list(rig.meshes())
    hide = not self.show_meshes
    if hide and context.active_object in objects:
        context.scene.objects.active = root
    for i in objects:
        i.hide = hide

def _toggleVisibilityOfRigidBodies(self, context):
    root = self.id_data
    rig = rigging.Rig(root)
    objects = list(rig.rigidBodies())
    hide = not self.show_rigid_bodies
    if hide and context.active_object in objects:
        context.scene.objects.active = root
    for i in objects:
        i.hide = hide

def _toggleVisibilityOfJoints(self, context):
    root = self.id_data
    rig = rigging.Rig(root)
    objects = list(rig.joints())
    hide = not self.show_joints
    if hide and context.active_object in objects:
        context.scene.objects.active = root
    for i in objects:
        i.hide = hide

def _toggleVisibilityOfTemporaryObjects(self, context):
    root = self.id_data
    rig = rigging.Rig(root)
    objects = list(rig.temporaryObjects())
    hide = not self.show_temporary_objects
    if hide and context.active_object in objects:
        context.scene.objects.active = root
    for i in objects:
        i.hide = hide

def _toggleShowNamesOfRigidBodies(self, context):
    root = self.id_data
    rig = rigging.Rig(root)
    objects = list(rig.rigidBodies())
    for i in objects:
        i.show_name = root.mmd_root.show_names_of_rigid_bodies

def _toggleShowNamesOfJoints(self, context):
    root = self.id_data
    rig = rigging.Rig(root)
    objects = list(rig.joints())
    for i in objects:
        i.show_name = root.mmd_root.show_names_of_joints

def _setVisibilityOfMMDRigArmature(obj, v):
    rig = rigging.Rig(obj)
    arm = rig.armature()
    if bpy.context.active_object == arm:
        bpy.context.scene.objects.active = obj
    arm.hide = not v

class MMDRoot(PropertyGroup):
    name = StringProperty(
        name='Name',
        default='',
        )

    name_e = StringProperty(
        name='Name (English)',
        default='',
        )

    show_meshes = BoolProperty(
        name='Show Meshes',
        update=_toggleVisibilityOfMeshes,
        )

    show_rigid_bodies = BoolProperty(
        name='Show Rigid Bodies',
        update=_toggleVisibilityOfRigidBodies,
        )

    show_joints = BoolProperty(
        name='Show Joints',
        update=_toggleVisibilityOfJoints,
        )

    show_temporary_objects = BoolProperty(
        name='Show Temps',
        update=_toggleVisibilityOfTemporaryObjects,
        )

    show_armature = BoolProperty(
        name='Show Armature',
        get=lambda x: not rigging.Rig(x.id_data).armature().hide,
        set=lambda x, v: _setVisibilityOfMMDRigArmature(x.id_data, v),
        )

    show_names_of_rigid_bodies = BoolProperty(
        name='Show Rigid Body Names',
        update=_toggleShowNamesOfRigidBodies,
        )

    show_names_of_joints = BoolProperty(
        name='Show Joint Names',
        update=_toggleShowNamesOfJoints,
        )

    scale = FloatProperty(
        name='Scale',
        min=0.1,
        default=1,
        )

    is_built = BoolProperty(
        name='Is Built',
        )

class MMDMaterial(PropertyGroup):
    name_j = StringProperty(
        name='Name',
        description='Japanese Name',
        default='',
        )

    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='',
        )

    ambient_color = FloatVectorProperty(
        name='Ambient',
        subtype='COLOR',
        size=3,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0],
        )

    is_double_sided = BoolProperty(
        name='Double Sided',
        description='',
        default=True,
        )

    enabled_drop_shadow = BoolProperty(
        name='Drop Shadow',
        description='',
        default=True,
        )

    enabled_self_shadow_map = BoolProperty(
        name='Self Shadow Map',
        description='',
        default=True,
        )

    enabled_self_shadow = BoolProperty(
        name='Self Shadow',
        description='',
        default=True,
        )

    enabled_toon_edge = BoolProperty(
        name='Toon Edge',
        description='',
        default=True,
        )

    edge_color = FloatVectorProperty(
        name='Edge Color',
        subtype='COLOR',
        size=4,
        min=0,
        max=1,
        precision=3,
        step=0.1,
        default=[0, 0, 0, 1],
        )

    edge_weight = FloatProperty(
        name='Edge Weight',
        min=0,
        max=100,
        step=0.1,
        default=0.5,
        )

    sphere_texture_type = EnumProperty(
        name='Sphere Map Type',
        description='',
        items = [
            (str(Material.SPHERE_MODE_OFF), 'Off', '', 1),
            (str(Material.SPHERE_MODE_MULT), 'Multiply', '', 2),
            (str(Material.SPHERE_MODE_ADD), 'Add', '', 3),
            (str(Material.SPHERE_MODE_SUBTEX), 'SubTexture', '', 4),
            ],
        )

    comment = StringProperty(
        name='Comment',
        )

def _getMMDCameraAngle(prop):
    empty = prop.id_data
    cam = mmd_camera.MMDCamera(empty).camera()
    return math.atan(cam.data.sensor_height/cam.data.lens/2) * 2

def _setMMDCameraAngle(prop, value):
    empty = prop.id_data
    cam = mmd_camera.MMDCamera(empty).camera()
    cam.data.lens = cam.data.sensor_height/math.tan(value/2)/2

class MMDCamera(PropertyGroup):
    angle = FloatProperty(
        name='Angle',
        subtype='ANGLE',
        get=_getMMDCameraAngle,
        set=_setMMDCameraAngle,
        min=0.1,
        max=math.radians(180),
        step=0.1,
        )

    is_perspective = BoolProperty(
        name='Perspective',
        default=True,
        )

class MMDBone(PropertyGroup):
    name_j = StringProperty(
        name='Name',
        description='Japanese Name',
        default='',
        )

    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='',
        )


    transform_order = IntProperty(
        name='Transform Order',
        min=0,
        max=100,
        )

    is_visible = BoolProperty(
        name='Visible',
        default=True,
        )

    is_controllable = BoolProperty(
        name='Controllable',
        default=True,
        )


    transform_after_dynamics = BoolProperty(
        name='After Dynamics',
        default=False,
        )

    enabled_local_axes = BoolProperty(
        name='Use Local Axes',
        default=False,
        )

    local_axis_x = FloatVectorProperty(
        name='Local X-Axis',
        size=3,
        default=[1, 0, 0],
        )

    local_axis_z = FloatVectorProperty(
        name='Local Z-Axis',
        size=3,
        default=[0, 0, 1],
        )

    is_tip = BoolProperty(
        name='Tip Bone',
        default=False,
        )

class MMDRigid(PropertyGroup):
    name_j = StringProperty(
        name='Name',
        description='Japanese Name',
        default='',
        )

    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='',
        )

    collision_group_number = IntProperty(
        name='Collision Group',
        min=0,
        max=16,
        default=1,
        )

    collision_group_mask = BoolVectorProperty(
        name='Collision Group Mask',
        size=16,
        subtype='LAYER',
        )

    type = EnumProperty(
        name='Rigid Type',
        items = [
            (str(Rigid.MODE_STATIC), 'Static', '', 1),
            (str(Rigid.MODE_DYNAMIC), 'Dynamic', '', 2),
            (str(Rigid.MODE_DYNAMIC_BONE), 'Dynamic&BoneTrack', '', 3),
            ],
        )

    shape = EnumProperty(
        name='Shape',
        items = [
            ('SPHERE', 'Sphere', '', 1),
            ('BOX', 'Box', '', 2),
            ('CAPSULE', 'Capsule', '', 3),
            ],
        )

    bone = StringProperty(
        name='Bone',
        description='',
        default='',
        )

class MMDJoint(PropertyGroup):
    name_j = StringProperty(
        name='Name',
        description='Japanese Name',
        default='',
        )

    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='',
        )

    spring_linear = FloatVectorProperty(
        name='Spring(Linear)',
        size=3,
        min=0,
        step=0.1,
        )

    spring_angular = FloatVectorProperty(
        name='Spring(Angular)',
        size=3,
        min=0,
        step=0.1,
        )
