// 只准备独立审阅工程和审计脚本，不接触主工程资源。
const fs=require('node:fs/promises'),path=require('node:path');
const base=__dirname,old=path.resolve(base,'../robot-fixed-rig-v009');
const write=(name,data)=>fs.writeFile(path.join(base,name),data);
async function run(){
 for(const dir of ['reference-v009','godot-review/assets'])await fs.mkdir(path.join(base,dir),{recursive:true});
 for(let i=0;i<8;i++){const name=`robot_walk_down_f${String(i).padStart(2,'0')}_v009.png`;await fs.copyFile(path.join(old,'frames',name),path.join(base,'reference-v009',name));}
 await fs.copyFile(path.join(base,'robot_walk_down_atlas_v010.png'),path.join(base,'godot-review/assets/robot_walk_down_atlas_v010.png'));
 const replace=s=>s.replaceAll('v009','v010').replaceAll('V009','V010').replaceAll('robot-fixed-rig-v010','robot-joint-repair-v010');
 let verify=replace(await fs.readFile(path.join(old,'godot-review/verify_fixed_rig_playback_v009.gd'),'utf8'));
 verify=verify.replaceAll('source/rig_down_v010.json','qa/local_composite_v010.json');
 await write('godot-review/verify_joint_playback_v010.gd',verify);
 let resource=replace(await fs.readFile(path.join(old,'godot-review/robot_sprite_frames_v009.tres'),'utf8')).replace('FixedRigWalkDownV010Candidate','JointRepairWalkDownV010Candidate');
 await write('godot-review/robot_sprite_frames_v010.tres',resource);
 // 只带 params；Godot 冷导入重新建立缓存路径与 UID。
 const priorImport=await fs.readFile(path.join(old,'godot-review/assets/robot_walk_down_atlas_v009.png.import'),'utf8');
 await write('godot-review/assets/robot_walk_down_atlas_v010.png.import','[remap]\nimporter="texture"\ntype="CompressedTexture2D"\n\n[params]'+priorImport.split('[params]')[1]);
 await write('godot-review/project.godot','config_version=5\n[application]\nconfig/name="Robot Joint Repair v010"\nrun/main_scene="res://preview_joint_v010.tscn"\n[display]\nwindow/size/viewport_width=640\nwindow/size/viewport_height=480\n[rendering]\nrenderer/rendering_method="gl_compatibility"\nrenderer/rendering_method.mobile="gl_compatibility"\ntextures/canvas_textures/default_texture_filter=0\nanti_aliasing/quality/msaa_2d=0\n');
 await write('godot-review/preview_joint_v010.tscn','[gd_scene load_steps=3 format=3]\n[ext_resource type="Script" path="res://preview_joint_v010.gd" id="1"]\n[ext_resource type="SpriteFrames" path="res://robot_sprite_frames_v010.tres" id="2"]\n[node name="Preview" type="Node2D"]\nscript=ExtResource("1")\n[node name="Robot" type="AnimatedSprite2D" parent="."]\ntexture_filter=1\nposition=Vector2(320,340)\nscale=Vector2(4,4)\ncentered=false\noffset=Vector2(-32,-80)\nsprite_frames=ExtResource("2")\nanimation=&"walk_down"\nautoplay="walk_down"\n');
 await write('godot-review/preview_joint_v010.gd','extends Node2D\n## 空格暂停，左右键逐帧；B 切换深浅背景。\nvar light := false\nfunc _ready() -> void:\n\tRenderingServer.set_default_clear_color(Color("182631"))\nfunc _unhandled_key_input(event: InputEvent) -> void:\n\tif not event.is_pressed() or event.is_echo(): return\n\tvar robot := $Robot as AnimatedSprite2D\n\tif event.keycode == KEY_SPACE:\n\t\tif robot.is_playing(): robot.pause()\n\t\telse: robot.play("walk_down")\n\telif event.keycode == KEY_LEFT or event.keycode == KEY_RIGHT:\n\t\trobot.pause()\n\t\trobot.frame = posmod(robot.frame + (-1 if event.keycode == KEY_LEFT else 1),8)\n\telif event.keycode == KEY_B:\n\t\tlight = not light\n\t\tRenderingServer.set_default_clear_color(Color("ece9d8" if light else "182631"))\n');
 // 专用 skill 的审计默认正方形；保留算法，仅适配项目已锁定的 64×96 整格。
 let audit=await fs.readFile('C:/Users/shiru/.codex/skills/character-animation-creator-skill/scripts/audit_sprite_motion.py','utf8');
 audit=audit.replace('parser.add_argument("--cell", type=int, default=64)','parser.add_argument("--cell-width", type=int, default=64)\n    parser.add_argument("--cell-height", type=int, default=96)');
 audit=audit.replace('expected = (args.columns * args.cell, args.rows * args.cell)','expected = (args.columns * args.cell_width, args.rows * args.cell_height)');
 audit=audit.replace('box = (col * args.cell, row * args.cell, (col + 1) * args.cell, (row + 1) * args.cell)','box = (col * args.cell_width, row * args.cell_height, (col + 1) * args.cell_width, (row + 1) * args.cell_height)');
 await write('qa/audit_sprite_motion_rect.py',audit);
 console.log('Prepared isolated review, reference frames and rectangular skill audit.');
}
run().catch(e=>{console.error(e);process.exitCode=1;});
