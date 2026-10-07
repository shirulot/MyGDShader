// 有实际意义的资产验收：原通过帧保真、固定画布、alpha/色板和动图逐像素无损。
// 连通域只作为定位数据，绝不据此声称关节在视觉上通过。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const palette=new Set(['101820','182631','2b3e4b','4d6470','829ba3','becbc4','566b78','ece9d8','7b4d35','b77c4b','e2b77a']);
function components(b){
 const seen=new Set(),sizes=[];
 for(let start=0;start<64*96;start++){
  if(!b[start*4+3]||seen.has(start))continue;
  const q=[start];seen.add(start);
  for(let i=0;i<q.length;i++){
   const x=q[i]%64,y=Math.floor(q[i]/64);
   for(const dx of [-1,0,1])for(const dy of [-1,0,1]){
    const xx=x+dx,yy=y+dy,id=yy*64+xx;
    if(xx<0||xx>=64||yy<0||yy>=96||seen.has(id)||!b[id*4+3])continue;
    seen.add(id);q.push(id);
   }
  }sizes.push(q.length);
 }return sizes.sort((a,b)=>b-a);
}
async function run(){
 const meta=JSON.parse(await fs.readFile(path.join(root,'phase-a-metadata.json'),'utf8')),checks=[],animationChecks=[],errors=[];
 for(const f of meta.source_files){
  const bytes=await fs.readFile(path.join(root,f.file)),image=sharp(bytes),m=await image.metadata(),raw=await image.ensureAlpha().raw().toBuffer();
  let invalidAlpha=0,invalidColor=0;
  for(let at=0;at<raw.length;at+=4){if(![0,255].includes(raw[at+3]))invalidAlpha++;if(raw[at+3]&&!palette.has(raw.subarray(at,at+3).toString('hex')))invalidColor++;}
  let frozen=null;if(f.file.startsWith('frames/walk/down/'))frozen=bytes.equals(await fs.readFile(path.join(root,'../robot-joint-repair-v010/frames',path.basename(f.file))));
  const check={file:f.file,sha256:sha(bytes),size:[m.width,m.height],invalidAlpha,invalidColor,frozen_v010_exact:frozen,alpha_components_8:components(raw)};
  if(check.sha256!==f.sha256||m.width!==64||m.height!==96||invalidAlpha||invalidColor||frozen===false)errors.push(check);
  checks.push(check);
 }
 for(const clip of meta.clips.filter(c=>c.action==='walk'))for(const scale of [1,4])for(const speed of ['normal','slow']){
  const frames=await Promise.all(clip.frames.map(f=>sharp(path.join(root,f.file)).ensureAlpha().resize(64*scale,96*scale,{kernel:'nearest'}).raw().toBuffer()));
  const expected=Buffer.concat(frames);
  for(const ext of ['gif','webp']){
   const file=`previews/${clip.name}_${speed}_${scale}x_v011.${ext}`,reader=sharp(path.join(root,file),{animated:true}),m=await reader.metadata(),decoded=await reader.ensureAlpha().raw().toBuffer();
   const exact=decoded.equals(expected),duration=m.delay.reduce((a,b)=>a+b,0);
   const check={file,frames:m.pages,duration_ms:duration,rgba_exact:exact};animationChecks.push(check);
   if(!exact||m.pages!==8||duration!==(speed==='normal'?1000:4000))errors.push(check);
  }
 }
 const patch=JSON.parse(await fs.readFile(path.join(root,'qa/down_left_joint_patch_v011.json'),'utf8'));
 if(patch.records.some(r=>r.protected_pixels_changed||r.outside_mask_changed))errors.push('Local patch altered a protected region');
 if(patch.records.some(r=>r.rigid_armor_pixels_changed_from_fixed_rig||r.non_armor_pixels_changed_from_rc01))errors.push('TA P2 correction did not preserve fixed armor or changed unrelated pixels');
 const report={technical_checks:errors.length?'FAIL':'PASS',art_acceptance:'PENDING_INDEPENDENT_REVIEW',errors,frames:checks,animations:animationChecks,local_patch_protection:'body, hand/tool and rigid boot including transparent contour margin'};
 await fs.writeFile(path.join(root,'qa/export_validation_phase_a.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.technical_checks,frames:checks.length,animatedExports:animationChecks.length,errors}));if(errors.length)process.exitCode=1;
}
run().catch(e=>{console.error(e);process.exitCode=1;});
