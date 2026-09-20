"""Factory that constructs use cases with their MeshRepository dependency wired in.

Separates *construction* (deciding which concrete ``MeshRepository`` a use
case gets) from *use* (operators calling ``.execute(...)`` on an
already-built instance). This is also the one place in ``usecases/``
allowed to import ``infrastructure/`` directly — its whole job is wiring
the concrete ``BlenderMeshRepository`` into use cases that otherwise only
know about the abstract ``MeshRepository`` port from ``domain/``. The use
case classes themselves never import ``infrastructure/``, and operators
only ever import ``factory`` from here.
"""
from ..infrastructure.blender_mesh import BlenderMeshRepository
from .add_cuboid import AddCuboidUseCase
from .add_first_voxel import AddFirstVoxelUseCase
from .add_voxel_on_click import AddVoxelAtMouseUseCase
from .add_voxel_on_face import AddVoxelOnFaceUseCase


class UseCaseFactory:
    """Builds each Polovoxel use case, injecting a ``BlenderMeshRepository`` instance."""

    def __init__(self):
        self._mesh_repo = BlenderMeshRepository()

    def build_add_first_voxel(self):
        return AddFirstVoxelUseCase(self._mesh_repo)

    def build_add_voxel_on_face(self):
        return AddVoxelOnFaceUseCase(self._mesh_repo)

    def build_add_voxel_at_mouse(self):
        return AddVoxelAtMouseUseCase(self._mesh_repo)

    def build_add_cuboid(self):
        return AddCuboidUseCase(self._mesh_repo)


factory = UseCaseFactory()
