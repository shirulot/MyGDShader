// 验证最终图集与动画导出，另核固定脚底、回位和旧文件。美术判断独立保留。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {components}=require('./qa/audit_walk_components.cjs');
const root=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const palette=new Set(['101820','182631','2b3e4b','4d6470','829ba3','becbc4','566b78','ece9d8','7b4d35','b77c4b','e2b77a']);
const read=async f=>JSON.parse(await fs.readFile(path.join(root,f),'utf8'));
(async()=>{
 const meta=await read('full-action-metadata.json'),errors=[],images=[],animated=[],invariants=[],raws=new Map();
 const atlasBytes=await fs.readFile(path.join(root,meta.atlas));if(sha(atlasBytes)!==meta.atlas_sha256)throw Error('Atlas hash mismatch');
 for(const clip of meta.clips)for(const frame of clip.frames){
  const bytes=await fs.readFile(path.join(root,frame.file)),reader=sharp(bytes),info=await reader.metadata(),raw=await reader.ensureAlpha().raw().toBuffer();raws.set(frame.file,raw);
  let invalidAlpha=0,invalidColor=0;for(let at=0;at<raw.length;at+=4){if(![0,255].includes(raw[at+3]))invalidAlpha++;if(raw[at+3]&&!palette.has(raw.subarray(at,at+3).toString('hex')))invalidColor++;}
  const[x,y,width,height]=frame.region,atlasRegion=await sharp(atlasBytes).extract({left:x,top:y,width,height}).ensureAlpha().raw().toBuffer();
  const check={file:frame.file,sha256:sha(bytes),size:[info.width,info.height],invalidAlpha,invalidColor,components:components(raw).length,atlas_rgba_exact:raw.equals(atlasRegion)};images.push(check);
  if(check.sha256!==frame.sha256||info.width!==64||info.height!==96||invalidAlpha||invalidColor||check.components!==1||!check.atlas_rgba_exact)errors.push(check);
 }
 for(const direction of meta.directions){
  const idle=meta.clips.find(c=>c.name==='idle_'+direction),collect=meta.clips.find(c=>c.name==='collect_'+direction);
  const idleRaw=idle.frames.map(f=>raws.get(f.file)),collectRaw=collect.frames.map(f=>raws.get(f.file));
  const source=direction==='down'?'source/action-candidate-masters/robot_neutral_down_v011.png':`source/candidate-masters/robot_idle_${direction}_v011.png`;
  const neutral=await sharp(path.join(root,source)).ensureAlpha().raw().toBuffer();
  const folder=direction==='down_left'?'action-rig-pilot':'action-rig-batch',ledger=await read(`source/${folder}/idle/${direction}/rig_and_poses.json`);
  const legs=Object.keys(ledger.states[0].transforms).filter(k=>k.startsWith('leg_'));
  const check={direction,idle0_matches_neutral:idleRaw[0].equals(neutral),collect3_matches_idle0:collectRaw[3].equals(idleRaw[0]),
   idle_leg_transforms_fixed:legs.every(k=>JSON.stringify(ledger.states[0].transforms[k])===JSON.stringify(ledger.states[1].transforms[k])),
   idle_sole_band_fixed:idleRaw.every(raw=>raw.subarray(77*64*4).equals(idleRaw[0].subarray(77*64*4))),
   collect_sole_band_fixed:collectRaw.every(raw=>raw.subarray(77*64*4).equals(idleRaw[0].subarray(77*64*4)))};
  invariants.push(check);if(Object.values(check).some(value=>value===false))errors.push(check);
  for(const action of['idle','collect']){
   const report=await read(`qa/${action}_${direction}_joint_patch_v011.json`);
   if(report.records.some(r=>r.protected_pixels_changed||r.outside_mask_changed))errors.push({direction,action,reason:'Patch crossed fixed geometry'});
  }
 }
 const accepted=[...(await read('source/walk-acceptance-v011.json')).clips,...(await read('source/action-acceptance-v011.json')).clips].flatMap(c=>c.frames);
 const mothers=(await read('source/reference-phase-b2-rc01-metadata.json')).clips.filter(c=>c.action==='pose').flatMap(c=>c.frames);
 for(const f of [...accepted,...mothers])if(sha(await fs.readFile(path.join(root,f.file)))!==f.sha256)errors.push({file:f.file,reason:'Accepted bytes changed'});
 for(const item of await read('qa/full_action_animated_exports.json')){
  const clip=meta.clips.find(c=>c.name===item.clip),expected=Buffer.concat(await Promise.all(clip.frames.map(f=>sharp(path.join(root,f.file)).resize(64*item.scale,96*item.scale,{kernel:'nearest'}).ensureAlpha().raw().toBuffer())));
  const reader=sharp(path.join(root,item.file),{animated:true}),info=await reader.metadata(),raw=await reader.ensureAlpha().raw().toBuffer();
  const check={file:item.file,frames:info.pages,delay:info.delay,loop_encoded:info.loop,rgba_exact:raw.equals(expected)};animated.push(check);
  if(!check.rgba_exact||info.pages!==clip.frames.length||JSON.stringify(info.delay)!==JSON.stringify(item.delay)||info.loop!==item.loop_encoded)errors.push(check);
 }
 for(const action of['idle','collect']){
  const clips=meta.clips.filter(c=>c.action===action),count=clips[0].frames.length,width=96*count,out=Buffer.alloc(width*96*8*4);
  for(const[row,clip]of clips.entries())for(const[column,f]of clip.frames.entries()){const raw=raws.get(f.file);for(let y=0;y<96;y++)raw.copy(out,((row*96+y)*width+column*96+16)*4,y*64*4,(y+1)*64*4);}
  await sharp(out,{raw:{width,height:96*8,channels:4}}).png().toFile(path.join(root,`qa/${action}_motion_diagnostic_full_padded96.png`));
 }
 const report={technical_checks:errors.length?'FAIL':'PASS',revision:meta.revision,atlas_sha256:meta.atlas_sha256,images,animated,invariants,preserved_approved_frames:accepted.length,preserved_identity_masters:mothers.length,errors,art_acceptance:'NEW_42_PENDING_TA'};
 await fs.writeFile(path.join(root,'qa/export_validation_full_actions.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.technical_checks,images:images.length,animations:animated.length,preserved:accepted.length+mothers.length,errors}));if(errors.length)process.exitCode=1;
})().catch(error=>{console.error(error);process.exitCode=1;});
