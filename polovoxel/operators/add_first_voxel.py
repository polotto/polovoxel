"""Operator: add a single voxel at the world origin."""
import bpy

from ..domain.geometry import get_material_name
from ..infrastructure.blender_mesh import create_cube


class PolovoxelAddFirstVoxelOperator(bpy.types.Operator):
    """Add one voxel over world origin"""
    bl_idname = "object.polovoxel_add_first_voxel_operator"
    bl_label = "Add first voxel (Ctrl + Alt + N)"

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
        """Create a single voxel cube centered at the world origin."""
        cube_scale = (self.scale, self.scale, self.scale)
        cube_location = (0, 0, 0)
        mat_name = get_material_name(self.color)

        create_cube(context, cube_location, cube_scale, mat_name, self.color)
