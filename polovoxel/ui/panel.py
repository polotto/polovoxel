"""Draws the Polovoxel panel and wires its widgets to operators.

No business logic lives here: this module only reads scene properties and
invokes operators by ``bl_idname``.
"""
import bpy

from ..operators.add_cuboid import PolovoxelAddCuboidVoxelOperator
from ..operators.add_first_voxel import PolovoxelAddFirstVoxelOperator
from ..operators.add_voxel_on_face import PolovoxelAddVoxelOperator


class PolovoxelPanel(bpy.types.Panel):
    """Polovoxel addon panel, shown under the World properties tab."""
    bl_label = "Polovoxel"
    bl_idname = "OBJECT_PT_polovoxel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"

    def draw(self, context):
        """Draw usage instructions plus the common/voxel/cuboid/edit-mode controls."""
        layout = self.layout

        world = context.scene.polovoxel_properties

        # row
        row = layout.row()
        row.label(text="How use:")
        row = layout.row()
        row.label(text=" * choose a scale")
        row = layout.row()
        row.label(text=" * choose a color")
        row = layout.row()
        row.label(text=" * click: Add first voxel")
        row = layout.row()
        row.label(text=" * choose desired face to draw")
        row = layout.row()
        row.label(text=" * click: Add voxel above selected face")

        # row
        row = layout.row()
        row.label(text="Common options:")

        # row
        row = layout.row()
        row.prop(world, "polovoxel_scale")

        # row
        row = layout.row()
        row.prop(world, "polovoxel_color")

        # row
        row = layout.row()
        row.label(text="Voxel:")

        # row
        row = layout.row()
        props = row.operator(PolovoxelAddFirstVoxelOperator.bl_idname)
        props.scale = world.polovoxel_scale
        props.color = world.polovoxel_color

        # row
        row = layout.row()
        row.label(text="3D shapes:")

        # row
        row = layout.row()
        row.prop(world, "polovoxel_x_location")

        # row
        row = layout.row()
        row.prop(world, "polovoxel_y_location")

        # row
        row = layout.row()
        row.prop(world, "polovoxel_z_location")

        # row
        row = layout.row()
        row.prop(world, "polovoxel_width")

        # row
        row = layout.row()
        row.prop(world, "polovoxel_height")

        # row
        row = layout.row()
        row.prop(world, "polovoxel_depth")

        # row
        row = layout.row()
        props = row.operator(PolovoxelAddCuboidVoxelOperator.bl_idname)
        props.scale = world.polovoxel_scale
        props.color = world.polovoxel_color
        props.x_location = world.polovoxel_x_location
        props.y_location = world.polovoxel_y_location
        props.z_location = world.polovoxel_z_location
        props.width = world.polovoxel_width
        props.height = world.polovoxel_height
        props.depth = world.polovoxel_depth

        # row
        row = layout.row()
        row.label(text="Edit mode:")

        # row
        row = layout.row()
        props = row.operator(PolovoxelAddVoxelOperator.bl_idname)
        props.scale = world.polovoxel_scale
        props.color = world.polovoxel_color

        # row
        row = layout.row()
        row.prop(world, "polovoxel_enable_with_click")
