extends SceneTree
func _initialize()->void: call_deferred("run")
func run()->void:
	var scene=load("res://preview.tscn").instantiate()
	root.add_child(scene)
	await create_timer(9.2).timeout
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://qa/gpu_playback.png")
	var passed:=true
	for key:String in scene.seen:
		passed=passed and scene.seen[key].size()==(6 if key.begins_with("attack") else 8)
	passed=passed and scene.finish_counts.attack_down_normal>=2 and scene.finish_counts.death_down_normal>=2 and scene.finish_counts.death_down_slow>=1 and scene.finish_counts.attack_down_slow>=1
	var report={"status":"PASS" if passed else "FAIL","scope":"runtime traversal only","seen":scene.seen,"loops":scene.loop_counts,"finished":scene.finish_counts,"seconds":scene.elapsed,"catalog_sha256":FileAccess.get_sha256("res://output/catalog_v006.json")}
	FileAccess.open("res://qa/gpu_playback.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print(JSON.stringify(report))
	quit(0 if passed else 1)
