from mathutils import *
import bmesh
import bpy
import math
import time

bl_info = {
    "name": "Polovoxel",
    "description": "Simple plugin to create voxel art",
    "author": "Polotto",
    "version": (0, 0, 3),
    "blender": (2, 80, 0),
    "location": "Object Properties > Polovoxel",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}


# ------------------------------------------------------------------------
# common functions
# ------------------------------------------------------------------------


def get_material_name(color):
    return 'R:{0:.2f},G:{1:.2f},B:{2:.2f},A:{3:.2f}'.format(color[0], color[1], color[2], color[3])


def get_props_from_context(context):
    return (
        context.scene.polovoxel_properties.polovoxel_scale,
        context.scene.polovoxel_properties.polovoxel_color
    )


def get_props_click_from_context(context):
    return (
        context.scene.polovoxel_properties.polovoxel_scale,
        context.scene.polovoxel_properties.polovoxel_color,
        context.scene.polovoxel_properties.polovoxel_enable_with_click
    )


def get_3d_shapes_props_from_context(context):
    return (
        context.scene.polovoxel_properties.polovoxel_x_location,
        context.scene.polovoxel_properties.polovoxel_y_location,
        context.scene.polovoxel_properties.polovoxel_z_location,
        context.scene.polovoxel_properties.polovoxel_width,
        context.scene.polovoxel_properties.polovoxel_height,
        context.scene.polovoxel_properties.polovoxel_depth
    )


def setup_obj_material(cube_obj, name, color):
    # Get material
    mat = bpy.data.materials.get(name)
    if mat is None:
        # create material
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = color

    # Assign it to object
    if cube_obj.data.materials:
        # assign to 1st material slot
        cube_obj.data.materials[0] = mat
    else:
        # no slots
        cube_obj.data.materials.append(mat)

    try:
        bpy.context.space_data.shading.type = 'MATERIAL'
    except:
        pass


def create_cube(context, cube_location, cube_scale, mat_name, cube_color):
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
    except:
        pass

    bpy.ops.mesh.primitive_cube_add(
        size=2, enter_editmode=False, align='WORLD', location=cube_location, scale=cube_scale)

    try:
        bpy.ops.object.mode_set(mode='EDIT')
    except:
        pass

    cube_obj: PointerProperty(type=bpy.types.Object) = context.active_object

    setup_obj_material(cube_obj, mat_name, cube_color)


def get_first_selected_face_center_location(context):
    ob = context.edit_object

    if ob is None:
        return None, None

    me = ob.data
    bm = bmesh.from_edit_mesh(me)

    # list of selected faces
    selfaces = [f for f in bm.faces if f.select]

    if selfaces:
        face = selfaces[0]
        selected_cube_pos = (
            ob.matrix_world[0][3], ob.matrix_world[1][3], ob.matrix_world[2][3])
        point_location = face.calc_center_median() + Vector(selected_cube_pos)
        return point_location, face.normal
    else:
        return None, None


# ------------------------------------------------------------------------
# operators
# ------------------------------------------------------------------------


class PolovoxelAddVoxelOperator(bpy.types.Operator):
    """Add new voxel above selected face"""
    bl_idname = "object.polovoxel_add_voxel_operator"
    bl_label = "Add voxel above selected face (Ctrl + Alt + I)"

    def key_map(km):
        return km.keymap_items.new(PolovoxelAddVoxelOperator.bl_idname, type='I', value='PRESS', ctrl=True, alt=True)

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
        self.main(context)
        return {'FINISHED'}

    # ------------------------------------------------------------------------
    # create new cube above selected face
    # ------------------------------------------------------------------------

    def main(self, context):
        self.scale, self.color = get_props_from_context(context)

        selected_center_location, selected_normal = get_first_selected_face_center_location(context)

        if selected_center_location:
            cube_scale = (self.scale, self.scale, self.scale)

            cube_location = selected_center_location + \
                            (selected_normal * Vector(cube_scale))

            mat_name = get_material_name(self.color)
            cube_color = self.color

            create_cube(context, cube_location, cube_scale, mat_name, cube_color)


class PolovoxelAddFirstVoxelOperator(bpy.types.Operator):
    """Add one voxel over world origin"""
    bl_idname = "object.polovoxel_add_first_voxel_operator"
    bl_label = "Add first voxel (Ctrl + Alt + N)"

    def key_map(self):
        return self.keymap_items.new(PolovoxelAddFirstVoxelOperator.bl_idname, type='N', value='PRESS', ctrl=True,
                                     alt=True)

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
        self.scale, self.color = get_props_from_context(context)

        self.main(bpy.context)
        return {'FINISHED'}

    def main(self, context):
        cube_scale = (self.scale, self.scale, self.scale)

        cube_location = (0, 0, 0)

        mat_name = get_material_name(self.color)
        cube_color = self.color

        create_cube(context, cube_location, cube_scale, mat_name, cube_color)


