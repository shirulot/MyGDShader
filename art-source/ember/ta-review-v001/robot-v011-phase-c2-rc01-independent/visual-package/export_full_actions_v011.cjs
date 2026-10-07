// 24段/112帧统一导出。已通过70帧与8身份母版先核哈希；新动图写独立full子目录。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {contact}=require('./build_fixed_rig_v011.cjs');
const root=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const directions=['down','down_left','left','up_left','up','up_right','right','down_right'];
const read=async file=>JSON.parse(await fs.readFile(path.join(root,file),'utf8'));
async function run(){
 const walkRegistry=await read('source/walk-acceptance-v011.json'),actionRegistry=await read('source/action-acceptance-v011.json');
 const accepted=[...walkRegistry.clips,...actionRegistry.clips].flatMap(c=>c.frames);
 const mothers=(await read('source/reference-phase-b2-rc01-metadata.json')).clips.filter(c=>c.action==='pose').flatMap(c=>c.frames);
 for(const frame of [...accepted,...mothers])if(sha(await fs.readFile(path.join(root,frame.file)))!==frame.sha256)throw Error('Approved image changed: '+frame.file);
 const approvedFiles=new Set(accepted.map(f=>f.file)),width=512,height=96*24,atlas=Buffer.alloc(width*height*4),clips=[],rawByClip=new Map();
 for(const direction of directions)for(const[action,count,fps,loop]of [['idle',2,2,true],['walk',8,8,true],['collect',4,6,false]]){
  const row=clips.length,frames=[],pixels=[];
  for(let i=0;i<count;i++){
   const version=action==='walk'&&direction==='down'?'v010':'v011';
   const file=`frames/${action}/${direction}/robot_${action}_${direction}_f${String(i).padStart(2,'0')}_${version}.png`;
   const bytes=await fs.readFile(path.join(root,file)),raw=await sharp(bytes).ensureAlpha().raw().toBuffer();
   for(let y=0;y<96;y++)raw.copy(atlas,((row*96+y)*width+i*64)*4,y*64*4,(y+1)*64*4);
   frames.push({file,frame:i,sha256:sha(bytes),region:[i*64,row*96,64,96]});pixels.push(raw);
  }
  const name=action+'_'+direction;rawByClip.set(name,pixels);
  clips.push({name,direction,action,fps,loop,frames,art_status:frames.every(f=>approvedFiles.has(f.file))?'PASS_RETAINED':'C2_NEW_ACTION_PENDING_TA'});
 }
 const atlasName='robot_eight_way_actions_atlas_v011.png';await sharp(atlas,{raw:{width,height,channels:4}}).png().toFile(path.join(root,atlasName));
 const meta={revision:'v011-phase-c2-rc01',status:'ALL_FRAMES_AUTHORED_NEW_42_PENDING_TA',canvas:[64,96],root_anchor:[32,80],directions,
  atlas:atlasName,atlas_size:[width,height],atlas_sha256:sha(await fs.readFile(path.join(root,atlasName))),clips,total_clips:24,total_frames:112,
  accepted_frames_preserved:70,identity_masters_preserved:8,new_frames:42,production_assets_modified:false};
 await fs.writeFile(path.join(root,'full-action-metadata.json'),JSON.stringify(meta,null,2)+'\n');
 const project=path.join(root,'godot-full-review');await fs.mkdir(path.join(project,'assets'),{recursive:true});
 await fs.copyFile(path.join(root,atlasName),path.join(project,'assets',atlasName));
 await fs.writeFile(path.join(project,'full-action-metadata.json'),JSON.stringify(meta,null,2)+'\n');
 let tres=`[gd_resource type="SpriteFrames" load_steps=114 format=3]\n\n[ext_resource type="Texture2D" path="res://assets/${atlasName}" id="1_atlas"]\n\n`,index=0;
 for(const clip of clips)for(const f of clip.frames)tres+=`[sub_resource type="AtlasTexture" id="Atlas_${index++}"]\natlas = ExtResource("1_atlas")\nregion = Rect2(${f.region.join(', ')})\n\n`;
 index=0;tres+='[resource]\nanimations = [\n'+clips.map(c=>`{ "frames": [${c.frames.map(()=>`{ "duration": 1.0, "texture": SubResource("Atlas_${index++}") }`).join(', ')}], "loop": ${c.loop}, "name": &"${c.name}", "speed": ${c.fps}.0 }`).join(',\n')+'\n]\n';
 await fs.writeFile(path.join(project,'robot_eight_way_v011.tres'),tres);
 let importer=await fs.readFile(path.join(root,'godot-action-review/assets/robot_action_pilot_atlas_v011.png.import'),'utf8');
 await fs.writeFile(path.join(project,'assets',atlasName+'.import'),importer.replaceAll('robot_action_pilot_atlas_v011.png',atlasName));
 await fs.mkdir(path.join(root,'previews/full'),{recursive:true});const animations=[];
 for(const clip of clips)for(const scale of[1,4])for(const speed of['normal','slow']){
  const source=rawByClip.get(clip.name),count=source.length,fps=clip.fps*(speed==='slow'?.25:1);
  const frames=await Promise.all(source.map(raw=>sharp(raw,{raw:{width:64,height:96,channels:4}}).resize(64*scale,96*scale,{kernel:'nearest'}).raw().toBuffer()));
  const raw=Buffer.concat(frames),options={raw:{width:64*scale,height:96*count*scale,channels:4,pageHeight:96*scale}};
  for(const ext of['webp','gif']){
   const quantum=ext==='gif'?10:1,delay=Array.from({length:count},(_,i)=>(Math.round((i+1)*1000/fps/quantum)-Math.round(i*1000/fps/quantum))*quantum);
   const file=`previews/full/${clip.name}_${speed}_${scale}x_v011.${ext}`,pipeline=sharp(raw,options),loop=clip.loop?0:1;
   if(ext==='webp')pipeline.webp({lossless:true,loop,delay});else pipeline.gif({loop,delay,dither:0,interFrameMaxError:0,interPaletteMaxError:0});
   await pipeline.toFile(path.join(root,file));animations.push({file,clip:clip.name,scale,speed,delay,loop_encoded:loop});
  }
 }
 await fs.writeFile(path.join(root,'qa/full_action_animated_exports.json'),JSON.stringify(animations,null,2)+'\n');
 // 联系图每行：idle F00/F01，collect F00/F01/F02/F03；仅拼装实际最终帧。
 for(const[group,dirs]of [['front_back',['down','up']],['sides',['left','right']],['diagonals',['up_left','up_right','down_right']]]){
  const frames=dirs.flatMap(d=>[...rawByClip.get('idle_'+d),...rawByClip.get('collect_'+d)]);
  for(const[bg,color]of [['light',[236,233,216]],['dark',[24,38,49]]])await contact(frames,path.join(root,`qa/c2_${group}_${bg}_4x.png`),4,color,6);
 }
 const manifest=await read('run-manifest.json'),generated=await read('qa/c2_imagegen_outputs.json');
 for(const item of generated){
  const entry={...item,scope:`C2 ${item.action} ${item.direction} local joints`,method:'imagegen_edit',cell:[64,96],
   source:`source/${item.action}_${item.direction}_joint_edit_raw_v011.png`,prompt:`prompts/${item.action}_${item.direction}_joint_edit_v011.txt`,
   actual_input:`source/action_edit_inputs_c2_rc01/${item.action}_${item.direction}.png`,usage:'MASKED_JOINT_EDIT_ON_FIXED_SOURCE_PARTS'};
  for(const[field,file]of [['sha256',entry.source],['input_sha256',entry.actual_input],['prompt_sha256',entry.prompt]])entry[field]=sha(await fs.readFile(path.join(root,file)));
  manifest.generation=manifest.generation.filter(g=>g.scope!==entry.scope).concat(entry);
 }
 manifest.status='PHASE_C2_RC01_AUTHORED_PENDING_QA';manifest.current_candidate_revision='phase-c2-rc01';manifest.current_review_metadata='full-action-metadata.json';
 manifest.current_revision_fix={revision:'phase-c2-rc01',scope:'remaining seven idle2/collect4 directions; new S neutral stance',accepted_frames_preserved:70,identity_masters_preserved:8,new_frames:42,art_acceptance:'PENDING_TA'};
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({clips:clips.length,frames:112,newFrames:42,preserved:accepted.length+mothers.length,animations:animations.length,atlas_sha256:meta.atlas_sha256}));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
