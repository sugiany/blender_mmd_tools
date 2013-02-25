import bpy
import mathutils
import math

class MMDCamera:
    def __init__(self, obj):
        if obj.type != 'EMPTY':
            if obj.parent is None or obj.type != 'CAMERA':
                raise ValueError('%s is not MMDCamera'%str(obj))
            obj = obj.parent
        if obj.type == 'EMPTY' and obj.get('is_mmd_camera', False):
            self.__emptyObj = obj
        else:
            raise ValueError('%s is not MMDCamera'%str(obj))


    @staticmethod
    def isMMDCamera(obj):
        if obj.type != 'EMPTY':
            if obj.parent is None or obj.type != 'CAMERA':
                return False
            obj = obj.parent
        return obj.type == 'EMPTY' and obj.get('is_mmd_camera', False)


    @staticmethod
    def __setDrivers(empty, camera):
        driver = camera.driver_add('location', 1).driver
        driverVar = driver.variables.new()
        driverVar.name = 'mmd_distance'
        driverVar.type = 'SINGLE_PROP'
        driverVar.targets[0].id_type = 'OBJECT'
        driverVar.targets[0].id = empty
        driverVar.targets[0].data_path = 'mmd_camera_distance'
        driver.type = 'SCRIPTED'
        driver.expression = '-%s'%driverVar.name

        driver = camera.data.driver_add('lens').driver
        angle = driver.variables.new()
        angle.name = 'mmd_distance'
        angle.type = 'SINGLE_PROP'
        angle.targets[0].id_type = 'OBJECT'
        angle.targets[0].id = empty
        angle.targets[0].data_path = 'mmd_camera_angle'

        sensorHeight = driver.variables.new()
        sensorHeight.name = 'sensor_height'
        sensorHeight.type = 'SINGLE_PROP'
        sensorHeight.targets[0].id_type = 'OBJECT'
        sensorHeight.targets[0].id = camera
        sensorHeight.targets[0].data_path = 'data.sensor_height'

        driver.type = 'SCRIPTED'
        driver.expression = '%s/(2*tan(radians(%s)/2))'%(sensorHeight.name, angle.name)


    @staticmethod
    def convertToMMDCamera(cameraObj):
        import bpy
        import mathutils
        if MMDCamera.isMMDCamera(cameraObj):
            return MMDCamera(cameraObj)

        name = cameraObj.name
        cameraObj.name = name + '_mmd'
        empty = bpy.data.objects.new(name=name, object_data=None)
        bpy.context.scene.objects.link(empty)

        empty.rotation_mode = 'YXZ'
        empty.is_mmd_camera = True
        empty.mmd_camera_distance = 0.0
        empty.mmd_camera_angle = 45
        empty.mmd_camera_persp = True
        cameraObj.parent = empty
        cameraObj.data.sensor_fit = 'VERTICAL'
        cameraObj.location = mathutils.Vector((0,0,0))
        cameraObj.rotation_mode = 'XYZ'
        cameraObj.rotation_euler = mathutils.Vector((math.radians(90.0),0,0))
        cameraObj.lock_location = (True, False, True)
        cameraObj.lock_rotation = (True, True, True)
        cameraObj.lock_scale = (True, True, True)

        MMDCamera.__setDrivers(empty, cameraObj)

        return MMDCamera(empty)

    def object(self):
        return self.__emptyObj
