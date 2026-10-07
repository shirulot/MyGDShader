// C1独立小样导出：SW idle2、collect4，附已通过walk8及身份参考用于动作切换。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function run(){
 const clips=[],sourceFiles=[],atlas=Buffer.alloc(512*384*4);
 const specs=[['idle',2,2,true],['collect',4,6,false],['walk',8,8,true],['pose',1,1,false]];
 for(const[row,[action,count,fps,loop]]of specs.entries()){
  const frames=[];
  for(let i=0;i<count;i++){
   const file=action==='pose'?'source/candidate-masters/robot_idle_down_left_v011.png':`frames/${action}/down_left/robot_${action}_down_left_f${String(i).padStart(2,'0')}_v011.png`;
   const bytes=await fs.readFile(path.join(root,file)),raw=await sharp(bytes).ensureAlpha().raw().toBuffer();
   for(let y=0;y<96;y++)raw.copy(atlas,((row*96+y)*512+i*64)*4,y*64*4,(y+1)*64*4);
   const f={file,frame:i,sha256:sha(bytes),region:[i*64,row*96,64,96]};frames.push(f);sourceFiles.push(f);
  }
  clips.push({name:action+'_down_left',direction:'down_left',action,fps,loop,frames,art_status:action==='walk'?'PHASE_A_PASS_RETAINED':action==='pose'?'IDENTITY_REFERENCE_ONLY':'NEW_ACTION_PILOT_PENDING_TA'});
 }
 const atlasName='robot_action_pilot_atlas_v011.png';await sharp(atlas,{raw:{width:512,height:384,channels:4}}).png().toFile(path.join(root,atlasName));
 const meta={revision:'v011-phase-c1-rc01',status:'ACTION_PILOT_PENDING_TA',canvas:[64,96],root_anchor:[32,80],direction:'down_left',atlas:atlasName,atlas_sha256:sha(await fs.readFile(path.join(root,atlasName))),clips,source_files:sourceFiles,scope:'SW idle2 and collect4 pilot, plus approved walk8 and one identity reference',final_scope:{clips:24,frames:112}};
 await fs.writeFile(path.join(root,'action-pilot-metadata.json'),JSON.stringify(meta,null,2)+'\n');
 const project=path.join(root,'godot-action-review');await fs.mkdir(path.join(project,'assets'),{recursive:true});
 await fs.copyFile(path.join(root,atlasName),path.join(project,'assets',atlasName));await fs.writeFile(path.join(project,'action-pilot-metadata.json'),JSON.stringify(meta,null,2)+'\n');
 let tres=`[gd_resource type="SpriteFrames" load_steps=${sourceFiles.length+2} format=3]\n\n[ext_resource type="Texture2D" path="res://assets/${atlasName}" id="1_atlas"]\n\n`;
 sourceFiles.forEach((f,i)=>tres+=`[sub_resource type="AtlasTexture" id="Atlas_${i}"]\natlas = ExtResource("1_atlas")\nregion = Rect2(${f.region.join(', ')})\n\n`);
 let index=0;tres+='[resource]\nanimations = [\n'+clips.map(c=>`{ "frames": [${c.frames.map(()=>`{ "duration": 1.0, "texture": SubResource("Atlas_${index++}") }`).join(', ')}], "loop": ${c.loop}, "name": &"${c.name}", "speed": ${c.fps}.0 }`).join(',\n')+'\n]\n';
 await fs.writeFile(path.join(project,'robot_action_pilot_v011.tres'),tres);
 const exports=[];
 for(const clip of clips.filter(c=>['idle','collect'].includes(c.action)))for(const scale of[1,4])for(const speed of['normal','slow']){
  const fps=clip.fps*(speed==='slow'?.25:1),count=clip.frames.length;
  const frames=await Promise.all(clip.frames.map(f=>sharp(path.join(root,f.file)).resize(64*scale,96*scale,{kernel:'nearest'}).ensureAlpha().raw().toBuffer()));
  const options={raw:{width:64*scale,height:96*count*scale,channels:4,pageHeight:96*scale}},raw=Buffer.concat(frames);
  for(const ext of['webp','gif']){
   // GIF只能以10ms为单位，累计舍入保留整段时长；WebP按1ms累计舍入。
   const quantum=ext==='gif'?10:1,delay=Array.from({length:count},(_,i)=>(Math.round((i+1)*1000/fps/quantum)-Math.round(i*1000/fps/quantum))*quantum);
   const file=`previews/${clip.name}_${speed}_${scale}x_v011.${ext}`,pipeline=sharp(raw,options);
   if(ext==='webp')pipeline.webp({lossless:true,loop:clip.loop?0:1,delay});else pipeline.gif({loop:clip.loop?0:1,delay,dither:0,interFrameMaxError:0,interPaletteMaxError:0});
   await pipeline.toFile(path.join(root,file));exports.push({file,clip:clip.name,scale,speed,delay,loop_encoded:clip.loop?0:1});
  }
 }
 await fs.writeFile(path.join(root,'qa/action_pilot_animated_exports.json'),JSON.stringify(exports,null,2)+'\n');
 // 复用已经生成的导入设置，关闭alpha边缘扩色；新工程将自己创建缓存。
 let importer=await fs.readFile(path.join(root,'godot-walk-review/assets/robot_walk_batch_atlas_v011.png.import'),'utf8');
 importer=importer.replaceAll('robot_walk_batch_atlas_v011.png',atlasName);await fs.writeFile(path.join(project,'assets',atlasName+'.import'),importer);
 console.log(JSON.stringify({clips:clips.length,sourceImages:sourceFiles.length,newActionFrames:6,animatedExports:exports.length,atlas_sha256:meta.atlas_sha256}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
