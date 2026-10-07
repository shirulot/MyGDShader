// 将候选采集帧装入独立运行工程，同时保留80张idle/walk和16张采集首尾原字节。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,base=path.resolve(root,'../..'),approved=path.join(base,'delivery/robot-v011'),runtime=path.join(root,'runtime');
const {contact}=require(path.join(base,'build_fixed_rig_v011.cjs'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=async f=>JSON.parse(await fs.readFile(f,'utf8'));
async function put(file,data){await fs.mkdir(path.dirname(path.join(runtime,file)),{recursive:true});await fs.writeFile(path.join(runtime,file),data);}
async function animation(rawFrames,file,scale,fps,format){
 const frames=await Promise.all(rawFrames.map(raw=>sharp(raw,{raw:{width:64,height:96,channels:4}}).resize(64*scale,96*scale,{kernel:'nearest'}).raw().toBuffer()));
 const quantum=format==='gif'?10:1,delay=frames.map((_,i)=>(Math.round((i+1)*1000/fps/quantum)-Math.round(i*1000/fps/quantum))*quantum);
 const p=sharp(Buffer.concat(frames),{raw:{width:64*scale,height:96*scale*frames.length,channels:4,pageHeight:96*scale}});
 if(format==='gif')p.gif({loop:1,delay,dither:0,interFrameMaxError:0,interPaletteMaxError:0});else p.webp({loop:1,delay,lossless:true});
 await fs.mkdir(path.dirname(file),{recursive:true});await p.toFile(file);
}
async function run(){
 try{await fs.access(runtime);throw Error('Candidate runtime already exists; do not overwrite a reviewed package');}catch(e){if(e.code!=='ENOENT')throw e;}
 const original=await read(path.join(approved,'full-action-metadata.json')),meta=structuredClone(original);
 const atlas=Buffer.alloc(512*2304*4),comparison=[],changes=[];let preserved=0;
 for(const clip of meta.clips){
  const rawFrames=[],before=[];
  for(const frame of clip.frames){
   const prior=await fs.readFile(path.join(approved,frame.file));let bytes=prior,oldFile=frame.file;
   if(clip.action==='collect'){
    frame.file=`frames/collect/${clip.direction}/robot_collect_${clip.direction}_f${String(frame.frame).padStart(2,'0')}_v012.png`;
    bytes=await fs.readFile(path.join(root,frame.file));before.push(await sharp(prior).ensureAlpha().raw().toBuffer());
   }
   if(bytes.equals(prior))preserved++;else changes.push({clip:clip.name,frame:frame.frame,source:oldFile,before_sha256:sha(prior),after_sha256:sha(bytes)});
   frame.sha256=sha(bytes);await put(frame.file,bytes);
   const raw=await sharp(bytes).ensureAlpha().raw().toBuffer();rawFrames.push(raw);
   for(let y=0;y<96;y++)raw.copy(atlas,((frame.region[1]+y)*512+frame.region[0])*4,y*64*4,(y+1)*64*4);
  }
  clip.art_status=clip.action==='collect'?'KNEE_REVISION_PENDING_REVIEW':'PASS_RETAINED';
  if(clip.action==='collect'){
   const d=clip.direction,poses=await read(path.join(root,'source',d,'poses.json'));
   const oldPoses=await read(path.join(base,`source/${d==='down_left'?'action-rig-pilot':'action-rig-batch'}/collect/${d}/rig_and_poses.json`));
   comparison.push({direction:d,before:clip.frames.map(f=>`source/${d}/baseline_f${f.frame}.png`),after:clip.frames.map(f=>f.file),old_joints:oldPoses.states.map(s=>s.joints),new_joints:poses.frames.map(f=>f.state.joints)});
   for(const scale of[1,4])for(const speed of['normal','slow'])for(const format of['gif','webp']){
    const suffix=`${clip.name}_${speed}_${scale}x_v012.${format}`;
    await animation(rawFrames,path.join(runtime,'previews/full',suffix),scale,6*(speed==='slow'?.25:1),format);
    await animation(before,path.join(root,'previews/before',suffix.replace('_v012','_v011')),scale,6*(speed==='slow'?.25:1),format);
   }
   // 膝甲与髋—膝—踝ROI，仅裁切/最近邻放大现有帧，供视觉检查而非生产素材。
   const roiFrames=await Promise.all(before.concat(rawFrames).map(raw=>sharp(raw,{raw:{width:64,height:96,channels:4}}).extract({left:12,top:53,width:42,height:28}).raw().toBuffer()));
   for(const [name,color]of[['light',[236,233,216,255]],['dark',[24,38,49,255]]]){
    const roi=Buffer.alloc(42*4*28*2*4);for(let i=0;i<roi.length;i+=4)roi.set(color,i);
    roiFrames.forEach((r,i)=>{for(let y=0;y<28;y++)for(let x=0;x<42;x++){const at=(y*42+x)*4;if(r[at+3])r.copy(roi,((Math.floor(i/4)*28+y)*168+(i%4)*42+x)*4,at,at+4);}});
    await sharp(roi,{raw:{width:168,height:56,channels:4}}).resize(1008,336,{kernel:'nearest'}).png().toFile(path.join(root,'qa',`${d}_hip_knee_ankle_${name}_6x.png`));
   }
  }
 }
 if(preserved!==96||changes.length!==16||changes.some(c=>!c.clip.startsWith('collect_')||![1,2].includes(c.frame)))throw Error('Unexpected asset change scope');
 const atlasName='robot_eight_way_actions_atlas_v012.png',asset='assets/ember/robot_v012';
 const atlasBytes=await sharp(atlas,{raw:{width:512,height:2304,channels:4}}).png().toBuffer();await put(asset+'/'+atlasName,atlasBytes);
 meta.revision='v012-collect-knee-rc01';meta.release='robot-v012-candidate';meta.status='COLLECT_KNEE_REVISION_PENDING_VISUAL_REVIEW';
 meta.atlas=asset+'/'+atlasName;meta.atlas_sha256=sha(atlasBytes);meta.art_acceptance={status:'COLLECT_REOPENED_BY_USER',preserved_frames:96,changed_frames:16};
 for(const field of['accepted_frames_preserved','new_frames','identity_masters_preserved'])delete meta[field];
 meta.unchanged_frames=96;meta.changed_frames=16;
 await put('full-action-metadata.json',JSON.stringify(meta,null,2)+'\n');
 for(const file of['project.godot','preview/preview_full_actions.gd','preview/preview_full_actions.tscn','verify_import.gd']){
  await put(file,(await fs.readFile(path.join(approved,file),'utf8')).replaceAll('robot_v011','robot_v012').replaceAll('v011','v012'));
 }
 let tres=await fs.readFile(path.join(approved,'assets/ember/robot_v011/robot_eight_way_v011.tres'),'utf8');
 await put(asset+'/robot_eight_way_v012.tres',tres.replaceAll('robot_v011','robot_v012').replaceAll('v011','v012'));
 let importer=await fs.readFile(path.join(approved,'assets/ember/robot_v011/robot_eight_way_actions_atlas_v011.png.import'),'utf8');
 await put(asset+'/'+atlasName+'.import',importer.replaceAll('robot_v011','robot_v012').replaceAll('v011','v012').replace(/^uid=.*\r?\n/m,''));
 for(const folder of['frames','previews','evidence'])await put(folder+'/.gdignore','');
 const animations=await read(path.join(base,'qa/full_action_animated_exports.json'));
 for(const item of animations.filter(a=>!a.clip.startsWith('collect_')))await put(item.file,await fs.readFile(path.join(approved,item.file)));
 let html=await fs.readFile(path.join(approved,'preview.html'),'utf8');
 html=html.replace('八向待机、行走和采集已通过逐批独立审查。','采集膝盖修订候选，等待新的视觉审查；待机与行走保持原帧。').replace("clip.art_status==='PASS'?'已通过独立审查':'待审'","clip.art_status==='PASS_RETAINED'?'保留原帧':'膝盖修订待审'").replace("_4x_v011.webp`;draw();","_4x_${clip.action==='collect'?'v012':'v011'}.webp`;draw();");
 await put('preview.html',html);
 await fs.writeFile(path.join(root,'comparison-metadata.json'),JSON.stringify(comparison,null,2)+'\n');
 const generation=await read(path.join(root,'source/imagegen-ledger.json'));
 for(const entry of generation)for(const [key,file]of[['source_sha256',entry.source],['input_sha256',entry.actual_input],['prompt_sha256',entry.prompt]])entry[key]=sha(await fs.readFile(path.join(root,file)));
 await fs.writeFile(path.join(root,'source/imagegen-ledger.json'),JSON.stringify(generation,null,2)+'\n');
 const manifest={revision:'v012-collect-knee-rc01',status:'CANDIDATE_PENDING_VISUAL_REVIEW',canvas:[64,96],root_anchor:[32,80],scope:'Only eight-direction collect F01/F02; stable support and existing upper-body reach',preserved_frames:96,changed_frames:16,changes,generation,rejected_generation:[{file:'source/down_right/imagegen_waist_edit_input_v1_superseded.png',reason:'Superseded after source assembly residue correction; not used in final candidate'}],baseline_zip_sha256:'8dc65a715b41b2c61a09eb6e2afbcd31134db60228f4b3081a0a39e4d153f4bb',main_project_modified:false};
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 await fs.writeFile(path.join(root,'qa/change-scope.json'),JSON.stringify({technical_checks:'PASS',preserved_frames:preserved,changed_frames:changes.length,changes},null,2)+'\n');
 console.log(JSON.stringify({preserved,changed:changes.length,clips:24,frames:112,atlas_sha256:meta.atlas_sha256}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
