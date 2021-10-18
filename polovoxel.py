from mathutils import *
import bmesh
import bpy

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
    
    cube_obj = context.active_object
    
    setup_obj_material(cube_obj, mat_name, cube_color)


# ------------------------------------------------------------------------
# operators
# ------------------------------------------------------------------------


class PolovoxelAddVoxelOperator(bpy.types.Operator):
    """Add new voxel over selected face"""
    bl_idname = "object.polovoxel_add_voxel_operator"
    bl_label = "Add voxel over selected face"

    scale: bpy.props.FloatProperty(
        name = 'Scale',
        default = 1.0,
        min = 0.0,
        precision=1
    )
    
    color: bpy.props.FloatVectorProperty(
        name = "Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (0.01, 0.85, 0.22, 1.0)
    )

    def execute(self, context):
        self.main(context)
        return {'FINISHED'}
    
    # ------------------------------------------------------------------------
    # create new cube above selected face
    # ------------------------------------------------------------------------

    def main(self, context):
        self.color = context.scene.polovoxel_properties.polovoxel_color
        self.scale = context.scene.polovoxel_properties.polovoxel_scale
        
        selected_center_location, selected_normal = self.get_first_selected_face_center_location(context)

        if selected_center_location:
            cube_scale = (self.scale, self.scale, self.scale)
            
            cube_location = selected_center_location + \
                (selected_normal * Vector(cube_scale))

            mat_name = 'R:{0:.2f},G:{1:.2f},B:{2:.2f},A:{3:.2f}'.format(self.color[0], self.color[1], self.color[2], self.color[3])
            cube_color = self.color

            create_cube(context, cube_location, cube_scale, mat_name, cube_color)
            

    def get_first_selected_face_center_location(self, context):
        ob = context.edit_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)

        # list of selected faces
        selfaces = [f for f in bm.faces if f.select]

        if selfaces:
            face = selfaces[0]
            selected_cube_pos = (
                ob.matrix_world[0][3], ob.matrix_world[1][3], ob.matrix_world[2][3])
            point_location = face.calc_center_median() + Vector(selected_cube_pos)
            return (point_location, face.normal)
        else:
            return (None, None)


class PolovoxelAddFirstVoxelOperator(bpy.types.Operator):
    """Add one voxel over world origin"""
    bl_idname = "object.polovoxel_add_first_voxel_operator"
    bl_label = "Add first voxel"

    scale: bpy.props.FloatProperty(
        name = 'Scale',
        default = 1.0,
        min = 0.0,
        precision=1
    )
    
    color: bpy.props.FloatVectorProperty(
        name = "Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (0.01, 0.85, 0.22, 1.0)
    )

    def execute(self, context):
        self.color = context.scene.polovoxel_properties.polovoxel_color
        self.scale = context.scene.polovoxel_properties.polovoxel_scale
        
        self.main(bpy.context)
        return {'FINISHED'}
    
    def main(self, context):
        cube_scale = (self.scale, self.scale, self.scale)            
        
        cube_location = (0,0,0)
        
        mat_name = 'R:{0:.2f},G:{1:.2f},B:{2:.2f},A:{3:.2f}'.format(self.color[0], self.color[1], self.color[2], self.color[3])
        cube_color = self.color

        create_cube(context, cube_location, cube_scale, mat_name, cube_color)


# ------------------------------------------------------------------------
# properties
# ------------------------------------------------------------------------

class PolovoxelPanelProperties(bpy.types.PropertyGroup):
    #bpy.types.Object.polovoxel_scale = 
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
        name = 'Scale',
        default = 1.0,
        min=0.0,
        precision=1
    )
    
    polovoxel_color: bpy.props.FloatVectorProperty(
        name = "Color",
        subtype = "COLOR",
        size = 4,
        min = 0.0,
        max = 1.0,
        default = (0.01, 0.85, 0.22, 1.0)
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
        row.label(text="General options")
        
        # row
        row = layout.row()
        row.prop(world, "polovoxel_scale")
        
        # row
        row = layout.row()
        row.prop(world, "polovoxel_color")
        
        # row
        row = layout.row()
        props = row.operator(PolovoxelAddFirstVoxelOperator.bl_idname)
        props.scale = world.polovoxel_scale
        props.color = world.polovoxel_color
        
        # row
        row = layout.row()
        props = row.operator(PolovoxelAddVoxelOperator.bl_idname)
        props.scale = world.polovoxel_scale
        props.color = world.polovoxel_color
        

# ------------------------------------------------------------------------
# blender manager
# ------------------------------------------------------------------------
addon_keymaps = []
classes = (
    PolovoxelPanelProperties,
    PolovoxelAddFirstVoxelOperator,
    PolovoxelAddVoxelOperator,
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
        
        kmi = km.keymap_items.new(PolovoxelAddVoxelOperator.bl_idname, type='I', value='PRESS', ctrl=True, alt=True)
        addon_keymaps.append((km, kmi))
        
        kmi = km.keymap_items.new(PolovoxelAddFirstVoxelOperator.bl_idname, type='N', value='PRESS', ctrl=True, alt=True)
        #print(dir(kmi.properties))
        addon_keymaps.append((km, kmi))


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

    # test call
    # bpy.ops.object.polovoxel_operator()