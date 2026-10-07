extends SceneTree
## 实际实例化两个新沙盒，并验证角色响应移动输入；不修改正式游戏。
func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var tiles := load("res://scenes/ember/autotile_sandbox_v005.tscn").instantiate() as Node2D
	root.add_child(tiles)
	await process_frame
	assert(tiles.get_node("Wall").tile_set.tile_size == Vector2i(128,128))
	assert(tiles.get_node("Wall").scale == Vector2(0.25,0.25))
	tiles.queue_free()
	await process_frame
	var character := load("res://scenes/ember/rivet_character_preview.tscn").instantiate() as Node2D
	root.add_child(character)
	await process_frame
	var actor := character.get_node("PlayableRivet") as Node2D
	var start := actor.position
	Input.action_press("move_right")
	await create_timer(0.1).timeout
	Input.action_release("move_right")
	assert(actor.position.x > start.x)
	assert(actor.get_node("AnimatedSprite2D").animation == "walk_right")
	await process_frame
	await process_frame
	assert(actor.get_node("AnimatedSprite2D").animation == "idle_right")
	print("PASS: v005 preview loads; 128px texture/32-unit grid; Rivet moves and returns to idle")
	character.queue_free()
	quit()
