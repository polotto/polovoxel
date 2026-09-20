"""Use case: add a single voxel at the world origin."""
from ..domain.geometry import get_material_name
from ..domain.mesh_repository import MeshRepository


class AddFirstVoxelUseCase:
    """Orchestrates domain math + the mesh repository to place one voxel at the origin."""

    def __init__(self, mesh_repo: MeshRepository):
        self._mesh_repo = mesh_repo

    def execute(self, context, scale, color):
        """Create a single voxel cube centered at the world origin."""
        cube_scale = (scale, scale, scale)
        cube_location = (0, 0, 0)
        mat_name = get_material_name(color)

        self._mesh_repo.create_cube(context, cube_location, cube_scale, mat_name, color)
