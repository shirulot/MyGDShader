// 结构检查不能替代视觉验收；记录两者边界，检查本次动作真正用了膝关节。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,base=path.resolve(root,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const {components}=require(path.join(base,'qa/audit_walk_components.cjs'));
const colors=new Set(['101820','182631','2b3e4b','4d6470','829ba3','becbc4','566b78','ece9d8','7b4d35','b77c4b','e2b77a']);
async function read(f){return JSON.parse(await fs.readFile(path.join(root,f),'utf8'));}
async function run(){const errors=[],records=[];let same=0,changed=0;
 const meta=await read('runtime/full-action-metadata.json');
 for(const clip of meta.clips){
  const poses=clip.action==='collect'?await read(`source/${clip.direction}/poses.json`):null;
  const neutral=clip.action==='collect'?await sharp(path.join(root,`source/${clip.direction}/baseline_f0.png`)).ensureAlpha().raw().toBuffer():null;
  for(const frame of clip.frames){
   const bytes=await fs.readFile(path.join(root,'runtime',frame.file));const {data,info}=await sharp(bytes).ensureAlpha().raw().toBuffer({resolveWithObject:true});
   if(info.width!==64||info.height!==96||sha(bytes)!==frame.sha256)errors.push('Size/hash '+frame.file);
   const prior=await fs.readFile(path.join(base,'revisions/collect-knee-v012/runtime',frame.file.replaceAll('v013','v012')));
   if(bytes.equals(prior))same++;else{changed++;if(clip.action!=='collect'||![1,2].includes(frame.frame))errors.push('Unexpected change '+frame.file);}
   for(let at=0;at<data.length;at+=4)if(![0,255].includes(data[at+3])||(data[at+3]&&!colors.has(data.subarray(at,at+3).toString('hex'))))errors.push('RGBA/palette '+frame.file);
   if(clip.action!=='collect')continue;
   if(components(data).length!==1)errors.push('Detached pixels '+frame.file);
   let soleDiff=0;for(let y=75;y<96;y++)for(let x=0;x<64;x++){const i=(y*64+x)*4;if(!data.subarray(i,i+4).equals(neutral.subarray(i,i+4)))soleDiff++;}
   if(soleDiff)errors.push('Planted foot bottom changed '+frame.file);
   const state=poses.frames[frame.frame].state,measurements=[];
   if([1,2].includes(frame.frame))for(const[id,j]of Object.entries(state.joints))if(id.startsWith('leg_')){
    const [l1,l2]=j.source_lengths,k=j.sagittal_joint;
    const u=[k[0]+.7,k[1]-2.4],v=[-k[0],l1+l2-k[1]];
    const flex=Math.acos(Math.max(-1,Math.min(1,(u[0]*v[0]+u[1]*v[1])/(l1*l2))))*180/Math.PI;
    if(k[0]<=0||flex<30||flex>90)errors.push('Wrong knee bend '+frame.file);
    if(Math.abs(Math.hypot(...u)-l1)>0.0001||Math.abs(Math.hypot(...v)-l2)>0.0001)errors.push('Bone length '+frame.file);
    measurements.push({limb:id,knee_flexion_degrees:flex,knee_forward_pixels:k[0],projected_knee:j.joint,fixed_ankle:j.ankle});
   }
   records.push({direction:clip.direction,frame:frame.frame,sole_difference_pixels:soleDiff,measurements});
  }
 }
 if(same!==96||changed!==16)errors.push('Change count');
 const report={status:errors.length?'FAIL':'PASS',preserved_frames:same,changed_frames:changed,collect_frames:records.length,checks:['canvas and hash','binary alpha and 11-color palette','one connected alpha component','planted sole rows unchanged','sagittal forward knee solution','constant sagittal bone lengths'],visual_acceptance:'PENDING_USER_REVIEW',godot_gpu_check:'NOT_RUN_AUTOMATIC_APPROVAL_REJECTED_PROCESS_LAUNCH',records,errors};
 await fs.writeFile(path.join(root,'qa/validation.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({status:report.status,same,changed,errors}));if(errors.length)process.exitCode=1;
}
run().catch(e=>{console.error(e);process.exitCode=1;});
