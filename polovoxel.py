from mathutils import *
import bmesh
import bpy
bl_info = {
    "name": "Polovoxel",
    "description": "",
    "author": "Polotto",
    "version": (0, 0, 3),
    "blender": (2, 80, 0),
    "location": "Object Properties > Polovoxel",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}


def get_first_selected_face_center_location():
    context = bpy.context

    ob = context.edit_object
    me = ob.data
    bm = bmesh.from_edit_mesh(me)

    # list of selected faces
    selfaces = [f for f in bm.faces if f.select]

    if selfaces:
        face = selfaces[0]
        selected_cube_pos = (
            ob.matrix_world[0][3], ob.matrix_world[1][3], ob.matrix_world[2][3])
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
    bpy.ops.mesh.primitive_cube_add(
        size=2, enter_editmode=False, align='WORLD', location=cube_location, scale=cube_scale)
    bpy.ops.object.mode_set(mode='EDIT')

    context = bpy.context
    cube_obj = context.object

    setup_obj_material(cube_obj, mat_name, cube_color)


selected_center_location, selected_normal = get_first_selected_face_center_location()

if selected_center_location:
    cube_scale = (1, 1, 1)
    cube_location = selected_center_location + \
        (selected_normal * Vector(cube_scale))

    mat_name = 'green'
    cube_color = (0, 1, 0, 1)

    create_cube(cube_location, cube_scale, mat_name, cube_color)
