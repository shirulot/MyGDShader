extends SceneTree
const Rig=preload("res://action_rig.gd")
func _initialize()->void: call_deferred("run")
func run()->void:
	var scene=load("res://preview.tscn").instantiate()
	root.add_child(scene)
	await create_timer(9.2).timeout
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("res://qa/gpu_playback.png")
	var passed:=true
	for key:String in scene.seen:
		var action:=key.trim_suffix("_normal").trim_suffix("_slow")
		passed=passed and scene.seen[key].size()==Rig.CLIPS[action].poses.size()
	passed=passed and scene.loop_counts.idle_down_normal>=2 and scene.loop_counts.move_down_normal>=2
	for action:String in ["attack_down","hit_down","death_down"]:
		passed=passed and scene.finish_counts[action+"_normal"]>=2 and scene.finish_counts[action+"_slow"]>=1
	var report={"status":"PASS" if passed else "FAIL","scope":"runtime traversal only","seen":scene.seen,"loops":scene.loop_counts,"finished":scene.finish_counts,"seconds":scene.elapsed,"catalog_sha256":FileAccess.get_sha256("res://output/catalog_v010.json")}
	FileAccess.open("res://qa/gpu_playback.json",FileAccess.WRITE).store_string(JSON.stringify(report,"\t"))
	print(JSON.stringify(report))
	quit(0 if passed else 1)

