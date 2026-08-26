"""Scene-level state for the Polovoxel add-on.

Holds the current scale/color/location/size/click-toggle values that the
panel displays and the operators read defaults from. No business logic
lives here.
"""
import bpy


class PolovoxelPanelProperties(bpy.types.PropertyGroup):
    """Add-on settings stored on ``bpy.types.Scene.polovoxel_properties``."""

    polovoxel_scale: bpy.props.FloatProperty(
        name='Scale',
        default=1.0,
        min=0.0,
        precision=2,
        step=1
    )

    polovoxel_color: bpy.props.FloatVectorProperty(
        name="Color",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.01, 0.85, 0.22, 1.0)
    )

    polovoxel_x_location: bpy.props.IntProperty(
        name='X Location',
        default=1,
        min=0,
        soft_max=50,
    )

    polovoxel_y_location: bpy.props.IntProperty(
        name='Y Location',
        default=1,
        min=0,
        soft_max=50,
    )

    polovoxel_z_location: bpy.props.IntProperty(
        name='Z Location',
        default=1,
        min=0,
        soft_max=50,
    )

    polovoxel_width: bpy.props.IntProperty(
        name='Width',
        default=2,
        min=1,
        soft_max=32,
    )

    polovoxel_height: bpy.props.IntProperty(
        name='Height',
        default=2,
        min=1,
        soft_max=32,
    )

    polovoxel_depth: bpy.props.IntProperty(
        name='Depth',
        default=2,
        min=1,
        soft_max=32,
    )

    polovoxel_enable_with_click: bpy.props.BoolProperty(
        name='Enable add with click',
        default=False
    )
