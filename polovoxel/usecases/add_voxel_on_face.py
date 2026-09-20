"""Use case: add a voxel offset from the active edit-mesh's selected face."""
from ..domain.geometry import compute_face_voxel_location, get_material_name
from ..domain.mesh_repository import MeshRepository


class AddVoxelOnFaceUseCase:
    """Orchestrates domain math + the mesh repository to place a voxel against a selected face."""

    def __init__(self, mesh_repo: MeshRepository):
        self._mesh_repo = mesh_repo

    def execute(self, context, scale, color):
        """Create a voxel offset from the active edit-mesh's selected face, if any.

        Returns ``True`` if a voxel was created, ``False`` if there was no
        selected face to build from.
        """
        selected_center_location, selected_normal = self._mesh_repo.get_first_selected_face_center_location(context)

        if selected_center_location is None:
            return False

        cube_scale = (scale, scale, scale)
        cube_location = compute_face_voxel_location(selected_center_location, selected_normal, scale)
        mat_name = get_material_name(color)

        self._mesh_repo.create_cube(context, cube_location, cube_scale, mat_name, color)
        return True
