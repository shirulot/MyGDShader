extends SceneTree
## 候选骨架渲染器：母稿层只读，真实三维骨长保持，前视投影交给Godot纹理光栅化。
## 只用固定部件/关节几何；不根据输出Alpha补洞、不逐帧bbox定心或拉伸骨长。

const BASE := "art-source/ember/robot-fixed-rig-v007/"
const RIG_FILE := BASE + "source/rig_down_v007.json"
const SIZE := Vector2i(64,96)
const ROOT_ANCHOR := Vector2(32,80)
const PHASES := ["left_contact","left_down","right_passing","right_up","right_contact","right_down","left_passing","left_up"]
const BODY_BOB := [1.0,1.6,1.2,0.6,1.0,1.6,1.2,0.6]
# 固定一次降低母稿骨盆1px，给真实15px腿链留下屈膝余量；每帧骨长完全相同。
const BIND_BODY_LOWER := 1.0
var workspace := ""
var rig: Dictionary
var rest := {}
var bones := {}
var images := {}
var textures := {}
var source_hashes := {}
var errors: Array = []
var frame_records: Array = []
var owner_shader := Shader.new()

func _initialize() -> void: call_deferred("_run")
func _abs(file: String) -> String: return workspace.path_join(file.trim_prefix("res://"))
func _json(file: String) -> Dictionary: return JSON.parse_string(FileAccess.get_file_as_string(_abs(file)))
func _write(file: String,value: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(_abs(file).get_base_dir())
	var output := FileAccess.open(_abs(file),FileAccess.WRITE)
	output.store_string(JSON.stringify(value,"\t",false,true)+"\n")
func _v2(value: Array) -> Vector2: return Vector2(float(value[0]),float(value[1]))
func _project(value: Vector3) -> Vector2: return Vector2(value.x,value.y)
func _arr(value: Vector3) -> Array: return [value.x,value.y,value.z]

func _run() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--workspace="): workspace=arg.trim_prefix("--workspace=")
	if workspace.is_empty() or DisplayServer.get_name()=="headless": push_error("需要--workspace及真实GPU窗口渲染器"); quit(1); return
	rig=_json(RIG_FILE)
	source_hashes[RIG_FILE]=FileAccess.get_sha256(_abs(RIG_FILE))
	source_hashes[str(rig.source_master)]=FileAccess.get_sha256(_abs(str(rig.source_master)))
	for key: String in rig.keypoints: rest[key]=_v2(rig.keypoints[key])
	for bone: Dictionary in rig.bones: bones[str(bone.id)]=bone
	for part: Dictionary in rig.parts:
		var image := Image.load_from_file(_abs(str(part.path))); image.convert(Image.FORMAT_RGBA8)
		images[str(part.id)]=image; textures[str(part.id)]=ImageTexture.create_from_image(image)
		source_hashes[str(part.path)]=FileAccess.get_sha256(_abs(str(part.path)))
	owner_shader.code="shader_type canvas_item; render_mode unshaded; uniform vec4 owner_color; void fragment(){ COLOR=vec4(owner_color.rgb,texture(TEXTURE,UV).a); }"
	var bind := _pose(-1)
	var canonical := await _capture(bind,false)
	var canonical_file := BASE+"source/robot_idle_down_fixed_rig_canonical_v007.png"
	canonical.save_png(_abs(canonical_file))
	_write(BASE+"source/canonical_bind_pose_v007.json",_pose_json(bind))
	var atlas := Image.create(512,96,false,Image.FORMAT_RGBA8); atlas.fill(Color(0,0,0,0))
	for index in 8:
		var pose := _pose(index)
		var image := await _capture(pose,false)
		var owners := await _capture(pose,true)
		var owner_file := BASE+"owner_maps/walk_down_f%02d_owner_v007.png"%index
		DirAccess.make_dir_recursive_absolute(_abs(owner_file).get_base_dir()); owners.save_png(_abs(owner_file))
		var file := BASE+"frames/robot_walk_down_f%02d_v007.png"%index
		DirAccess.make_dir_recursive_absolute(_abs(file).get_base_dir()); image.save_png(_abs(file))
		atlas.blit_rect(image,Rect2i(Vector2i.ZERO,SIZE),Vector2i(index*64,0))
		var record := _pose_json(pose)
		record["file"]="res://"+file; record["sha256"]=FileAccess.get_sha256(_abs(file)); record["measurement"]=_measure(image)
		record["stable_parts"]=_stable_owner_mapping(pose,image,owners)
		record["owner_map_file"]="res://"+owner_file
		record["owner_map_sha256"]=FileAccess.get_sha256(_abs(owner_file))
		for side: String in ["left","right"]:
			var stance: bool=record.contacts[side].stance
			var sole: Vector2=rest["sole_"+side]
			var contact_alpha:=image.get_pixel(int(sole.x),79).a8 if stance else -1
			record.contacts[side]["registered_sole_source_pixel"]=[int(sole.x),79]
			record.contacts[side]["actual_gpu_contact_pixel_alpha"]=contact_alpha
			if stance and contact_alpha!=255: errors.append("支撑脚接地点非实体: f%d/%s"%[index,side])
		if not record.measurement.binary_alpha or not record.measurement.palette_registered: errors.append("GPU源帧Alpha/调色板失败: f%d"%index)
		_write(BASE+"poses/walk_down_f%02d_v007.json"%index,record); frame_records.append(record)
		# 骨轴图仅另存，绝不混入正式候选帧。
		var overlay := await _capture(pose,false,true)
		var overlay_file := BASE+"overlays/walk_down_f%02d_overlay_v007.png"%index
		DirAccess.make_dir_recursive_absolute(_abs(overlay_file).get_base_dir()); overlay.save_png(_abs(overlay_file))
	var atlas_file:=BASE+"robot_walk_down_atlas_v007.png"; atlas.save_png(_abs(atlas_file))
	_build_preview_resource(atlas_file)
	for file: String in source_hashes:
		if FileAccess.get_sha256(_abs(file))!=source_hashes[file]: errors.append("原母稿/rig/部件SHA改变: "+file)
	_write(BASE+"fixed_rig_render_v007.json",{"status":"CANDIDATE","technical_checks":"PASS" if errors.is_empty() else "FAIL","errors":errors,
		"source_hashes":source_hashes,"renderer_sha256":FileAccess.get_sha256(get_script().resource_path),"engine":Engine.get_version_info(),
		"gpu_renderer":RenderingServer.get_video_adapter_name(),"canvas":[64,96],"root_anchor":[32,80],"fps":8,"frames":frame_records,
		"canonical":{"file":canonical_file,"sha256":FileAccess.get_sha256(_abs(canonical_file)),"measure":_measure(canonical),"bind_body_lower_px":BIND_BODY_LOWER,"status":"RIG_DERIVED_NATIVE_CANDIDATE_NOT_HAND_PIXEL_FINAL"},
		"projection":"Orthographic front XY projection; YZ two-bone IK with fixed X splay. Pixel UVs use rest layers. Longitudinal foreshortening follows real bone pitch, not arbitrary scale.",
		"caps":"13 once-authored native cuff/crossbeam polygons from rig, placed by joints, single-sided steel shade; no alpha gap detector.",
		"old_assets_changed":false,"art_acceptance":"NOT_CLAIMED"})
	print("FIXED_RIG_V007 CANDIDATE technical=", "PASS" if errors.is_empty() else "FAIL")
	for error: String in errors: push_error(error)
	quit(0 if errors.is_empty() else 1)

func _pose(index: int) -> Dictionary:
	var points := {}
	var bob: float=BIND_BODY_LOWER if index<0 else BODY_BOB[index]
	for key: String in rest:
		var p: Vector2=rest[key]; points[key]=Vector3(p.x,p.y+bob,0)
	points.root=Vector3(32,80,0)
	var leg_z_left: float=0 if index<0 else [2.8,1.0,-1.0,-2.8,-2.8,-2.0,0.0,2.4][index]
	var leg_z_right: float=0 if index<0 else [-2.8,-2.0,0.0,2.4,2.8,1.0,-1.0,-2.8][index]
	var lift_left: float=0 if index<0 else [0,0,0,0,0,1.0,3.0,1.2][index]
	var lift_right: float=0 if index<0 else [0,1.0,3.0,1.2,0,0,0,0][index]
	_solve_leg(points,"left",leg_z_left,lift_left)
	_solve_leg(points,"right",leg_z_right,lift_right)
	var counter: float=0 if index<0 else [-18,-12,0,15,18,12,0,-15][index]
	_solve_arm(points,"left",counter,12)
	_solve_arm(points,"right",-counter,12)
	var support: String="both" if index<0 else ("left" if index<4 else "right")
	return {"index":index,"phase":"canonical_relaxed_bind" if index<0 else PHASES[index],"points":points,"body_lower":bob,"support_leg":support,
		"lift":{"left":lift_left,"right":lift_right},"depth":{"left":leg_z_left,"right":leg_z_right}}

func _solve_leg(points: Dictionary,side: String,z: float,lift: float) -> void:
	var hip: Vector3=points["hip_"+side]
	var knee_rest: Vector2=rest["knee_"+side]; var ankle_rest: Vector2=rest["ankle_"+side]
	var length_a: float=absf(knee_rest.y-rest["hip_"+side].y)
	var length_b: float=absf(ankle_rest.y-knee_rest.y)
	var ankle:=Vector3(ankle_rest.x,ankle_rest.y-lift,z)
	var yz:=Vector2(ankle.y-hip.y,ankle.z-hip.z); var distance:=yz.length()
	if distance>length_a+length_b+0.00001: errors.append("腿目标不可达，禁止拉伸: "+side)
	var along: float=(length_a*length_a-length_b*length_b+distance*distance)/(2*distance)
	var height: float=sqrt(maxf(0,length_a*length_a-along*along))
	var direction:=yz/distance; var knee_yz:=direction*along+Vector2(-direction.y,direction.x)*height
	points["knee_"+side]=Vector3(knee_rest.x,hip.y+knee_yz.x,hip.z+knee_yz.y)
	points["ankle_"+side]=ankle
	points["sole_"+side]=ankle+Vector3(0,rest["sole_"+side].y-ankle_rest.y,0)

func _solve_arm(points: Dictionary,side: String,upper_deg: float,elbow_deg: float) -> void:
	var shoulder: Vector3=points["shoulder_"+side]
	var upper: Vector2=rest["elbow_"+side]-rest["shoulder_"+side]
	var lower: Vector2=rest["wrist_"+side]-rest["elbow_"+side]
	var a:=deg_to_rad(upper_deg); var b:=deg_to_rad(upper_deg+elbow_deg)
	var elbow:=shoulder+Vector3(upper.x,upper.y*cos(a),upper.y*sin(a))
	points["elbow_"+side]=elbow
	points["wrist_"+side]=elbow+Vector3(lower.x,lower.y*cos(b),lower.y*sin(b))

func _pose_json(pose: Dictionary) -> Dictionary:
	var p: Dictionary=pose.points; var points3d:={}; var points2d:={}; var measures: Array=[]
	for key: String in p: points3d[key]=_arr(p[key]); points2d[key]=[p[key].x,p[key].y]
	for bone: Dictionary in rig.bones:
		var from: Vector3=p[str(bone.from)]; var to: Vector3=p[str(bone.to)]; var vector:=to-from
		var actual:=vector.length(); var error:=absf(actual-float(bone.rest_length))
		if error>0.0001: errors.append("骨长改变: "+str(bone.id)+" error="+str(error))
		measures.append({"bone":bone.id,"rest_length":bone.rest_length,"actual_length_3d":actual,"length_error":error,
			"projected_length":Vector2(vector.x,vector.y).length(),"angle_yz_degrees":rad_to_deg(atan2(vector.z,vector.y))})
	var contacts:={}
	for side: String in ["left","right"]:
		contacts[side]={"stance":pose.support_leg==side or pose.support_leg=="both","sole_boundary_y":p["sole_"+side].y,
			"ankle3d":_arr(p["ankle_"+side]),"lift_px":pose.lift[side],"contact_definition":"registered sole source pixel ending at y80, not sprite bbox"}
	return {"status":"CANDIDATE","phase":pose.phase,"frame_index":pose.index,"root_anchor":[32,80],"support_leg":pose.support_leg,
		"source_rig_sha256":source_hashes[RIG_FILE],"source_master_sha256":source_hashes[str(rig.source_master)],
		"canonical_bind_body_lower":BIND_BODY_LOWER,"pelvis_bob":pose.body_lower-BIND_BODY_LOWER,"body_lower_from_original":pose.body_lower,
		"keypoints3d":points3d,"keypoints_projected":points2d,"bone_measures":measures,"contacts":contacts,
		"whole_sprite_scale":1,"bbox_alignment":"NONE","part_transforms":_part_transform_records(pose)}

func _map_point(point: Vector2,bone_id: String,pose: Dictionary) -> Vector2:
	var bone: Dictionary=bones[bone_id]
	var from: Vector2=rest[str(bone.from)]; var to: Vector2=rest[str(bone.to)]
	var actual_from: Vector3=pose.points[str(bone.from)]; var actual_to: Vector3=pose.points[str(bone.to)]
	var ratio: float=(actual_to.y-actual_from.y)/(to.y-from.y)
	return Vector2(point.x+(actual_from.x-from.x),actual_from.y+(point.y-from.y)*ratio)

func _part_transform_records(pose: Dictionary) -> Array:
	var records: Array=[]
	for part: Dictionary in rig.parts:
		var bone: Dictionary=bones[str(part.parent_bone)]
		var a: Vector2=rest[str(bone.from)]; var b: Vector2=rest[str(bone.to)]
		var aa: Vector3=pose.points[str(bone.from)]; var bb: Vector3=pose.points[str(bone.to)]
		records.append({"part":part.id,"source_sha256":source_hashes[str(part.path)],"bone":part.parent_bone,
			"pitch_projection_y_ratio":(bb.y-aa.y)/(b.y-a.y),"basis":"fixed physical bone X-splay and YZ pitch projection; source UV unchanged"})
	return records

func _material(owner_id: int,owner_pass: bool) -> Material:
	if owner_pass:
		var material:=ShaderMaterial.new(); material.shader=owner_shader; material.set_shader_parameter("owner_color",Color(float(owner_id)/255,0,0,1)); return material
	var material:=CanvasItemMaterial.new(); material.light_mode=CanvasItemMaterial.LIGHT_MODE_UNSHADED; return material

func _polygon(parent: Node,points: PackedVector2Array,color: Color,z: int,owner_id: int,owner_pass: bool) -> Polygon2D:
	var polygon:=Polygon2D.new(); polygon.polygon=points; polygon.color=color; polygon.antialiased=false; polygon.z_index=z
	polygon.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST; polygon.material=_material(owner_id,owner_pass); parent.add_child(polygon); return polygon

func _rig_nodes(pose: Dictionary,owner_pass: bool,overlay: bool) -> Node2D:
	var node:=Node2D.new(); node.name="FixedRigRoot"; node.position=ROOT_ANCHOR
	# Godot实际关节树沿rig父骨关系建立。世界角由真实3D骨前视投影导出；
	# 下方纹理quad再转到该父骨局部坐标，保持同一物理投影而非机械逐层平移。
	var joint_nodes:={"root":node}
	for bone: Dictionary in rig.bones:
		var joint:=Node2D.new(); joint.name=str(bone.id)
		var parent: Node2D=joint_nodes[str(bone.parent)]; parent.add_child(joint)
		var origin:=_project(pose.points[str(bone.from)])
		var direction:=_project(pose.points[str(bone.to)])-origin
		joint.transform=parent.global_transform.affine_inverse()*Transform2D(direction.angle(),origin)
		joint_nodes[str(bone.id)]=joint
	var cap_id:=100
	for cap: Dictionary in rig.cap_definitions:
		var pivot: Vector2=rest[str(cap.pivot_keypoint)]; var points:=PackedVector2Array()
		var bone: Dictionary=bones[str(cap.parent_bone)]
		var before: Vector2=rest[str(bone.to)]-rest[str(bone.from)]
		var after: Vector2=_project(pose.points[str(bone.to)])-_project(pose.points[str(bone.from)])
		var angle:=after.angle()-before.angle(); var center:=_project(pose.points[str(cap.pivot_keypoint)])
		var joint: Node2D=joint_nodes[str(cap.parent_bone)]
		var to_local:=joint.global_transform.affine_inverse()
		for value: Array in cap.local_polygon: points.append(to_local*(center+_v2(value).rotated(angle)))
		_polygon(joint,points,Color(str(cap.medium_color)),10,cap_id,owner_pass)
		# 固定单侧阴影，不把4px轴承四边包黑缩成细针。源装甲在其上搭接。
		var extent:=float(cap.get("span_native",cap.width_native))*0.5; var low: float=0; var high: float=0
		for value: Array in cap.local_polygon: low=minf(low,float(value[1])); high=maxf(high,float(value[1]))
		var shade:=PackedVector2Array()
		for value: Vector2 in [Vector2(-extent,low+1),Vector2(-extent+1,low+1),Vector2(-extent+1,high-1),Vector2(-extent,high-1)]: shade.append(to_local*(center+value.rotated(angle)))
		_polygon(joint,shade,Color(str(cap.edge_color)),11,cap_id,owner_pass); cap_id+=1
	for index in rig.parts.size():
		var part: Dictionary=rig.parts[index]; var id:=str(part.id); var bbox: Array=part.bbox
		var corners:=[Vector2(bbox[0],bbox[1]),Vector2(bbox[0]+bbox[2],bbox[1]),Vector2(bbox[0]+bbox[2],bbox[1]+bbox[3]),Vector2(bbox[0],bbox[1]+bbox[3])]
		var points:=PackedVector2Array(); var uv:=PackedVector2Array()
		var joint: Node2D=joint_nodes[str(part.parent_bone)]
		var to_local:=joint.global_transform.affine_inverse()
		for corner: Vector2 in corners: points.append(to_local*_map_point(corner,str(part.parent_bone),pose)); uv.append(corner)
		var z:=30+int(part.draw_order)
		if id.begins_with("elbow_") or id.begins_with("knee_") or id in ["waist_core","pelvis_core"]: z=0
		if id=="chest_shell": z=80
		if "arm_" in id or id.begins_with("shoulder_") or id.begins_with("hand_") or id=="left_wrist_tool":
			var side: String="left" if id.ends_with("left") or id=="left_wrist_tool" else "right"
			z=(90 if pose.points["wrist_"+side].z>=0 else 40)+int(part.draw_order)
		if id=="head": z=200
		var polygon:=_polygon(joint,points,Color.WHITE,z,index+1,owner_pass); polygon.uv=uv; polygon.texture=textures[id]
	if overlay:
		for bone: Dictionary in rig.bones:
			var line:=Line2D.new(); line.points=PackedVector2Array([_project(pose.points[str(bone.from)])-ROOT_ANCHOR,_project(pose.points[str(bone.to)])-ROOT_ANCHOR]); line.width=0.4; line.default_color=Color(1,0.35,0.2); line.z_index=300; node.add_child(line)
	return node

func _capture(pose: Dictionary,owner_pass: bool,overlay: bool=false) -> Image:
	var viewport:=SubViewport.new(); viewport.size=SIZE; viewport.transparent_bg=true; viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	viewport.canvas_item_default_texture_filter=Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST; viewport.msaa_2d=Viewport.MSAA_DISABLED
	viewport.add_child(_rig_nodes(pose,owner_pass,overlay)); root.add_child(viewport)
	await process_frame; await process_frame; await RenderingServer.frame_post_draw
	var image:=viewport.get_texture().get_image(); image.convert(Image.FORMAT_RGBA8)
	root.remove_child(viewport); viewport.free(); return image

func _stable_owner_mapping(pose: Dictionary,image: Image,owners: Image) -> Dictionary:
	var result:={}
	for id: String in ["head","chest_shell"]:
		var index:=0
		for i in rig.parts.size():
			if str(rig.parts[i].id)==id: index=i; break
		var part: Dictionary=rig.parts[index]; var source: Image=images[id]; var mapped: Array=[]; var occluded:=0; var unknown:=0
		for y in 96:
			for x in 64:
				if source.get_pixel(x,y).a8==0: continue
				var target:=_map_point(Vector2(x+0.5,y+0.5),str(part.parent_bone),pose).floor(); var point:=Vector2i(target)
				if owners.get_pixelv(point).r8!=index+1: occluded+=1; continue
				if image.get_pixelv(point)!=source.get_pixel(x,y): unknown+=1; continue
				mapped.append([point.x,point.y,x,y])
		result["head" if id=="head" else "chest"]={"visible_source_pixels":mapped,"occluded_source_pixel_count":occluded,"source_pixel_count":part.pixel_count,
			"unknown_rgba_samples":unknown,"transform_note":"Actual separate GPU owner-ID pass; fixed source UV, no source-part scaling for head/chest. Frame coordinates retain whole-cell root."}
	return result

func _measure(image: Image) -> Dictionary:
	var binary:=true; var palette:=true; var count:=0; var colors:={}
	for y in 96:
		for x in 64:
			var value:=image.get_pixel(x,y); binary=binary and value.a8 in [0,255]
			if value.a8==0: continue
			count+=1; var key:="#"+value.to_html(false).to_upper(); colors[key]=true; palette=palette and key in rig.palette
	var bbox:=image.get_used_rect()
	return {"canvas":[64,96],"binary_alpha":binary,"palette_registered":palette,"colors":colors.keys(),"opaque_pixels":count,
		"bbox_xywh":[bbox.position.x,bbox.position.y,bbox.size.x,bbox.size.y],"visible_bottom_boundary":bbox.end.y,"root_is_not_bbox":true}

func _build_preview_resource(atlas_file: String) -> void:
	var local_atlas:="res://assets/robot_walk_down_atlas_v007.png"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://assets")); DirAccess.copy_absolute(_abs(atlas_file),ProjectSettings.globalize_path(local_atlas))
	# 候选工程禁止导入器改变透明RGB；正式原生PNG从不经此步骤修改。
	var import_settings:=ConfigFile.new()
	if FileAccess.file_exists(local_atlas+".import"): import_settings.load(local_atlas+".import")
	else:
		import_settings.set_value("remap","importer","texture")
		import_settings.set_value("remap","type","CompressedTexture2D")
		import_settings.set_value("deps","source_file",local_atlas)
	import_settings.set_value("params","compress/mode",0)
	import_settings.set_value("params","mipmaps/generate",false)
	import_settings.set_value("params","process/fix_alpha_border",false)
	import_settings.set_value("params","process/premult_alpha",false)
	import_settings.save(local_atlas+".import")
	var text:="[gd_resource type=\"SpriteFrames\" format=3]\n\n[ext_resource type=\"Texture2D\" path=\"%s\" id=\"1_atlas\"]\n\n"%local_atlas
	for index in 8: text+="[sub_resource type=\"AtlasTexture\" id=\"Frame_%d\"]\natlas = ExtResource(\"1_atlas\")\nregion = Rect2(%d, 0, 64, 96)\nfilter_clip = true\n\n"%[index,index*64]
	text+="[resource]\nresource_name=\"FixedRigWalkDownV007Candidate\"\nanimations=[{\"frames\":["
	for index in 8: text+="{\"duration\":1.0,\"texture\":SubResource(\"Frame_%d\")}%s"%[index,"," if index<7 else ""]
	text+="],\"loop\":true,\"name\":&\"walk_down\",\"speed\":8.0}]\n"
	var file:=FileAccess.open("res://robot_sprite_frames_v007.tres",FileAccess.WRITE); file.store_string(text)
