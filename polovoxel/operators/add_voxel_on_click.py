"""Operator: modal handler that adds a voxel on whatever face the user clicks."""
import bpy

from ..usecases.factory import factory

_running = False


class PolovoxelAddOnClickVoxelOperator(bpy.types.Operator):
    """Add one voxel over click"""
    bl_idname = "object.polovoxel_add_on_click_voxel_operator"
    bl_label = "Add voxel over clicked face"
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

    enable_with_click: bpy.props.BoolProperty(
        name='Enable add with click',
        default=False
    )

    def modal(self, context, event):
        """Handle viewport events: left-click raycasts and adds a voxel on whatever
        face it hits, right-click/Esc cancels.

        Works in any object/edit mode and needs no prior face selection —
        the ray is cast straight from the mouse cursor into the 3D
        viewport (see :class:`polovoxel.usecases.add_voxel_on_click.AddVoxelAtMouseUseCase`).
        """
        if event.type != 'LEFTMOUSE':
            if event.type in {'RIGHTMOUSE', 'ESC'}:
                self._stop()
                return {'CANCELLED'}
            return {'PASS_THROUGH'}

        props = context.scene.polovoxel_properties
        self.scale = props.polovoxel_scale
        self.color = props.polovoxel_color
        self.enable_with_click = props.polovoxel_enable_with_click

        if not self.enable_with_click or event.value != 'PRESS':
            return {'PASS_THROUGH'}

        try:
            created = factory.build_add_voxel_at_mouse().execute(context, event, self.scale, self.color)
        except Exception as exc:
            # Never let a single bad click silently kill the whole listener
            # (an uncaught exception here would remove this modal handler).
            self.report({'ERROR'}, f"Polovoxel: click-to-add failed: {exc}")
            return {'PASS_THROUGH'}

        if not created:
            # Nothing under the cursor — let the click behave normally
            # (viewport navigation/selection), no voxel to place there.
            return {'PASS_THROUGH'}

        # Consume the click: a voxel was just placed and create_cube() put
        # the new object into Edit Mode, so don't also let Blender's own
        # click-select run against the (different) screen position.
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        """Start the modal click-to-add loop, guarding against a second handler stacking on top."""
        global _running

        if _running:
            return {'CANCELLED'}

        _running = True
        context.window_manager.modal_handler_add(self)
        self.report({'INFO'}, "Polovoxel: click-to-add is on — click any face in the 3D viewport")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        """Called by Blender if the modal loop is torn down externally (e.g. window closed)."""
        self._stop()

    def _stop(self):
        global _running
        _running = False


def start_if_not_running():
    """Schedule the click-to-add modal loop to start, unless one is already running.

    Called from the "Enable add with click" checkbox's ``update`` callback
    (see :mod:`polovoxel.ui.properties`) — the checkbox only stores a scene
    property, it does not by itself start the modal handler that listens for
    clicks, so this is what actually makes the toggle do something.

    The operator call is deferred one tick via ``bpy.app.timers`` rather than
    invoked directly: calling an operator that does
    ``modal_handler_add`` *from inside a property update callback* runs in a
    restricted context in Blender and can silently fail to attach the
    handler. A timer callback runs on the next event-loop tick with a normal,
    unrestricted context, which is the documented-safe way to do this.
    """
    if _running:
        return

    def _invoke():
        bpy.ops.object.polovoxel_add_on_click_voxel_operator('INVOKE_DEFAULT')
        return None  # don't repeat

    bpy.app.timers.register(_invoke, first_interval=0.0)
