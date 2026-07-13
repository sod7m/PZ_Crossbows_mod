import bpy, mathutils
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,0))
obj = bpy.context.active_object
print("obj:", obj.name, obj.hide_render, obj.hide_viewport)

sun = bpy.data.objects.new("Sun1", bpy.data.lights.new("Sun1", type='SUN'))
sun.data.energy=3.0
bpy.context.scene.collection.objects.link(sun)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam_pos = mathutils.Vector((3,-3,2))
cam.location = cam_pos
direction = mathutils.Vector((0,0,0)) - cam_pos
cam.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x=400
scene.render.resolution_y=400
scene.render.filepath = "E:/PZCrossbows/work/InWork/sanity_cube.png"
bpy.ops.render.render(write_still=True)
print("done")
