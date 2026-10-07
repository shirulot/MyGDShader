// 动作小样只采纳AI源中允许编辑的接缝；身份基帧与采集回位帧保持原像素。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {renderAction}=require('./build_action_pilot_v011.cjs');
const {protectRange}=require('./composite_remaining_joints_v011.cjs');
const {png,contact}=require('./build_fixed_rig_v011.cjs');
const {components}=require('./qa/audit_walk_components.cjs');
const root=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const palette=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A'].map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
const nearest=p=>palette.reduce((best,c)=>{const d=c.reduce((s,v,i)=>s+(v-p[i])**2,0);return d<best.d?{d,c}:best;},{d:Infinity,c:palette[0]}).c;

async function processAction(action,direction='down_left'){
 if(direction!=='down_left'||!['idle','collect'].includes(action))throw Error('Unauthored pilot action or direction');
 const pilot=`source/action-rig-pilot/${action}/${direction}`,ledger=JSON.parse(await fs.readFile(path.join(root,pilot,'rig_and_poses.json'),'utf8'));
 const parts={},guards={},rules=[];
 for(const p of ledger.parts)parts[p.id]=await sharp(path.join(root,p.file)).ensureAlpha().raw().toBuffer();
 for(const[id,part]of Object.entries(parts)){
  if(['body','pelvis'].includes(id)){guards[id]=Buffer.from(part);rules.push({part:id,rule:'all opaque fixed body/pelvis source pixels'});continue;}
  const l=ledger.rig.limbs[id.replace(/_(upper|lower|end)$/,'')];let range;
  if(id.endsWith('_end'))range=[0,H-1];
  else if(l.kind==='leg')range=id.endsWith('_upper')?[0,Math.floor(l.joint[1]-2.5)]:[Math.ceil(l.joint[1]+2),Math.floor(l.end[1]-2)];
  else range=id.endsWith('_upper')?[0,Math.floor(l.joint[1]-1.5)]:[Math.ceil(l.joint[1]+2),H-1];
  guards[id]=protectRange(part,...range).mask;rules.push({part:id,source_y:range,rule:'rigid shell, endpoints and transparent contour'});
 }
 const sourceFile=`source/${action}_${direction}_joint_edit_raw_v011.png`,bytes=await fs.readFile(path.join(root,sourceFile)),info=await sharp(bytes).metadata(),rows=action==='idle'?1:2;
 if(Math.abs(info.width/info.height-(128/(96*rows)))>.001)throw Error('Wrong action edit grid');
 const patch=await sharp(bytes).resize(128,96*rows,{kernel:'nearest'}).ensureAlpha().raw().toBuffer();
 for(let at=0;at<patch.length;at+=4)if(patch[at+3]<160)patch.fill(0,at,at+4);else patch.set([...nearest(patch.subarray(at,at+3)),255],at);
 const frames=[],records=[];
 for(const[stateIndex,state]of ledger.states.entries()){
  const name=`robot_${action}_${direction}_f${String(stateIndex).padStart(2,'0')}_v011.png`,raw=await sharp(path.join(root,pilot,name)).ensureAlpha().raw().toBuffer(),guard=renderAction(guards,ledger.rig,state),output=Buffer.from(raw),mask=Buffer.alloc(raw.length);
  const locked=action==='idle'?stateIndex===0:stateIndex===3,regions=[];
  if(action==='idle')regions.push({id:'waist',center:[32,54],rx:9,ry:3});
  else for(const[id,j]of Object.entries(state.joints)){
   // 准备帧只有双臂改变，站姿腿部直接保留idle基准，避免无原因的膝部跳色。
   if(stateIndex===0&&id.startsWith('leg'))continue;
   if(id.startsWith('leg'))regions.push({id:id+'_hip',center:j.root,rx:3.2,ry:3.2},{id:id+'_knee',center:j.joint,rx:4.8,ry:4.8},{id:id+'_ankle',center:j.ankle,rx:4,ry:3.5});
   else regions.push({id:id+'_shoulder',center:j.root,rx:3.4,ry:3.4},{id:id+'_elbow',center:j.joint,rx:3.5,ry:3.5});
  }
  if(!locked)for(let y=45;y<H;y++)for(let x=0;x<W;x++){
   const at=(y*W+x)*4,from=(((stateIndex>>1)*H+y)*128+(stateIndex%2)*W+x)*4;
   if(guard[at+3]||!regions.some(r=>((x+.5-r.center[0])/r.rx)**2+((y+.5-r.center[1])/r.ry)**2<=1))continue;
   mask.set([255,255,255,255],at);
   if(!patch[from+3]&&raw[at+3])continue;
   // 新增只能是暗色内芯；生成图的亮边或光晕不进入透明连接区。
   if(!raw[at+3]&&patch[from+3]&&patch[from]+patch[from+1]+patch[from+2]>350)continue;
   patch.copy(output,at,from,from+4);
  }
  let sharedPosePatch=null;
  if(action==='collect'&&stateIndex===2){
   // 保持帧与下探帧的身体/腿/远臂排姿完全相同。复用同一关节修形，避免AI逐格改型。
   const previous=ledger.states[1],armMasks={};
   for(const[id,part]of Object.entries(parts))armMasks[id]=id.startsWith('arm_left_')?protectRange(part,0,H-1,1).mask:Buffer.alloc(part.length);
   for(const key of Object.keys(state.transforms).filter(k=>!k.startsWith('arm_left_')))if(JSON.stringify(state.transforms[key])!==JSON.stringify(previous.transforms[key]))throw Error('Hold patch reuse encountered a changed pose');
   const beforeMask=renderAction(armMasks,ledger.rig,previous),afterMask=renderAction(armMasks,ledger.rig,state);
   const elbows=[previous.joints.arm_left,state.joints.arm_left].flatMap(j=>[j.root,j.joint]);
   let sharedPixels=0;
   for(let y=0;y<H;y++)for(let x=0;x<W;x++){
    const at=(y*W+x)*4,nearArm=beforeMask[at+3]||afterMask[at+3]||elbows.some(p=>((x+.5-p[0])/3.5)**2+((y+.5-p[1])/3.5)**2<=1);
    if(!nearArm){frames[1].copy(output,at,at,at+4);sharedPixels++;}
   }
   sharedPosePatch={reference_frame:1,scope:'body, legs, boots and far arm outside old/new anatomical left arm union',shared_pixels:sharedPixels};
  }
  let changed=0,protectedChanges=0,outsideChanges=0;
  for(let at=0;at<raw.length;at+=4)if(!raw.subarray(at,at+4).equals(output.subarray(at,at+4))){changed++;if(guard[at+3])protectedChanges++;if(!mask[at+3])outsideChanges++;}
  if(protectedChanges||outsideChanges)throw Error('Action patch crossed protection');
  const alpha=components(output);if(alpha.length!==1)throw Error('Action patch left separated pixels: '+JSON.stringify(alpha.map(({indices,...c})=>c)));
  const file=`frames/${action}/${direction}/${name}`;await png(output,path.join(root,file));await png(mask,path.join(root,`qa/${action}_${direction}_joint_mask_f${String(stateIndex).padStart(2,'0')}.png`));
  frames.push(output);records.push({frame:stateIndex,file,sha256:sha(await fs.readFile(path.join(root,file))),locked,changed_pixels:changed,protected_pixels_changed:protectedChanges,outside_mask_changed:outsideChanges,shared_pose_patch:sharedPosePatch,regions});
 }
 for(const scale of[1,4])for(const[name,bg]of[['light',[236,233,216]],['dark',[24,38,49]],['transparent',null]])await contact(frames,path.join(root,`previews/${action}_${direction}_${name}_${scale}x_v011.png`),scale,bg,2);
 const report={status:'ACTION_PILOT_PENDING_VISUAL_REVIEW',action,direction,source_file:sourceFile,source_sha256:sha(bytes),source_size:[info.width,info.height],common_sheet_transform:[128/info.width,96*rows/info.height],no_per_frame_bbox_fit:true,protection:rules,records};
 await fs.writeFile(path.join(root,`qa/${action}_${direction}_joint_patch_v011.json`),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({action,direction,changed:records.map(r=>r.changed_pixels),protectedChanges:0,outsideChanges:0}));
}
if(require.main===module)(async()=>{for(const action of process.argv.slice(2))await processAction(action);})().catch(e=>{console.error(e);process.exitCode=1;});
module.exports={processAction};
