extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
 var scene=load("res://preview.tscn").instantiate()
 root.add_child(scene)
 await create_timer(9.2).timeout
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png("res://qa/assembly_runtime.png")
 var passed:=true
 for sprite:AnimatedSprite2D in scene.actors:
  var key:String=sprite.get_meta("key")
  passed=passed and scene.seen[key].size()==sprite.sprite_frames.get_frame_count(sprite.animation)
  if sprite.sprite_frames.get_animation_loop(sprite.animation):passed=passed and scene.loops[key]>=1
  else:passed=passed and scene.finished[key]>=1
 FileAccess.open("res://qa/assembly_runtime.json",FileAccess.WRITE).store_string(JSON.stringify({"status":"PASS" if passed else "FAIL","scope":"20 saved resources x normal/slow playback only","seen":scene.seen,"finished":scene.finished,"loops":scene.loops,"seconds":scene.elapsed,"recipe_sha256":FileAccess.get_sha256("res://assembly_recipe.json")},"\t"))
 quit(0 if passed else 1)
