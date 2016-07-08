mmd_tools
===========

Overview
----
mmd_tools is a blender import addon for importing MMD (MikuMikuDance) model data (.pmd, .pmx) and motion data (.vmd)

### Environment

#### Compatible Version
blender 2.67 or later

Usage
---------
### Download

* Download mmd_tools from [the github repository](https://github.com/powroupi/blender_mmd_tools/tree/dev_test) (dev_test branch)
    * https://github.com/powroupi/blender_mmd_tools/archive/dev_test.zip

### Install
Extract the archive and put the folder mmd__tools into the addon folder of blender.

    .../blender-2.67-windows64/2.67/scripts/addons/

### Loading Addon
1. User Preferences -> addon tab -> select the User filter and click the checkbox before mmd_tools (you can also find the addon using the search function)
2. After the installation, you can find two panels called mmd_tools and mmd_utils on the left of the 3D view

### Importing a model
1. Go to the mmd_tools panel
2. Press _Import Model_ and select a .pmx or .pmd file


### Importing motion data
1. Load the MMD model. Then, select the imported model's Mesh, Armature and Camera.
2. Click the _Import Motion_ button of the mmd_tools panel.
3. If a rigid body simulation is needed, press the _Build_ button in the same panel.

Turn on "update scene settings" checkbox to automatically update scene settings such as frame range after the motion import.


Various functions in detail
-------------------------------
### Import Model
Imports a MMD model. Corresponding file formats are .pmd and .pmx (version 2.0).

* Scale
    * Size of the model
* Rename bones
    * Renames the bones to be more blender suitable
* Use MIP map for UV textures
    * Specify if mipmaps will be generated
    * Please turn it off when the textures seem messed up
* Influence of .sph textures
    * Specifies the strength of the sphere map <a></a>
* Influence of .spa textures
    * Specifies the strength of the sphere map <a></a>

### Import Motion
Imports some motion from a .vmd file for the currently selected armature/bones
* Scale
    * Recommended to make it the same as the imported model's scale
* Margin <a></a>
    * The margin frame for the physical simulation.
    * If the initial position of the motion is far away from the origin, physical simulation will collapse because the model would move the moment when the motion begins.
    To work around this behavior, insert a blank space between the timeline start and motion the beginning of the blender.
    * There is also the effect of stabilizing the rigid body at the time of the motion start.
* Update scene settings
    * Performs automatic setting of the camera range and frame rate after the motion data read.


Other
------
* If the camera and the character motion is in a different file, character motion to select the Armature and Mesh, please be imported in two so that the camera motion to select the Camera.
* When you import the motion data will apply the motion to each bone using a bone names.
    * If the bone name and the structure is consistent with the MMD model, it is possible import of motion in the original model, and the like.
    * If you want to load the MMD model by a method other than mmd_tools, please be bone name to match the MMD model.
* The camera generates a Empty object named MMD_Camera, it will be assigned to the motion to this object.
* If you want to import with the offset to or frame if you want to import more than one motion, please edit the animation in the NLA editor.
* If the initial position of the animation is far away and the origin of the model, you may be rigid body simulation to collapse. In that case, please increase the vmd import parameters "margin".
* Motion data because to prevent the collapse of the physical simulation "margin" is added. This margin is the value of the "margin" is specified at the time of vmd import.
    * Imported motion body will start from the value +1 frame of the "margin". (Example: If the margin = 5, 6 th frame becomes the 0-th frame of vmd motion)
For * pmx import
    * If the weight information of the vertex of SDEF, do the same treatment as the BDEF2.
    * It does not correspond to morph information other than the vertex morph.
    * Rigid setting "physical + bone alignment" is treated as "physics".
* If you want to import multiple pmx files, please unified scale.


Known problems
----------
* Because you are forcibly resolve the non-collision group of rigid body, you may want to freeze When you import a model number of rigid body often.
    * Well, this is not exactly a complete freeze, it just is taking unusual time to read.
    * If you want to load the freeze to model, please put a check to "ignore non collision groups" option.
    * If you turn on the above-mentioned options, unintended rigid bodies is interference, there is a possibility that normal physical simulation does not work.
* "Movement grant" bone does not work correctly.
* If the object of the coordinate (root of empty and Armature) is moved from the origin, it may bone structure to collapse.
    * If you want to move the model, without the movement of an object mode, please move the bone, such as "center" or "all of the parent" in Pose Mode.
    * Status quo, because resolution is difficult, it is recommended that you do not move operation in the object mode.


License
----------
&Copy; 2012-2014 sugiany
Distributed under the MIT License.
