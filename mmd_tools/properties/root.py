# -*- coding: utf-8 -*-
""" MMDモデルパラメータ用Prop
"""
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, FloatProperty, IntProperty, StringProperty, EnumProperty
from mmd_tools import rigging
from . import register_property


#===========================================
# Callback functions
#===========================================
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



#===========================================
# Property classes
#===========================================

class MMDDisplayItem(PropertyGroup):
    """ PMX 表示項目(表示枠内の1項目)
    """
    type = EnumProperty(
        name='Type',
        items = [
            ('BONE', 'Bone', '', 1),
            ('MORPH', 'Morph', '', 2),
            ],
        )

class MMDDisplayItemFrame(PropertyGroup):
    """ PMX 表示枠

     PMXファイル内では表示枠がリストで格納されています。
    """
    name_e = StringProperty(
        name='Name(Eng)',
        description='English Name',
        default='',
        )

    ## 特殊枠フラグ
    # 特殊枠はファイル仕様上の固定枠(削除、リネーム不可)
    is_special = BoolProperty(
        name='Special',
        default=False,
        )

    ## 表示項目のリスト
    items = CollectionProperty(
        name='Display Items',
        type=MMDDisplayItem,
        )

    ## 現在アクティブな項目のインデックス
    active_item = IntProperty(
        name='Active Display Item',
        default=0,
        )


@register_property(bpy.types.Object, 'mmd_root')
class MMDRoot(PropertyGroup):
    """ MMDモデルデータ

     モデルルート用に作成されたEmtpyオブジェクトで使用します
    """
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

    display_item_frames = CollectionProperty(
        name='Display Frames',
        type=MMDDisplayItemFrame,
        )

    active_display_item_frame = IntProperty(
        name='Active Display Item Frame',
        default=0,
        )
