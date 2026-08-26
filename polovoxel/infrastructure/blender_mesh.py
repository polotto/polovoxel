"""bpy/bmesh-dependent adapters for the Polovoxel add-on.

This is the only layer allowed to call ``bpy.ops``/``bpy.data``/``bmesh`` to
create objects, assign materials, or read mesh data. Domain math (material
naming, voxel placement) lives in :mod:`polovoxel.domain.geometry` and is
only ever consumed here, never duplicated.
"""
import bmesh
import bpy
from mathutils import Vector

from ..domain.geometry import compute_face_voxel_location, get_material_name


def setup_obj_material(cube_obj, name, color):
    """Get-or-create a material named ``name``/colored ``color`` and assign it to ``cube_obj``.

    Sets both the legacy ``diffuse_color`` (used by Solid shading's
    "Material" color mode) and the Principled BSDF node's Base Color (used
    by Material Preview/Rendered shading, since ``bpy.data.materials.new()``
    creates a node-based material by default in Blender 2.8+ — without this,
    voxels render as the node graph's default gray once the viewport is
    switched to Material Preview below).
    """
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = color

        if mat.use_nodes:
            bsdf = mat.node_tree.nodes.get('Principled BSDF')
            if bsdf is not None:
                bsdf.inputs['Base Color'].default_value = color

    if cube_obj.data.materials:
        # assign to 1st material slot
        cube_obj.data.materials[0] = mat
    else:
        # no slots
        cube_obj.data.materials.append(mat)

    try:
        bpy.context.space_data.shading.type = 'MATERIAL'
    except AttributeError:
        # No 3D viewport space_data available in the current context
        # (e.g. called from a different editor area) — nothing to switch.
        pass


def create_cube(context, cube_location, cube_scale, mat_name, cube_color):
    """Create a new 2-unit cube at ``cube_location``/``cube_scale`` and material it."""
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except RuntimeError:
        pass

    bpy.ops.mesh.primitive_cube_add(
        size=2, enter_editmode=False, align='WORLD', location=cube_location, scale=cube_scale)

    try:
        bpy.ops.object.mode_set(mode='EDIT')
    except RuntimeError:
        pass

    cube_obj = context.active_object

    setup_obj_material(cube_obj, mat_name, cube_color)


def get_first_selected_face_center_location(context):
    """Return ``(world-space center, normal)`` of the first selected face.

    Reads the currently active edit-mesh's ``bmesh`` state. Returns
    ``(None, None)`` if there is no edit-mesh object or no selected face.
    """
    ob = context.edit_object

    if ob is None:
        return None, None

    me = ob.data
    bm = bmesh.from_edit_mesh(me)

    selected_faces = [f for f in bm.faces if f.select]

    if not selected_faces:
        return None, None

    face = selected_faces[0]
    object_location = (ob.matrix_world[0][3], ob.matrix_world[1][3], ob.matrix_world[2][3])
    point_location = face.calc_center_median() + Vector(object_location)
    return point_location, face.normal


def add_voxel_on_selected_face(context, scale, color):
    """Create a new voxel offset from the active edit-mesh's selected face, if any.

    Shared by the "add voxel above selected face" operator and the
    click-to-add modal operator so this placement logic only lives in one
    place. Returns ``True`` if a voxel was created, ``False`` if there was
    no selected face to build from.
    """
    selected_center_location, selected_normal = get_first_selected_face_center_location(context)

    if selected_center_location is None:
        return False

    cube_scale = (scale, scale, scale)
    cube_location = compute_face_voxel_location(selected_center_location, selected_normal, scale)
    mat_name = get_material_name(color)

    create_cube(context, cube_location, cube_scale, mat_name, color)
    return True
