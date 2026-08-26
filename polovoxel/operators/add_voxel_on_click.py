"""Operator: modal handler that adds a voxel on the selected face when the user left-clicks."""
import bpy

from ..infrastructure.blender_mesh import add_voxel_on_selected_face


class PolovoxelAddOnClickVoxelOperator(bpy.types.Operator):
    """Add one voxel over click"""
    bl_idname = "object.polovoxel_add_on_click_voxel_operator"
    bl_label = "Add voxel over clicked face"

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

    enable_with_click: bpy.props.BoolProperty(
        name='Enable add with click',
        default=False
    )

    def modal(self, context, event):
        """Handle viewport events: left-click adds a voxel, right-click/Esc cancels."""
        if event.type == 'LEFTMOUSE':
            props = context.scene.polovoxel_properties
            self.scale = props.polovoxel_scale
            self.color = props.polovoxel_color
            self.enable_with_click = props.polovoxel_enable_with_click

            active = context.active_object

            if (event.value != 'CLICK' or not self.enable_with_click
                    or active is None or active.mode != 'EDIT'):
                return {'PASS_THROUGH'}

            created = add_voxel_on_selected_face(context, self.scale, self.color)

            if not created:
                return {'PASS_THROUGH'}

            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.select_all(action='DESELECT')

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        """Start the modal click-to-add loop if there is an active object."""
        if context.object is None:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
