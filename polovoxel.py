bl_info = {
    "name": "Polovoxel Add-on",
    "blender": (2, 80, 0),
    "category": "Object",
}


import bpy
import bmesh
from mathutils import *


def get_first_selected_face_center_location():
    context = bpy.context

    ob = context.edit_object
    me = ob.data
    bm = bmesh.from_edit_mesh(me)

    # list of selected faces
    selfaces = [f for f in bm.faces if f.select]
    
    if selfaces:
        face = selfaces[0]
        selected_cube_pos = (ob.matrix_world[0][3], ob.matrix_world[1][3], ob.matrix_world[2][3])
        point_location = face.calc_center_median() + Vector(selected_cube_pos)
        return (point_location, face.normal)
    else:
        return (None, None)


def setup_obj_material(cube_obj, name, color):
    # Get material
    mat = bpy.data.materials.get(name)
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name=mat_name)
        mat.diffuse_color = color

    # Assign it to object
    if cube_obj.data.materials:
        # assign to 1st material slot
        cube_obj.data.materials[0] = mat
    else:
        # no slots
        cube_obj.data.materials.append(mat)


def create_cube(cube_location, cube_scale, mat_name, cube_color):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=cube_location, scale=cube_scale)
    bpy.ops.object.mode_set(mode='EDIT')
    
    context = bpy.context
    cube_obj = context.object
    
    setup_obj_material(cube_obj, mat_name, cube_color)


selected_center_location, selected_normal = get_first_selected_face_center_location()    

if selected_center_location:
    cube_scale = (1, 1, 1)
    cube_location = selected_center_location + (selected_normal * Vector(cube_scale))
    
    mat_name = 'green'
    cube_color = (0, 1, 0, 1)
    
    create_cube(cube_location, cube_scale, mat_name, cube_color)

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