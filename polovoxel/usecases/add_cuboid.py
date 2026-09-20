"""Use case: stamp a solid cuboid of voxels."""
from ..domain.geometry import compute_cuboid_voxel_locations, get_material_name
from ..domain.mesh_repository import MeshRepository


class AddCuboidUseCase:
    """Orchestrates domain math + the mesh repository to stamp a solid cuboid of voxels."""

    def __init__(self, mesh_repo: MeshRepository):
        self._mesh_repo = mesh_repo

    def execute(self, context, x_location, y_location, z_location, width, height, depth, scale, color):
        """Create one voxel cube per grid location in the configured cuboid."""
        cube_scale = (scale, scale, scale)
        mat_name = get_material_name(color)

        locations = compute_cuboid_voxel_locations(
            x_location, y_location, z_location, width, height, depth, scale
        )

        for cube_location in locations:
            self._mesh_repo.create_cube(context, cube_location, cube_scale, mat_name, color)
