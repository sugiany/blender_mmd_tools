mmd_tools
===========

About
----
mmd_tools is a blender import addon for importing MMD (MikuMikuDance) model data (.pmd, .pmx) and motion data (.vmd)


### Environment

#### Compatible Version
blender 2.67 and later

#### Tested working environments
Windows 7 + blender 2.67 64bit

OSX + blender 2.67 64bit

Ubuntu + blender 2.67 64bit


Usage
---------
### Download

* download mmd_tools from our github repository.
    * https://github.com/sugiany/blender_mmd_tools
* Stable release can be found in the link below.
    * [Tags](https://github.com/sugiany/blender_mmd_tools/tags)
* Nightly release can be downloaded from the master, only basic functionality is tested working.
    * [master.zip](https://github.com/sugiany/blender_mmd_tools/archive/master.zip)

### Install
Extract the archive and put the folder mmd__tools into the addon folder of blender.

    .../blender-2.67-windows64/2.67/scripts/addons/

### Loading Addon
1. In User Preferences, under addon tab, select User filter and click the checkbox before mmd_tools
   (you can also find the addon my search)
2. After installation, you can find the panel called MMD on the left of 3D view

### Importing an MMD model data
1. Click "import/Model" button on mmd_tools panel.
2. Select a pmx file in the file select screen and mmd_tools imports the model.

### Importing a motion data
1. Import a model beforehand. Then select the imported model's Mesh, Armature and Camera. (For the items that you don't select, mmd_tools doesn't import motion)
2. Click "import/Motion" button on mmd_tools panel.
3. Select a vmd file in the file select screen and mmd_tools imports motions for the selected objects.
4. Turn on "update scene settings" checkbox to automatically update scene settings such as frame range after the motion import.


Feature details
-------------------------------
### Import Model
Import MMD model data. Supported formats are pmd and pmx(ver2.0).
Using the default option setting is recommended.
Turn on "import only non dynamics rigid bodies" if you don't want to import rigid body information.

* scale
    * Scaling factor for the model import. Use the same value when you import motion.
* rename bones
    * Rename the bone name to the one work well with blender. ("右腕" to "腕.L", etc...）
* hide rigid bodies and joints
    *  Hide objects that have rigid body information
* import only non dynamics rigid bodies
    * Import only rigid bodies that follows a bone. Use this feature when you don't need rigid body information. (e.g. using cloth and/or soft body)
* ignore non collision groups
    * If this option is set, mmd_tool doesn't import non collision groups. Use this when model import causes lockup.
* distance of ignore collisions
    * Specify the range of non collision group resolution distance
* use MIP map for UV textures
    * Turn on and off automatic MIPmap generation feature in Blender.
    * When you see purple colored noise in some textures with alpha channel, turn off this option.
* influence of .sph textures
    * Specify sphere map influence. (Min 0.0, Max 1.0)
* influence of .spa textures
    * Specify sphere map influence. (Min 0.0, Max 1.0)

### Import Motion
Apply motion imported from vmd file to the Armature, Mesh and Camera currently selected.

* scale
    * Scaling factor for the motion import. Use the same value you used when you imported model.
* margin
    * Specify the number of margin frames for physics simulation.
    * If the origin point of motion is significantly different from the model origin point, the model teleports at the beginning of the motion and physics simulation breaks.
    * To avoid this issue, this option inserts blank frames between the beginning of timeline and the motion start frame.
    * This option stabilizes rigid bodies at motion start frame too.
* update scene settings
    * Automatically set frame range and frame rate after motion data import.
    * mmd_tool adjusts the frame range so that blender can play all animation exists in the scene.
    * mmd_tool set the framerate to 30fps.

### Set frame range
Adjust the frame range so that blender can play all animation exists in the scene.
Set frame rate to 30fps.
* The same function as the update scene setting option in Import vmd.

### View

#### GLSL
Automatically performs setups required to display in GLSL mode.
* Switch Shading to GLSL.
* Turn off shadeless for all materials in the current scene.
* Add Hemi light.
* Change the shading of the 3D View in which this button is clicked to Textured.

#### Shadeless
Automatically performs setups required to display in Shadeless mode.
* Switch Shading to GLSL.
* Set shadeless for all materials in the current scene.
* Change the shading of the 3D View in which this button is clicked to Textured.

#### Cycles
Convert all materials for Cycles.
* This concert isn't based on any strict theory.
* mmd_tools doesn't display completion message. Confirm from the material panel or other UI.
* Change the shading of the 3D View in which this button is clicked to Material.
    * If you change shading of the 3D View to Rendered, you can preview Cycle in real time.
* mmd_tools doesn't change lighting. Changing World Color to white(1, 1, 1) works to some extent.

#### Reset
Reset the values changed by GLSL button to the original values.

#### Separate by materials
Divide the selected mesh object into multiple mesh objects based on the applied material. Then set each divided object name to the material name.
* mmd_tool uses blender's "Separate" > "By Material" feature.


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
* Resolution of rigid body non collision group is brute-force now. If the model has too many rigid bodies, import would cause lockup.
    * Accurately, the lockup is not a real lockup but import takes excessively long time.
    * When you import the model that causes this issue, turn on "ignore non collision groups" option.
    * When you turn on the option, undesired collision would occur among rigid bodies and physics simulation wouldn't work as expected.
* "Additional move" bones don't work as expected.
* The bone structure would break if you move the object (empty object at root and Armature) position from the origin.
    * If you want to move the model, use Pose Mode and move "Center" or "Parent of all" bone and don't use object mode.
    * Since resolving this issue is difficult, I recommend not to use Object mode to move objects.


Bug・Request・Questions etc.
------------------
Please submit a GitHub issue or contact me using twitter 
[@sugiany](https://twitter.com/sugiany)


Changelog
--------
Please refer to CHANGELOG.md


License
----------
&copy; 2012-2014 sugiany  
Distributed under the MIT License.  


