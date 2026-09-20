"""Operator: add a new voxel above the currently selected face (edit mode)."""
import bpy

from ..usecases.factory import factory


class PolovoxelAddVoxelOperator(bpy.types.Operator):
    """Add new voxel above selected face"""
    bl_idname = "object.polovoxel_add_voxel_operator"
    bl_label = "Add voxel above selected face (Ctrl + Alt + I)"
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
        """Pull current scene defaults into this operator, then place a voxel on the selected face."""
        self.scale = context.scene.polovoxel_properties.polovoxel_scale
        self.color = context.scene.polovoxel_properties.polovoxel_color

        self.main(context)
        return {'FINISHED'}

    def main(self, context):
        """Create a voxel offset from the active edit-mesh's selected face, if any."""
        factory.build_add_voxel_on_face().execute(context, self.scale, self.color)
