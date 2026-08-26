"""Pure grid/coordinate and material-naming math for the Polovoxel add-on.

Nothing in this module imports ``bpy`` or ``bmesh`` and nothing here has
side effects: nothing is created, drawn, or written to a scene. Only
``mathutils.Vector`` is used for vector arithmetic, so this module can be
imported and unit-tested outside Blender.
"""
from mathutils import Vector


def get_material_name(color):
    """Return a deterministic material name encoding an RGBA color.

    Same color always maps to the same name, so materials are reused
    instead of duplicated when the same color is picked again.
    """
    return 'R:{0:.2f},G:{1:.2f},B:{2:.2f},A:{3:.2f}'.format(color[0], color[1], color[2], color[3])


def compute_face_voxel_location(face_center, face_normal, scale):
    """Compute the location for a new voxel placed against a selected face.

    ``face_center`` and ``face_normal`` are ``mathutils.Vector`` instances
    (as produced by ``bmesh``) describing the already-selected face in world
    space. The new voxel is offset from that face by ``face_normal`` scaled
    by ``(scale, scale, scale)``.
    """
    cube_scale = Vector((scale, scale, scale))
    return face_center + (face_normal * cube_scale)


def compute_cuboid_voxel_locations(x_location, y_location, z_location, width, height, depth, scale):
    """Compute the list of voxel-center locations for a solid cuboid stamp.

    ``width``/``height``/``depth`` are voxel counts along X/Z/Y respectively,
    starting at ``(x_location, y_location, z_location)``. Grid spacing is
    derived from the true cube size (``2 * scale``, since each cube is built
    with ``size=2`` and then scaled), so it stays exact for any positive
    float scale instead of being rounded up to an integer.

    Raises ``ValueError`` if ``scale`` is not greater than zero, since a
    non-positive scale cannot produce a valid, non-zero grid spacing.
    """
    if scale <= 0:
        raise ValueError("scale must be greater than 0 to build a cuboid")

    voxel_size = 2 * scale

    locations = []
    for ix in range(width):
        x = x_location + ix * voxel_size
        for iy in range(depth):
            y = y_location + iy * voxel_size
            for iz in range(height):
                z = z_location + iz * voxel_size
                locations.append((x, y, z))
    return locations
