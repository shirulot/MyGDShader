// 检查真实导出资产：色板/alpha、已批准文件哈希、动画解码、固定源片保护边界。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {components}=require('./qa/audit_walk_components.cjs');
const root=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const palette=new Set(['101820','182631','2b3e4b','4d6470','829ba3','becbc4','566b78','ece9d8','7b4d35','b77c4b','e2b77a']);
async function run(){
 const meta=JSON.parse(await fs.readFile(path.join(root,'walk-batch-metadata.json'),'utf8'));
 const baseline=JSON.parse(await fs.readFile(path.join(root,meta.approved_baseline),'utf8'));
 const baselineFiles=new Map(baseline.source_files.map(f=>[f.file,f.sha256]));
 const errors=[],frames=[],animations=[],motion=[],patches=[];
 const previousBaseline=meta.previous_batch_baseline?JSON.parse(await fs.readFile(path.join(root,meta.previous_batch_baseline),'utf8')):null;
 if(previousBaseline)for(const f of previousBaseline.source_files)if(sha(await fs.readFile(path.join(root,f.file)))!==f.sha256)errors.push({file:f.file,reason:'previous frozen batch changed'});
 let phaseRevision=null;
 if(meta.revision==='v011-phase-b1-rc02'){
  phaseRevision=JSON.parse(await fs.readFile(path.join(root,'qa/arm_phase_revision_evidence.json'),'utf8'));
  for(const f of phaseRevision.unchanged_files)if(sha(await fs.readFile(path.join(root,f.file)))!==f.sha256)errors.push({file:f.file,reason:'rc01 preserved baseline changed'});
  for(const d of phaseRevision.directions){
   if(d.contacts.some(c=>!c.after.opposed))errors.push({direction:d.direction,reason:'same-side contact phase is not opposed'});
   for(const f of d.frames)if(sha(await fs.readFile(path.join(root,f.after_file)))!==f.after_sha256||f.outside_revision_mask_changed||!f.body_leg_transforms_unchanged)errors.push({direction:d.direction,frame:f.frame,reason:'revision evidence stale or exceeds agreed scope'});
  }
 }
 for(const f of meta.source_files){
  const bytes=await fs.readFile(path.join(root,f.file)),reader=sharp(bytes),info=await reader.metadata(),raw=await reader.ensureAlpha().raw().toBuffer();
  let invalidAlpha=0,invalidColor=0;for(let at=0;at<raw.length;at+=4){if(![0,255].includes(raw[at+3]))invalidAlpha++;if(raw[at+3]&&!palette.has(raw.subarray(at,at+3).toString('hex')))invalidColor++;}
  const c=components(raw),hash=sha(bytes),approved=baselineFiles.get(f.file),check={file:f.file,sha256:hash,size:[info.width,info.height],invalidAlpha,invalidColor,approved_baseline_exact:approved?hash===approved:null,alpha_components_8:c.map(({indices,...rest})=>rest)};
  frames.push(check);if(hash!==f.sha256||info.width!==64||info.height!==96||invalidAlpha||invalidColor||check.approved_baseline_exact===false)errors.push(check);
  if(c.length!==1)errors.push({file:f.file,reason:'unexplained separated pixels; inspect visually',components:check.alpha_components_8});
 }
 for(const clip of meta.clips.filter(c=>c.action==='walk')){
  const raw=await Promise.all(clip.frames.map(f=>sharp(path.join(root,f.file)).ensureAlpha().raw().toBuffer()));
  const changes=raw.map((frame,i)=>{const next=raw[(i+1)%8];let n=0;for(let p=0;p<frame.length;p+=4)if(!frame.subarray(p,p+4).equals(next.subarray(p,p+4)))n++;return n;});
  motion.push({clip:clip.name,distinct_frame_images:new Set(raw.map(sha)).size,adjacent_rgba_changes_including_loop:changes,interpretation:'diagnostic only; not a motion or joint art pass'});
  if(changes.some(n=>n===0))errors.push({clip:clip.name,reason:'duplicate consecutive walk frames'});
  for(const scale of[1,4])for(const speed of['normal','slow']){
   const expected=Buffer.concat(await Promise.all(clip.frames.map(f=>sharp(path.join(root,f.file)).resize(64*scale,96*scale,{kernel:'nearest'}).ensureAlpha().raw().toBuffer())));
   for(const ext of['gif','webp']){
    const file=`previews/${clip.name}_${speed}_${scale}x_v011.${ext}`,reader=sharp(path.join(root,file),{animated:true}),m=await reader.metadata(),decoded=await reader.ensureAlpha().raw().toBuffer();
    const check={file,frames:m.pages,duration_ms:m.delay.reduce((a,b)=>a+b,0),rgba_exact:decoded.equals(expected)};animations.push(check);
    if(!check.rgba_exact||check.frames!==8||check.duration_ms!==(speed==='normal'?1000:4000))errors.push(check);
   }
  }
  if(!['down','down_left'].includes(clip.direction)){
   const patch=JSON.parse(await fs.readFile(path.join(root,`qa/${clip.direction}_joint_patch_v011.json`),'utf8'));
   const rig=JSON.parse(await fs.readFile(path.join(root,`source/fixed-rig-pilot/${clip.direction}/rig_and_poses.json`),'utf8'));
   if(patch.records.some(r=>r.protected_pixels_changed||r.outside_mask_changed)||rig.neutral_reassembly_pixel_mismatch||rig.body_pixels_below_y64.length||rig.states.some(s=>s.notes.length))errors.push({direction:clip.direction,reason:'rig or protection report has unresolved errors'});
   patches.push({direction:clip.direction,source:patch.source_file,source_sha256:patch.source_sha256,fixed_plate_changes:0,mask_outside_changes:0,neutral_reassembly_difference:0});
  }
 }
 const report={technical_checks:errors.length?'FAIL':'PASS',art_acceptance:'PENDING_INDEPENDENT_TA',revision:meta.revision,atlas_sha256:meta.atlas_sha256,previous_batch_preserved_files:previousBaseline?.source_files.length??null,phase_revision_scope:phaseRevision?{unchanged_files:phaseRevision.unchanged_files.length,revised_frames:phaseRevision.directions.reduce((n,d)=>n+d.frames.length,0),evidence_sha256:sha(await fs.readFile(path.join(root,'qa/arm_phase_revision_evidence.json')))}:null,errors,frames,animations,motion,patches};
 await fs.writeFile(path.join(root,'qa/export_validation_walk_batch.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.technical_checks,images:frames.length,animatedExports:animations.length,motion,errors}));if(errors.length)process.exitCode=1;
}
run().catch(e=>{console.error(e);process.exitCode=1;});
