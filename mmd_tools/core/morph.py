

class FnMorph(object):
    
    def __init__(self, morph, model):
        self.__morph = morph
        self.__rig = model
    
    def update_mat_related_mesh(self, new_mesh=None):
        for offset in self.__morph.data:
            # Use the new_mesh if provided  
            meshObj = new_mesh          
            if new_mesh is None:
                # Try to find the mesh by material name
                meshObj = self.__rig.findMesh(offset.material)
            
            if meshObj is None:
                # Given this point we need to loop through all the meshes
                for mesh in self.__rig.meshes():
                    if mesh.data.materials.find(offset.material) >= 0:
                        meshObj = mesh
                        break

            # Finally update the reference
            if meshObj is not None:
                offset.related_mesh = meshObj.data.name
            