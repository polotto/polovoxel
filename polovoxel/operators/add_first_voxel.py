"""Operator: add a single voxel at the world origin."""
import bpy

from ..usecases.factory import factory


class PolovoxelAddFirstVoxelOperator(bpy.types.Operator):
    """Add one voxel over world origin"""
    bl_idname = "object.polovoxel_add_first_voxel_operator"
    bl_label = "Add first voxel (Ctrl + Alt + N)"
    bl_options = {'REGISTER', 'UNDO'}

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
        """Pull current scene defaults into this operator, then create the voxel."""
        self.scale = context.scene.polovoxel_properties.polovoxel_scale
        self.color = context.scene.polovoxel_properties.polovoxel_color

        self.main(context)
        return {'FINISHED'}

    def main(self, context):
        """Create a single voxel cube centered at the world origin via the use case."""
        factory.build_add_first_voxel().execute(context, self.scale, self.color)
