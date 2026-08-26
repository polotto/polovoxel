"""Polovoxel Blender add-on: composition root.

Holds ``bl_info`` and wires the domain/infrastructure/operators/ui layers
together via :func:`register`/:func:`unregister`. No business logic lives
here — everything is imported from the other layers and just registered
with Blender.
"""
import bpy

from . import keymaps
from .operators.add_cuboid import PolovoxelAddCuboidVoxelOperator
from .operators.add_first_voxel import PolovoxelAddFirstVoxelOperator
from .operators.add_voxel_on_click import PolovoxelAddOnClickVoxelOperator
from .operators.add_voxel_on_face import PolovoxelAddVoxelOperator
from .ui.panel import PolovoxelPanel
from .ui.properties import PolovoxelPanelProperties

bl_info = {
    "name": "Polovoxel",
    "description": "Simple plugin to create voxel art",
    "author": "Polotto",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "Properties > World > Polovoxel",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}

classes = (
    PolovoxelPanelProperties,
    PolovoxelAddFirstVoxelOperator,
    PolovoxelAddCuboidVoxelOperator,
    PolovoxelAddVoxelOperator,
    PolovoxelAddOnClickVoxelOperator,
    PolovoxelPanel,
)


def register():
    """Register all add-on classes, attach Scene state, and wire up keymaps."""
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.polovoxel_properties = bpy.props.PointerProperty(type=PolovoxelPanelProperties)

    keymaps.register()


def unregister():
    """Undo everything :func:`register` did, in reverse order."""
    keymaps.unregister()

    if hasattr(bpy.types.Scene, "polovoxel_properties"):
        del bpy.types.Scene.polovoxel_properties

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
