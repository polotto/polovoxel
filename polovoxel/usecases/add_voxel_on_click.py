"""Use case: add a voxel offset from whatever face is under the mouse cursor."""
from ..domain.geometry import compute_face_voxel_location, get_material_name
from ..domain.mesh_repository import MeshRepository


class AddVoxelAtMouseUseCase:
    """Orchestrates domain math + the mesh repository to place a voxel under the mouse cursor."""

    def __init__(self, mesh_repo: MeshRepository):
        self._mesh_repo = mesh_repo

    def execute(self, context, event, scale, color):
        """Create a new voxel offset from whatever face is under the mouse cursor.

        Used by the click-to-add modal operator: raycasts from the mouse into
        the 3D viewport, so a single click on any face (in any mode) adds a
        voxel there directly. Returns ``True`` if a voxel was created,
        ``False`` if the ray didn't hit anything.
        """
        location, normal = self._mesh_repo.get_face_under_mouse(context, event)

        if location is None:
            return False

        cube_scale = (scale, scale, scale)
        cube_location = compute_face_voxel_location(location, normal, scale)
        mat_name = get_material_name(color)

        self._mesh_repo.create_cube(context, cube_location, cube_scale, mat_name, color)
        return True
