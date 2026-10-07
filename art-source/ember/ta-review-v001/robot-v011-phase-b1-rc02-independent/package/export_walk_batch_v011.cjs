// 将阶段 B 的方向小样打成独立审阅资源；已经通过的 S / SW 按原字节引用。
// 预览工程只存在于本源目录，绝不修改主工程或阶段 A 冻结快照。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const ROOT=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const directions=['down','down_left','left','up_left','up','up_right','right','down_right'];
const revision=process.argv[2]||'phase-b1-rc01';
if(!/^phase-b\d-rc\d{2}$/.test(revision))throw Error('Invalid batch review revision');
const selected=process.argv.slice(3);
const walkDirections=directions.filter(d=>selected.length?selected.includes(d):!['left','right'].includes(d));
const replace=(text,from,to)=>{if(!text.includes(from))throw Error('Review template changed: '+from);return text.replaceAll(from,to);};
async function run(){
 const baselineFile=path.join(ROOT,'source/approved-phase-a-rc02-metadata.json');
 try{await fs.access(baselineFile);}catch(error){if(error.code!=='ENOENT')throw error;await fs.copyFile(path.join(ROOT,'review/phase-a-rc02/phase-a-metadata.json'),baselineFile);}
 const prior=JSON.parse(await fs.readFile(baselineFile,'utf8'));
 const clips=[],files=[],rawFrames=[];
 for(const[ row,d ]of walkDirections.entries()){
  const frames=[];
  for(let i=0;i<8;i++){
   const file=`frames/walk/${d}/robot_walk_${d}_f${String(i).padStart(2,'0')}_${d==='down'?'v010':'v011'}.png`;
   const bytes=await fs.readFile(path.join(ROOT,file)),raw=await sharp(bytes).ensureAlpha().raw().toBuffer();
   if(raw.length!==W*H*4)throw Error('Wrong cell size: '+file);
   const priorFrame=prior.clips.find(c=>c.name==='walk_'+d)?.frames[i];
   if(priorFrame&&sha(bytes)!==priorFrame.sha256)throw Error('Approved frame changed: '+file);
   const f={file,sha256:sha(bytes),frame:i,region:[i*W,row*H,W,H]};frames.push(f);files.push(f);rawFrames.push({raw,row,column:i});
  }
  clips.push({name:'walk_'+d,direction:d,action:'walk',fps:8,loop:true,frames,art_status:['down','down_left'].includes(d)?'PHASE_A_PASS_RETAINED':'NEW_CANDIDATE_PENDING_TA'});
 }
 for(const[i,d]of directions.entries()){
  const file=`source/candidate-masters/robot_idle_${d}_v011.png`,bytes=await fs.readFile(path.join(ROOT,file)),raw=await sharp(bytes).ensureAlpha().raw().toBuffer();
  const f={file,sha256:sha(bytes),frame:0,region:[i*W,walkDirections.length*H,W,H]};files.push(f);rawFrames.push({raw,row:walkDirections.length,column:i});
  clips.push({name:'pose_'+d,direction:d,action:'pose',fps:1,loop:false,frames:[f],art_status:d==='down'?'APPROVED_IDENTITY_REFERENCE_NOT_IDLE':'STATIC_IDENTITY_PASS_NOT_IDLE'});
 }
 const rows=walkDirections.length+1,atlas=Buffer.alloc(W*8*H*rows*4);
 for(const{raw,row,column}of rawFrames)for(let y=0;y<H;y++)raw.copy(atlas,((row*H+y)*W*8+column*W)*4,y*W*4,(y+1)*W*4);
 const atlasName='robot_walk_batch_atlas_v011.png';await sharp(atlas,{raw:{width:W*8,height:H*rows,channels:4}}).png().toFile(path.join(ROOT,atlasName));
 const metadata={revision:'v011-'+revision,status:'CANDIDATE_PENDING_TA',canvas:[W,H],root_anchor:[32,80],direction_order:directions,walk_directions:walkDirections,atlas:atlasName,atlas_sha256:sha(await fs.readFile(path.join(ROOT,atlasName))),phase_scope:`${walkDirections.length} walk directions, including approved S/SW; eight identity references are not final idle`,final_scope:{clips:24,frames:112,idle:[2,2,true],walk:[8,8,true],collect:[4,6,false]},clips,source_files:files,approved_baseline:'source/approved-phase-a-rc02-metadata.json'};
 await fs.writeFile(path.join(ROOT,'walk-batch-metadata.json'),JSON.stringify(metadata,null,2)+'\n');
 const project=path.join(ROOT,'godot-walk-review');await fs.mkdir(path.join(project,'assets'),{recursive:true});
 await fs.copyFile(path.join(ROOT,atlasName),path.join(project,'assets',atlasName));
 await fs.writeFile(path.join(project,'walk-batch-metadata.json'),JSON.stringify(metadata,null,2)+'\n');
 let tres=`[gd_resource type="SpriteFrames" load_steps=${files.length+2} format=3]\n\n[ext_resource type="Texture2D" path="res://assets/${atlasName}" id="1_atlas"]\n\n`;
 files.forEach((f,i)=>tres+=`[sub_resource type="AtlasTexture" id="Atlas_${i}"]\natlas = ExtResource("1_atlas")\nregion = Rect2(${f.region.join(', ')})\n\n`);
 let index=0;tres+='[resource]\nanimations = [\n'+clips.map(c=>`{ "frames": [${c.frames.map(()=>`{ "duration": 1.0, "texture": SubResource("Atlas_${index++}") }`).join(', ')}], "loop": ${c.loop}, "name": &"${c.name}", "speed": ${c.fps}.0 }`).join(',\n')+'\n]\n';
 await fs.writeFile(path.join(project,'robot_walk_batch_v011.tres'),tres);
 for(const clip of clips.filter(c=>c.action==='walk'))for(const delay of[125,500])for(const scale of[1,4]){
  const frames=await Promise.all(clip.frames.map(f=>sharp(path.join(ROOT,f.file)).resize(W*scale,H*scale,{kernel:'nearest'}).ensureAlpha().raw().toBuffer()));
  const film=Buffer.concat(frames),options={raw:{width:W*scale,height:H*8*scale,channels:4,pageHeight:H*scale}},stem=`previews/${clip.name}_${delay===125?'normal':'slow'}_${scale}x_v011`;
  await sharp(film,options).webp({lossless:true,loop:0,delay:Array(8).fill(delay)}).toFile(path.join(ROOT,stem+'.webp'));
  await sharp(film,options).gif({loop:0,delay:delay===125?[130,120,130,120,130,120,130,120]:Array(8).fill(delay),dither:0,interFrameMaxError:0,interPaletteMaxError:0}).toFile(path.join(ROOT,stem+'.gif'));
 }
 // 从已验证的独立审阅工程生成另一工程；更换资源名称和输出目录，保留 A 工程不动。
 for(const file of['project.godot','preview_phase_a.tscn','preview_phase_a.gd','verify_phase_a.gd']){
  let s=await fs.readFile(path.join(ROOT,'godot-review',file),'utf8');
  s=s.replaceAll('phase-a-metadata.json','walk-batch-metadata.json').replaceAll('robot_phase_a_v011.tres','robot_walk_batch_v011.tres').replaceAll('robot_phase_a_atlas_v011.png',atlasName).replaceAll('preview_phase_a','preview_walk_batch').replaceAll('gpu-playback/','gpu-walk-playback/').replaceAll('qa/godot_phase_a_v011.json','qa/godot_walk_batch_v011.json').replaceAll('PHASE A - CANDIDATE','WALK BATCH - CANDIDATE').replaceAll('Phase A review','Walk batch review').replaceAll('ROBOT_V011_PHASE_A','ROBOT_V011_WALK_BATCH');
  if(file==='preview_phase_a.gd')s=s.replace('var direction := "down_left"','var direction := "up_left"');
  if(file==='verify_phase_a.gd'){
   const at=s.indexOf('func _walk_phase_board()->void:');if(at<0)throw Error('GPU template changed');
   s=s.slice(0,at)+`func _walk_phase_board()->void:\n\tvar view:=_view(Vector2i(2048,384*metadata.walk_directions.size()))\n\tfor row in metadata.walk_directions.size():\n\t\tfor i in 8:\n\t\t\tvar sprite:=_sprite("walk_"+metadata.walk_directions[row],i,4)\n\t\t\tsprite.position+=Vector2(i*256,row*384);view.add_child(sprite)\n\t_save(await _read(view),"gpu-walk-playback/all_walk_same_phase_4x.png")\n`;
  }
  await fs.writeFile(path.join(project,file.replaceAll('phase_a','walk_batch')),s);
 }
 await fs.copyFile(path.join(ROOT,'verify_walk_transitions.gd'),path.join(project,'verify_walk_transitions.gd'));
 let html=await fs.readFile(path.join(ROOT,'review.html'),'utf8');
 html=replace(html,'左下行走修订：恢复固定大腿甲的轮廓和明暗，保留关节承接。','新增行走小样：左上、朝上、右上、右下。固定甲片，关节局部修形。');
 if(revision==='phase-b1-rc02')html=replace(html,'新增行走小样：左上、朝上、右上、右下。固定甲片，关节局部修形。','步相返修：东北、东南交错摆臂，朝北纵向投影。南、南西、北西保持原帧。');
 html=replace(html,'阶段 A · rc02 待复审',revision+' · 待审');
 html=replace(html,'phase-a-metadata.json','walk-batch-metadata.json');html=replace(html,'godot-review/project.godot','godot-walk-review/project.godot');
 html=replace(html,"$('#direction').value='down_left'","$('#direction').value='up_left'");
 html=replace(html,'朝下 v010 保留原帧','S / SW 保留已通过原帧');
 html=replace(html,"d==='down'?'朝下行走：已通过的 v010 原帧。':'rc02：画面左侧大腿甲已恢复固定源形状，八帧待复审。'","['down','down_left'].includes(d)?'保留已通过的阶段 A 行走原帧。':'新增行走小样：固定部件与局部关节修形，待独立审查。'");
 html=replace(html,'当前新内容：八向固定造型候选、左下行走 8 帧。单张固定造型不代表最终双帧待机；其他方向行走、待机微动和采集动作将在小样通过后继续补齐。',`本批有 ${walkDirections.length} 向行走，共 ${walkDirections.length*8} 帧，S/SW 已通过并保持原字节。其余新增方向待审；左右侧面行走、八向双帧待机与四帧采集仍在后续批次。固定造型只代表身份参考。`);
 const detailStart=html.indexOf('<details>'),detailEnd=html.indexOf('<div class="notes">');
 html=html.slice(0,detailStart)+walkDirections.filter(d=>!['down','down_left'].includes(d)).map(d=>`<details><summary>${d} · 八帧对照</summary><img class="contact" src="previews/walk_${d}_light_4x_v011.png" alt="${d}行走八帧联系图"></details>\n`).join('')+html.slice(detailEnd);
 html=replace(html,'自动切换八向造型','自动切换方向');html=replace(html,"$('#action').value='pose';turnStart=performance.now();update();","turnStart=performance.now();update();");
 html=replace(html,'<a href="previews/walk_down_left_normal_4x_v011.webp">','<a id="normal-link" href="previews/walk_up_left_normal_4x_v011.webp">');
 html=replace(html,'<a href="previews/walk_down_left_slow_4x_v011.webp">','<a id="slow-link" href="previews/walk_up_left_slow_4x_v011.webp">');
 html=replace(html,'last=performance.now();draw();',"for(const speed of ['normal','slow']){const link=$('#'+speed+'-link');link.hidden=clip.action!=='walk';if(clip.action==='walk')link.href='previews/'+clip.name+'_'+speed+'_4x_v011.webp';}last=performance.now();draw();");
 await fs.writeFile(path.join(ROOT,'walk-review.html'),html);
 const manifest=JSON.parse((await fs.readFile(path.join(ROOT,'run-manifest.json'),'utf8')).replace(/^\uFEFF/,''));
 manifest.status='PHASE_B1_CANDIDATE';manifest.phases[1].status='FOUR_NEW_WALK_DIRECTIONS_PENDING_TA';manifest.current_candidate_revision=revision;manifest.current_review_metadata='walk-batch-metadata.json';
 manifest.phase_b={walk_directions:walkDirections,new_direction_frames:walkDirections.filter(d=>!['down','down_left'].includes(d)).length*8,source_rig:'build_remaining_walk_v011.cjs',local_compositor:'composite_remaining_joints_v011.cjs',side_hidden_source:'source/side_hidden_parts_raw_v011.png',side_hidden_source_usage:'PREPARATION_ONLY_NOT_IN_CURRENT_FRAMES',motion_art_acceptance:'PENDING_TA'};
 await fs.writeFile(path.join(ROOT,'run-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({revision,walkDirections,walkFrames:walkDirections.length*8,identityReferences:8,atlas_sha256:metadata.atlas_sha256}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
