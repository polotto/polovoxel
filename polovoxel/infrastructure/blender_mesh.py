"""bpy/bmesh-dependent adapters for the Polovoxel add-on.

This is the only layer allowed to call ``bpy.ops``/``bpy.data``/``bmesh`` to
create objects, assign materials, or read mesh data. Domain math (material
naming, voxel placement) lives in :mod:`polovoxel.domain.geometry` and is
only ever consumed here, never duplicated.
"""
import bmesh
import bpy
from bpy_extras import view3d_utils
from mathutils import Vector

from ..domain.geometry import compute_face_voxel_location, get_material_name


def setup_obj_material(cube_obj, name, color):
    """Get-or-create a material named ``name``/colored ``color`` and assign it to ``cube_obj``.

    Sets both the legacy ``diffuse_color`` (used by Solid shading's default
    "Material" color mode) and the Principled BSDF node's Base Color (used
    by Material Preview/Rendered shading, since ``bpy.data.materials.new()``
    creates a node-based material by default in Blender 2.8+) so the color
    is correct in either shading mode. Does **not** change the user's
    current viewport shading mode — Solid stays Solid.
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

    Used by the "add voxel above selected face" operator (button/Ctrl+Alt+I).
    Returns ``True`` if a voxel was created, ``False`` if there was no
    selected face to build from.
    """
    selected_center_location, selected_normal = get_first_selected_face_center_location(context)

    if selected_center_location is None:
        return False

    cube_scale = (scale, scale, scale)
    cube_location = compute_face_voxel_location(selected_center_location, selected_normal, scale)
    mat_name = get_material_name(color)

    create_cube(context, cube_location, cube_scale, mat_name, color)
    return True


def _find_view3d_region_under_mouse(context, event):
    """Locate the 3D viewport WINDOW region under the mouse cursor.

    ``context.region``/``context.region_data`` can be ``None`` for a modal
    operator that was started outside a normal UI event — e.g. via
    ``bpy.app.timers`` (as click-to-add is, to work around a separate
    context restriction on starting modals from property update callbacks).
    Blender doesn't fill in per-event area/region context for handlers
    started that way, so this resolves it manually: scan the window's areas
    for a ``VIEW_3D`` one whose bounds contain the event's absolute
    window-space mouse position, then its ``WINDOW``-type region the same
    way. Returns ``(region, region_3d)`` or ``(None, None)``.
    """
    window = context.window
    if window is None or window.screen is None:
        return None, None

    for area in window.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        if not (area.x <= event.mouse_x < area.x + area.width
                and area.y <= event.mouse_y < area.y + area.height):
            continue

        for region in area.regions:
            if region.type != 'WINDOW':
                continue
            if (region.x <= event.mouse_x < region.x + region.width
                    and region.y <= event.mouse_y < region.y + region.height):
                return region, area.spaces.active.region_3d

    return None, None


def get_face_under_mouse(context, event):
    """Return ``(world-space face center, world-space face normal)`` for
    whatever face is under the mouse cursor in a 3D viewport.

    Casts a ray from the viewport camera through the cursor position using
    the region's view matrix, then ``Scene.ray_cast`` against the evaluated
    scene. Uses the *hit face's* actual center (via the returned polygon
    index), not the raw ray-hit point — the hit point can land anywhere on
    the face depending on exactly where the cursor was, which would offset
    each new voxel by a few pixels' worth of surface position instead of
    keeping it flush and grid-aligned against the clicked face. Returns
    ``(None, None)`` if the event isn't over a 3D viewport region, the ray
    doesn't hit a mesh, or the hit has no usable face index.
    """
    region, rv3d = _find_view3d_region_under_mouse(context, event)

    if region is None or rv3d is None:
        return None, None

    coord = (event.mouse_x - region.x, event.mouse_y - region.y)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    ray_direction = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)

    depsgraph = context.evaluated_depsgraph_get()
    success, _location, normal, index, hit_obj, matrix = context.scene.ray_cast(
        depsgraph, ray_origin, ray_direction)

    if not success or hit_obj is None or hit_obj.type != 'MESH' or index < 0:
        return None, None

    face_center_world = matrix @ hit_obj.data.polygons[index].center

    return face_center_world, normal


def add_voxel_at_mouse(context, event, scale, color):
    """Create a new voxel offset from whatever face is under the mouse cursor.

    Used by the click-to-add modal operator: raycasts from the mouse into
    the 3D viewport, so a single click on any face (in any mode) adds a
    voxel there directly — unlike :func:`add_voxel_on_selected_face`, this
    needs no prior face selection. Returns ``True`` if a voxel was created,
    ``False`` if the ray didn't hit anything.
    """
    location, normal = get_face_under_mouse(context, event)

    if location is None:
        return False

    cube_scale = (scale, scale, scale)
    cube_location = compute_face_voxel_location(location, normal, scale)
    mat_name = get_material_name(color)

    create_cube(context, cube_location, cube_scale, mat_name, color)
    return True
