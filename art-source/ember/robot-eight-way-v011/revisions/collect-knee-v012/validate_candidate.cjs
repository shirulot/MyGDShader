// 技术核对不代替姿态美术验收；输出明确保留候选状态。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,base=path.resolve(root,'../..'),approved=path.join(base,'delivery/robot-v011');
const {components}=require(path.join(base,'qa/audit_walk_components.cjs'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const colors=new Set(['101820','182631','2b3e4b','4d6470','829ba3','becbc4','566b78','ece9d8','7b4d35','b77c4b','e2b77a']);
async function run(){
 const meta=await read(path.join(root,'runtime/full-action-metadata.json')),baseline=await read(path.join(approved,'full-action-metadata.json'));
 let unchanged=0,changed=0;const records=[],sources=[];
 for(const clip of meta.clips){
  const old=baseline.clips.find(c=>c.name===clip.name);
  for(const frame of clip.frames){
   const bytes=await fs.readFile(path.join(root,'runtime',frame.file)),prior=await fs.readFile(path.join(approved,old.frames[frame.frame].file));
   const {data:raw,info}=await sharp(bytes).ensureAlpha().raw().toBuffer({resolveWithObject:true});
   if(info.width!==64||info.height!==96||sha(bytes)!==frame.sha256||components(raw).length!==1)throw Error('Frame geometry/hash: '+frame.file);
   for(let at=0;at<raw.length;at+=4){if(![0,255].includes(raw[at+3]))throw Error('Partial alpha');if(raw[at+3]&&!colors.has(raw.subarray(at,at+3).toString('hex')))throw Error('Palette drift');}
   if(bytes.equals(prior))unchanged++;else{
    changed++;if(clip.action!=='collect'||![1,2].includes(frame.frame))throw Error('Unexpected edited frame');
    const oldRaw=await sharp(prior).ensureAlpha().raw().toBuffer();
    if(!raw.subarray(0,53*64*4).equals(oldRaw.subarray(0,53*64*4)))throw Error('Upper-body motion was altered');
   }
   if(clip.action==='collect'){
    const neutral=await sharp(path.join(root,'source',clip.direction,'baseline_f3.png')).ensureAlpha().raw().toBuffer();
    if(!raw.subarray(70*64*4).equals(neutral.subarray(70*64*4)))throw Error('Boot/support drift: '+frame.file);
   }
   records.push({file:frame.file,sha256:sha(bytes),same_as_v011:bytes.equals(prior)});
  }
  if(clip.action==='collect'){
   const d=clip.direction,kind=d==='down_left'?'action-rig-pilot':'action-rig-batch';
   const ledgerFile=`source/${kind}/collect/${d}/rig_and_poses.json`,ledger=await read(path.join(base,ledgerFile));
   const copyFolder=path.join(root,'source/fixed-source-record',d);await fs.mkdir(copyFolder,{recursive:true});
   const ledgerBytes=await fs.readFile(path.join(base,ledgerFile));await fs.writeFile(path.join(copyFolder,'original_rig_and_poses.json'),ledgerBytes);
   for(const part of ledger.parts){const bytes=await fs.readFile(path.join(base,part.file)),copy=`source/fixed-source-record/${d}/${part.id}.png`;await fs.writeFile(path.join(root,copy),bytes);sources.push({original:part.file,copy,sha256:sha(bytes)});}
   const candidate=await read(path.join(root,'source',d,'poses.json'));
   for(const frame of candidate.frames)for(const [id,limb]of Object.entries(ledger.rig.limbs).filter(([,l])=>l.kind==='leg')){
    const joint=frame.state.joints[id];
    for(const [key,expected]of[['root',limb.root],['joint',limb.joint],['ankle',limb.end]])if(JSON.stringify(joint[key])!==JSON.stringify(expected))throw Error('Support joint moved: '+d);
   }
  }
 }
 if(unchanged!==96||changed!==16)throw Error('Changed-frame boundary failed');
 const generation=await read(path.join(root,'source/imagegen-ledger.json'));
 for(const entry of generation)for(const [hash,file]of[['source_sha256',entry.source],['input_sha256',entry.actual_input],['prompt_sha256',entry.prompt]])if(sha(await fs.readFile(path.join(root,file)))!==entry[hash])throw Error('Generation provenance changed');
 let animationCount=0;
 for(const clip of meta.clips.filter(c=>c.action==='collect'))for(const scale of[1,4])for(const speed of['normal','slow'])for(const format of['gif','webp']){
  const file=path.join(root,`runtime/previews/full/${clip.name}_${speed}_${scale}x_v012.${format}`),m=await sharp(file,{animated:true}).metadata();
  const expected=4000/(6*(speed==='slow'?.25:1));
  if(m.width!==64*scale||m.pageHeight!==96*scale||m.loop!==1||Math.abs(m.delay.reduce((a,b)=>a+b,0)-expected)>10)throw Error('Animation timing/size: '+file);
  animationCount++;
 }
 const gpu=await read(path.join(root,'runtime/evidence/collect-gpu-validation.json')),engine=await read(path.join(root,'runtime/evidence/engine-process-receipt.json'));
 if(gpu.technical_checks!=='PASS'||gpu.samples.length!==64||gpu.recoveries.length!==8||Object.values(engine).some(v=>v!==0))throw Error('Actual engine verification failed');
 const catalog=await read(path.join(approved,'sha256-manifest.json'));
 for(const item of catalog.files)if(sha(await fs.readFile(path.join(approved,item.file)))!==item.sha256)throw Error('Frozen original changed');
 await fs.writeFile(path.join(root,'source/fixed-source-mapping.json'),JSON.stringify(sources,null,2)+'\n');
 const report={technical_checks:'PASS',art_acceptance:'PENDING_NEW_VISUAL_REVIEW',checked_frames:112,unchanged_frames:unchanged,changed_frames:changed,checked_revised_animations:animationCount,gpu_samples:64,collect_recoveries:8,frozen_v011_payloads_unchanged:catalog.files.length,stable_support:'Original registered hip/knee/ankle positions, boot pixels y>=70 fixed across all collect frames',records};
 await fs.writeFile(path.join(root,'qa/validation.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({...report,records:undefined}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
