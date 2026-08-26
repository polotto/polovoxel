"""Centralizes keyboard-shortcut registration for the add-on's operators.

Pulling this out of the individual operator classes fixes three bugs that
existed when each operator defined its own ``key_map`` method: a mismatched
``self``/``km`` target on two of them, a copy-pasted ``bl_idname`` on the
cuboid operator, and the cuboid shortcut never actually being wired up in
``register()``. There is now exactly one place to look for "what does
Ctrl+Alt+<key> do".
"""
import bpy

from .operators.add_cuboid import PolovoxelAddCuboidVoxelOperator
from .operators.add_first_voxel import PolovoxelAddFirstVoxelOperator
from .operators.add_voxel_on_face import PolovoxelAddVoxelOperator

addon_keymaps = []


def register():
    """Register the 3D-viewport keyboard shortcuts (Ctrl+Alt+I/N/C)."""
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

    addon_keymaps.append((km, km.keymap_items.new(
        PolovoxelAddVoxelOperator.bl_idname, type='I', value='PRESS', ctrl=True, alt=True)))
    addon_keymaps.append((km, km.keymap_items.new(
        PolovoxelAddFirstVoxelOperator.bl_idname, type='N', value='PRESS', ctrl=True, alt=True)))
    addon_keymaps.append((km, km.keymap_items.new(
        PolovoxelAddCuboidVoxelOperator.bl_idname, type='C', value='PRESS', ctrl=True, alt=True)))


def unregister():
    """Remove every keyboard shortcut added by :func:`register`."""
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
