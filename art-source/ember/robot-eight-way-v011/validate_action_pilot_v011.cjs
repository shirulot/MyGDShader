// 核对真实输出与回位约定。连通/像素守恒不替代动作美术复审。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {components}=require('./qa/audit_walk_components.cjs');
const root=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const palette=new Set(['101820','182631','2b3e4b','4d6470','829ba3','becbc4','566b78','ece9d8','7b4d35','b77c4b','e2b77a']);
(async()=>{
 const meta=JSON.parse(await fs.readFile(path.join(root,'action-pilot-metadata.json'),'utf8')),errors=[],images=[],animated=[];
 const rawByFile=new Map(),accepted=JSON.parse(await fs.readFile(path.join(root,'source/walk-acceptance-v011.json'),'utf8'));
 for(const f of meta.source_files){
  const bytes=await fs.readFile(path.join(root,f.file)),reader=sharp(bytes),info=await reader.metadata(),raw=await reader.ensureAlpha().raw().toBuffer();rawByFile.set(f.file,raw);
  let invalidAlpha=0,invalidColor=0;for(let at=0;at<raw.length;at+=4){if(![0,255].includes(raw[at+3]))invalidAlpha++;if(raw[at+3]&&!palette.has(raw.subarray(at,at+3).toString('hex')))invalidColor++;}
  const check={file:f.file,sha256:sha(bytes),size:[info.width,info.height],invalidAlpha,invalidColor,components:components(raw).length};images.push(check);
  if(check.sha256!==f.sha256||info.width!==64||info.height!==96||invalidAlpha||invalidColor||check.components!==1)errors.push(check);
 }
 const idle=meta.clips.find(c=>c.action==='idle'),collect=meta.clips.find(c=>c.action==='collect'),pose=meta.clips.find(c=>c.action==='pose'),walk=meta.clips.find(c=>c.action==='walk');
 const raws=c=>c.frames.map(f=>rawByFile.get(f.file)),idleRaw=raws(idle),collectRaw=raws(collect);
 const invariant={idle0_equals_identity:idleRaw[0].equals(raws(pose)[0]),collect_recovery_equals_idle0:collectRaw[3].equals(idleRaw[0]),idle_lower_body_y64_95_exact:idleRaw[0].subarray(64*64*4).equals(idleRaw[1].subarray(64*64*4)),collect_boot_sole_band_y77_95_exact:collectRaw.every(r=>r.subarray(77*64*4).equals(idleRaw[0].subarray(77*64*4)))};
 for(const[key,value]of Object.entries(invariant))if(!value)errors.push({invariant:key});
 const approved=accepted.clips.find(c=>c.direction==='down_left');for(const f of walk.frames)if(f.sha256!==approved.frames[f.frame].sha256)errors.push({file:f.file,reason:'approved walk changed'});
 const exports=JSON.parse(await fs.readFile(path.join(root,'qa/action_pilot_animated_exports.json'),'utf8'));
 for(const item of exports){
  const clip=meta.clips.find(c=>c.name===item.clip),expected=Buffer.concat(await Promise.all(clip.frames.map(f=>sharp(path.join(root,f.file)).resize(64*item.scale,96*item.scale,{kernel:'nearest'}).ensureAlpha().raw().toBuffer())));
  const reader=sharp(path.join(root,item.file),{animated:true}),info=await reader.metadata(),raw=await reader.ensureAlpha().raw().toBuffer();
  const check={file:item.file,frames:info.pages,delay:info.delay,loop_encoded:info.loop,rgba_exact:raw.equals(expected)};animated.push(check);
  if(!check.rgba_exact||info.pages!==clip.frames.length||JSON.stringify(info.delay)!==JSON.stringify(item.delay)||info.loop!==item.loop_encoded)errors.push(check);
 }
 const report={technical_checks:errors.length?'FAIL':'PASS',revision:meta.revision,atlas_sha256:meta.atlas_sha256,art_acceptance:'PENDING_TA',invariants:invariant,images,animated,errors};
 await fs.writeFile(path.join(root,'qa/export_validation_action_pilot.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.technical_checks,images:images.length,animations:animated.length,invariant,errors}));if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
