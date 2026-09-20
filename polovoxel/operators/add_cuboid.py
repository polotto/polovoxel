"""Operator: stamp a solid cuboid of voxels."""
import bpy

from ..usecases.factory import factory


class PolovoxelAddCuboidVoxelOperator(bpy.types.Operator):
    """Create a voxel cuboid"""
    bl_idname = "object.polovoxel_add_plane_voxel_operator"
    bl_label = "Create voxel cuboid (Ctrl + Alt + C)"
    bl_options = {'REGISTER', 'UNDO'}

    x_location: bpy.props.IntProperty(
        name='X Location',
        default=1,
        min=0,
    )

    y_location: bpy.props.IntProperty(
        name='Y Location',
        default=1,
        min=0,
    )

    z_location: bpy.props.IntProperty(
        name='Z Location',
        default=1,
        min=0,
    )

    width: bpy.props.IntProperty(
        name='Width',
        default=2,
        min=1
    )

    height: bpy.props.IntProperty(
        name='Height',
        default=2,
        min=1
    )

    depth: bpy.props.IntProperty(
        name='Depth',
        default=2,
        min=1
    )

    scale: bpy.props.FloatProperty(
        name='Scale',
        default=1.0,
        min=0.0,
        precision=1
    )

    color: bpy.props.FloatVectorProperty(
        name="Color",
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        default=(0.01, 0.85, 0.22, 1.0)
    )

    def execute(self, context):
        """Pull current scene defaults into this operator, then build the cuboid."""
        props = context.scene.polovoxel_properties
        self.x_location = props.polovoxel_x_location
        self.y_location = props.polovoxel_y_location
        self.z_location = props.polovoxel_z_location
        self.width = props.polovoxel_width
        self.height = props.polovoxel_height
        self.depth = props.polovoxel_depth
        self.scale = props.polovoxel_scale
        self.color = props.polovoxel_color

        self.main(context)
        return {'FINISHED'}

    def main(self, context):
        """Create one voxel cube per grid location in the configured cuboid."""
        if self.scale <= 0:
            self.report({'WARNING'}, "Scale must be greater than 0 to build a cuboid")
            return

        factory.build_add_cuboid().execute(
            context, self.x_location, self.y_location, self.z_location,
            self.width, self.height, self.depth, self.scale, self.color
        )
