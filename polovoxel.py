bl_info = {
    "name": "Polovoxel Add-on",
    "blender": (2, 80, 0),
    "category": "Object",
}

import bpy


import bmesh

context = bpy.context
ob = context.edit_object

me = ob.data

bm = bmesh.from_edit_mesh(me)
# list of selected faces
selfaces = [f for f in bm.faces if f.select]
cube_location = selfaces[0].calc_center_median()


if selfaces:
    print("%d faces selected" % len(selfaces))
else:
    print("No Faces Selected")

bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=cube_location, scale=(1, 1, 1))


'''
cube_scale = (1, 1, 1)
cube_color = (0, 0, 1, 1)
cube_location = (0, 1, 0)

bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=cube_location, scale=cube_scale)
cube_obj = bpy.context.object

mat_name = cube_obj.name

# Get material
mat = bpy.data.materials.get(mat_name)
if mat is None:
    # create material
    mat = bpy.data.materials.new(name=mat_name)

mat.diffuse_color = cube_color

# Assign it to object
if cube_obj.data.materials:
    # assign to 1st material slot
    cube_obj.data.materials[0] = mat
else:
    # no slots
    cube_obj.data.materials.append(mat)
'''    

'''

class ObjectMoveX(bpy.types.Operator):
    """My Object Moving Script"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "object.move_x"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Move X by One"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    def execute(self, context):        # execute() is called when running the operator.

        # The original script
        scene = context.scene
        for obj in scene.objects:
            obj.location.x += 1.0

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

def menu_func(self, context):
    self.layout.operator(ObjectMoveX.bl_idname)

def register():
    bpy.utils.register_class(ObjectMoveX)
    bpy.types.VIEW3D_MT_object.append(menu_func)  # Adds the new operator to an existing menu.

def unregister():
    bpy.utils.unregister_class(ObjectMoveX)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
    
'''