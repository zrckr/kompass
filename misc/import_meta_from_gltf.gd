@tool
extends EditorScript

# e.g. 'res://assets/meshes/industrial.gltf'
static var gltf := ''

# e.g. 'res://assets/meshes/industial.tscn'
static var imported := ''


func _run():
	var file := FileAccess.open(gltf, FileAccess.READ)
	var json = JSON.parse_string(file.get_as_text())
	var meta = json.get('asset', {}).get('extras', {})
	file.close()
	
	var resource_scene := load(imported) as PackedScene
	var resource_flags := PackedScene.GEN_EDIT_STATE_INSTANCE | PackedScene.GEN_EDIT_STATE_MAIN_INHERITED
	var scene := resource_scene.instantiate(resource_flags) as Node
	
	for child in scene.get_children():
		var trile_name := child.name
		var trile_meta := meta[trile_name] as Dictionary
		print(trile_name)
		
		var collision_size := Vector3(
			trile_meta['collisionSize'][0],
			trile_meta['collisionSize'][1],
			trile_meta['collisionSize'][2],
		)
		
		var static_body := StaticBody3D.new()
		var collision_shape := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		
		shape.size = collision_size
		collision_shape.shape = shape
		
		static_body.add_child(collision_shape, true)
		child.add_child(static_body, true)
		
		static_body.set_owner(scene)
		collision_shape.set_owner(scene)
	
	var packed_scene = PackedScene.new()
	packed_scene.pack(scene)
	ResourceSaver.save(packed_scene, 'res://out.tscn')
