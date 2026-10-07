// 小样交付入口。八张 pose 只代表待审母版，不能计作最终双帧 idle。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const ROOT=__dirname,W=64,H=96,dirs=['down','down_left','left','up_left','up','up_right','right','down_right'];
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function run(){
 const files=[],clips=[],all=[];
 for(const[direction,row]of [['down',0],['down_left',1]]){
   const frames=[];
   for(let i=0;i<8;i++){
     const file=`frames/walk/${direction}/robot_walk_${direction}_f${String(i).padStart(2,'0')}_${direction==='down'?'v010':'v011'}.png`;
     const bytes=await fs.readFile(path.join(ROOT,file)),image=await sharp(bytes).ensureAlpha().raw().toBuffer();
     if(image.length!==W*H*4)throw Error('Frame size changed');
     const entry={file,sha256:sha(bytes),region:[i*W,row*H,W,H],frame:i};files.push(entry);frames.push(entry);all.push(image);
   }
   clips.push({name:`walk_${direction}`,action:'walk',direction,fps:8,loop:true,frames,art_status:direction==='down'?'V010_APPROVED_UNCHANGED':'CANDIDATE_PENDING_TA'});
 }
 for(let i=0;i<8;i++){
   const file=`source/candidate-masters/robot_idle_${dirs[i]}_v011.png`,bytes=await fs.readFile(path.join(ROOT,file)),image=await sharp(bytes).ensureAlpha().raw().toBuffer();
   const entry={file,sha256:sha(bytes),region:[i*W,H*2,W,H],frame:0};files.push(entry);all.push(image);
   clips.push({name:`pose_${dirs[i]}`,action:'pose',direction:dirs[i],fps:1,loop:false,frames:[entry],art_status:'STATIC_MASTER_CANDIDATE_NOT_FINAL_IDLE'});
 }
 const atlas=Buffer.alloc(W*8*H*3*4);
 all.forEach((frame,i)=>{for(let y=0;y<H;y++)frame.copy(atlas,((Math.floor(i/8)*H+y)*W*8+i%8*W)*4,y*W*4,(y+1)*W*4);});
 const atlasFile='robot_phase_a_atlas_v011.png';await sharp(atlas,{raw:{width:W*8,height:H*3,channels:4}}).png().toFile(path.join(ROOT,atlasFile));
 const metadata={revision:'v011-phase-a-rc01',status:'CANDIDATE_PENDING_TA',canvas:[W,H],root_anchor:[32,80],texture_scale:1,direction_order:dirs,atlas:atlasFile,atlas_sha256:sha(await fs.readFile(path.join(ROOT,atlasFile))),phase_scope:'eight static direction masters, frozen v010 down walk, and new down_left walk pilot',final_scope:{clips:24,frames:112,idle:[2,2,true],walk:[8,8,true],collect:[4,6,false]},clips,source_files:files};
 await fs.writeFile(path.join(ROOT,'phase-a-metadata.json'),JSON.stringify(metadata,null,2)+'\n');
 await fs.mkdir(path.join(ROOT,'godot-review/assets'),{recursive:true});await fs.copyFile(path.join(ROOT,atlasFile),path.join(ROOT,'godot-review/assets',atlasFile));
 let tres=`[gd_resource type="SpriteFrames" load_steps=${all.length+2} format=3]\n\n[ext_resource type="Texture2D" path="res://assets/${atlasFile}" id="1_atlas"]\n\n`;
 files.forEach((entry,i)=>{tres+=`[sub_resource type="AtlasTexture" id="Atlas_${i}"]\natlas = ExtResource("1_atlas")\nregion = Rect2(${entry.region.join(', ')})\n\n`;});
 let offset=0;tres+='[resource]\nanimations = [\n'+clips.map(clip=>{
   const frames=clip.frames.map(()=>`{ "duration": 1.0, "texture": SubResource("Atlas_${offset++}") }`).join(', ');
   return `{ "frames": [${frames}], "loop": ${clip.loop}, "name": &"${clip.name}", "speed": ${clip.fps}.0 }`;
 }).join(',\n')+'\n]\n';
 await fs.writeFile(path.join(ROOT,'godot-review/robot_phase_a_v011.tres'),tres);
 await fs.writeFile(path.join(ROOT,'godot-review/phase-a-metadata.json'),JSON.stringify(metadata,null,2)+'\n');
 for(const clip of clips.filter(c=>c.action==='walk')){
   const images=await Promise.all(clip.frames.map(f=>sharp(path.join(ROOT,f.file)).ensureAlpha().raw().toBuffer()));
   for(const delay of [125,500])for(const scale of [1,4]){
     const scaled=await Promise.all(images.map(image=>sharp(image,{raw:{width:W,height:H,channels:4}}).resize(W*scale,H*scale,{kernel:'nearest'}).raw().toBuffer()));
     const film=Buffer.concat(scaled),options={raw:{width:W*scale,height:H*8*scale,channels:4,pageHeight:H*scale}};
     const stem=`previews/${clip.name}_${delay===125?'normal':'slow'}_${scale}x_v011`;
     await sharp(film,options).webp({lossless:true,loop:0,delay:Array(8).fill(delay)}).toFile(path.join(ROOT,stem+'.webp'));
     await sharp(film,options).gif({loop:0,delay:delay===125?[130,120,130,120,130,120,130,120]:Array(8).fill(delay),dither:0,interFrameMaxError:0,interPaletteMaxError:0}).toFile(path.join(ROOT,stem+'.gif'));
     const check=await sharp(path.join(ROOT,stem+'.webp'),{animated:true}).metadata();if(check.pages!==8)throw Error('Animation export lost frames');
     const decoded=await sharp(path.join(ROOT,stem+'.webp'),{animated:true}).ensureAlpha().raw().toBuffer();
     if(!decoded.equals(film))throw Error('Animated WebP changed native source RGBA');
   }
 }
 const manifest=JSON.parse(await fs.readFile(path.join(ROOT,'run-manifest.json'),'utf8'));
 manifest.status='PHASE_A_SELF_REVIEW';manifest.phases[0].status='PILOT_RENDERED_PENDING_PLAYBACK_AND_TA';
 manifest.generation=manifest.generation.filter(g=>!g.scope.startsWith('down_left'));
 for(const[scope,file,prompt,use]of [
   ['down_left walk pose guide','walk_down_left_pose_guide_raw_v011.png','walk_down_left_pose_guide_v011.txt','REFERENCE_ONLY_NOT_ANIMATION_SOURCE'],
   ['down_left local joint repair','walk_down_left_joint_edit_raw_v011.png','walk_down_left_joint_edit_v011.txt','JOINT_LOCAL_PATCH_ON_FIXED_RIG']]){
   manifest.generation.push({scope,method:'imagegen_edit',source:'source/'+file,prompt:'prompts/'+prompt,sha256:sha(await fs.readFile(path.join(ROOT,'source',file))),usage:use});
 }
 manifest.current_review_metadata='phase-a-metadata.json';await fs.writeFile(path.join(ROOT,'run-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({scope:metadata.phase_scope,reviewClips:clips.length,walkFrames:16,poseCandidates:8,atlas_sha256:metadata.atlas_sha256}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
