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
* Influence of .sph textures and influence of .spa textures
    * Used to set the diffuse_color_factor of texture slot for sphere textures.

### Import Motion
Apply motion imported from vmd file to the Armature, Mesh and Camera currently selected.
* Scale
    * Recommended to make it the same as the imported model's scale
* Margin
    * It is used to add/offset some frames before the motion start, so the rigid bodies can have more smooth transition at the beginning
* Update scene settings
    * Performs automatic setting of the camera range and frame rate after the motion data read.


Notes
------
* If camera and character motions are not in one file, import two times. First, select Armature and Mesh and import the character motion. Second, select Camera and import the camera motion.
* When mmd_tool imports motion data, mmd_tool uses the bone name to apply motion to each bone.
    * If the bone name and the bones structure matches with MMD model, you can import the motion to any model.
    * When you import MMD model by using other than mmd_tools, match bone names to those in MMD model.
* mmd_tools creates an empty model named "MMD_Camera" and assigns the motion to the object.
* If you want to import multiple motions or want to import motion with offset, edit the motion with NLA editor.
* If the origin point of the motion is significantly different from the origin point of the model, rigid body simulation might break. If this happens, increase "margin" parameter in vmd import.
* mmd_tool adds blank frames to avoid the glitch from physics simulation. The number of the blank frames is "margin" parameter in vmd import.
    * The imported motion starts from the frame number "margin" + 1. (e.g. If margin is 5, frame 6 is frame 0 in vmd motion)
* pmx import
    * If the weight information is SDEF, mmd_tool processes as if it is in BDEF2.
    * mmd_tool only supports vertex morph.
    * mmd_tool treats "Physics + Bone location match" in rigid body setting as "Physics simulation".
* Use the same scale in case you imports multiple pmx files.


Known issues
----------
* None, feel free to report some
    
    
License
----------
&Copy; 2012-2014 sugiany
Distributed under the MIT License.