class PolovoxelAddCuboidVoxelOperator(bpy.types.Operator):
    """Create a voxel cuboid"""
    bl_idname = "object.polovoxel_add_plane_voxel_operator"
    bl_label = "Create voxel cuboid (Ctrl + Alt + C)"

    def key_map(self):
        return self.keymap_items.new(PolovoxelAddFirstVoxelOperator.bl_idname, type='C', value='PRESS', ctrl=True,
                                     alt=True)

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
        self.x_location, self.y_location, self.z_location, self.width, self.height, self.depth = \
            get_3d_shapes_props_from_context(context)
        self.scale, self.color = get_props_from_context(context)

        self.main(bpy.context)
        return {'FINISHED'}

    def main(self, context):
        cube_scale = (self.scale, self.scale, self.scale)
        voxel_size = 2 * int(math.ceil(self.scale))
        location_x_range = range(self.x_location, self.x_location + (self.width * voxel_size), voxel_size)
        location_y_range = range(self.y_location, self.y_location + (self.depth * voxel_size), voxel_size)
        location_z_range = range(self.z_location, self.z_location + (self.height * voxel_size), voxel_size)

        print(location_x_range)

        for x in location_x_range:
            for y in location_y_range:
                for z in location_z_range:
                    cube_location = (x, y, z)

                    mat_name = get_material_name(self.color)
                    cube_color = self.color

                    create_cube(context, cube_location, cube_scale, mat_name, cube_color)


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
        # print('2 EVENT VALUE')
        # print(event.type)
        # print(event.value)

        if event.type == 'LEFTMOUSE':
            self.scale, self.color, self.enable_with_click = get_props_click_from_context(context)

            if event.value != 'CLICK' or (not self.enable_with_click) or context.active_object.mode != 'EDIT':
                return {'PASS_THROUGH'}

            # print('LEFTMOUSE')
            # print(event.mouse_prev_x, event.mouse_prev_y)
            # print(event.mouse_region_x, event.mouse_region_y)
            # print(event.mouse_x, event.mouse_y)

            selected_center_location, selected_normal = get_first_selected_face_center_location(context)

            if selected_center_location:
                cube_scale = (self.scale, self.scale, self.scale)

                cube_location = selected_center_location + \
                    (selected_normal * Vector(cube_scale))

                mat_name = get_material_name(self.color)
                cube_color = self.color

                create_cube(context, cube_location, cube_scale, mat_name, cube_color)

                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.select_all(action='DESELECT')

            else:
                return {'PASS_THROUGH'}

            # print(self.first_mouse_x)
            # context.object.location = bpy.context.scene.cursor.location
            # cursor_location = bpy.context.scene.cursor.location
            # cube_location = (cursor_location[0], cursor_location[1], cursor_location[2])
            # create_cube(context, cube_location, (1.0, 1.0, 1.0), 'blue', (1,0,0,1))

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.object:
            self.first_mouse_x = event.mouse_x
            self.first_value = context.object.location.x

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}


# ------------------------------------------------------------------------
# properties
# ------------------------------------------------------------------------

class PolovoxelPanelProperties(bpy.types.PropertyGroup):
    # bpy.types.Object.polovoxel_scale =
    #    bpy.types.Scene.polovoxel_scale = bpy.props.FloatProperty(
    #        name = 'Scale',
    #        default = 1.0,
    #        min=0.0,
    #        precision=1
    #    )
    #    
    #    bpy.types.Scene.polovoxel_color = bpy.props.FloatVectorProperty(
    #        name = "Color",
    #        subtype = "COLOR",
    #        size = 4,
    #        min = 0.0,
    #        max = 1.0,
    #        default = (0.01, 0.85, 0.22, 1.0)
    #    )
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
    )

    polovoxel_y_location: bpy.props.IntProperty(
        name='Y Location',
        default=1,
        min=0,
    )

    polovoxel_z_location: bpy.props.IntProperty(
        name='Z Location',
        default=1,
        min=0,
    )

    polovoxel_width: bpy.props.IntProperty(
        name='Width',
        default=2,
        min=1
    )

    polovoxel_height: bpy.props.IntProperty(
        name='Height',
        default=2,
        min=1
    )

    polovoxel_depth: bpy.props.IntProperty(
        name='Depth',
        default=2,
        min=1
    )

    polovoxel_enable_with_click: bpy.props.BoolProperty(
        name='Enable add with click',
        default=False
    )


# ------------------------------------------------------------------------
# panel ui
# ------------------------------------------------------------------------

class PolovoxelPanel(bpy.types.Panel):
    """Polovoxel addon object panel"""
    bl_label = "Polovoxel"
    bl_idname = "OBJECT_PT_polovoxel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"

    def draw(self, context):
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
        props.width = world.polovoxel_height
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


# ------------------------------------------------------------------------
# blender manager
# ------------------------------------------------------------------------
addon_keymaps = []
classes = (
    PolovoxelPanelProperties,
    PolovoxelAddFirstVoxelOperator,
    PolovoxelAddCuboidVoxelOperator,
    PolovoxelAddVoxelOperator,
    PolovoxelAddOnClickVoxelOperator,
    PolovoxelPanel
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.polovoxel_properties = bpy.props.PointerProperty(type=PolovoxelPanelProperties)

    props = bpy.props.CollectionProperty(type=PolovoxelPanelProperties)

    # Add the hotkey
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')

        addon_keymaps.append((km, PolovoxelAddVoxelOperator.key_map(km)))
        addon_keymaps.append((km, PolovoxelAddFirstVoxelOperator.key_map(km)))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Object.polovoxel_properties

    # Remove the hotkey
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()

    bpy.ops.object.polovoxel_add_on_click_voxel_operator('INVOKE_DEFAULT')

    # test call
    # bpy.ops.object.polovoxel_operator()
