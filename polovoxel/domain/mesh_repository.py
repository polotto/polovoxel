"""Port (interface) for whatever creates/reads mesh objects in the scene.

Defined in `domain/` — pure Python (``abc`` only), zero `bpy`/`bmesh`
imports — so `usecases/` can depend on this abstraction instead of a
concrete infrastructure implementation. This is the Dependency Inversion
half of the layering rule: `infrastructure/blender_mesh.py` implements it
as `BlenderMeshRepository`, but no use case imports that module — only
`usecases/factory.py` does, to construct the concrete instance a use case
gets injected with.
"""
from abc import ABC, abstractmethod


class MeshRepository(ABC):
    """Abstract gateway to mesh creation/reading in the scene."""

    @abstractmethod
    def create_cube(self, context, cube_location, cube_scale, mat_name, cube_color):
        """Create a new cube at ``cube_location``/``cube_scale`` and material it."""

    @abstractmethod
    def get_first_selected_face_center_location(self, context):
        """Return ``(world-space center, normal)`` of the first selected face.

        Returns ``(None, None)`` if there is no edit-mesh object or no
        selected face.
        """

    @abstractmethod
    def get_face_under_mouse(self, context, event):
        """Return ``(world-space face center, world-space face normal)`` under the mouse.

        Returns ``(None, None)`` if the event isn't over a 3D viewport
        region or the ray doesn't hit a mesh face.
        """
