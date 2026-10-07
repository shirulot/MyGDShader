// 阶段 B 的局部关节合成：保护由各方向固定源片定义的甲片和末端。
// 接缝像素来自对应方向的 imagegen 编辑图；代码只登记/采样/合成，不绘制机械结构。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {render,contact,png}=require('./build_fixed_rig_v011.cjs');
const ROOT=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const palette=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A'].map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
const nearest=p=>palette.reduce((best,c)=>{const d=c.reduce((s,v,i)=>s+(v-p[i])**2,0);return d<best.d?{d,c}:best;},{d:Infinity,c:palette[0]}).c;

function protectRange(part,minY,maxY,margin=1){
  const mask=Buffer.alloc(W*H*4);let x0=W,x1=-1,y0=H,y1=-1;
  for(let y=Math.max(0,Math.ceil(minY));y<=Math.min(H-1,Math.floor(maxY));y++)for(let x=0;x<W;x++)if(part[(y*W+x)*4+3]){
    x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);
  }
  // 同时保护透明轮廓，避免“旧像素没改，但沿外边加胖了甲片”。
  if(x1>=0)for(let y=y0;y<=y1;y++)for(let x=Math.max(0,x0-margin);x<=Math.min(W-1,x1+margin);x++)mask.set([255,255,255,255],(y*W+x)*4);
  return {mask,rect:x1<0?null:[Math.max(0,x0-margin),y0,Math.min(W-1,x1+margin)-Math.max(0,x0-margin)+1,y1-y0+1]};
}
async function processDirection(direction){
  if(['down','down_left'].includes(direction))throw Error('Approved walk directions are read-only');
  const pilot=path.join(ROOT,'source/fixed-rig-pilot',direction),ledger=JSON.parse(await fs.readFile(path.join(pilot,'rig_and_poses.json'),'utf8'));
  const {rig}=ledger,parts={},protectedParts={},protection=[];
  let revisionScope=null;
  try{const scope=JSON.parse(await fs.readFile(path.join(ROOT,'qa/arm_phase_revision_scope.json'),'utf8'));if(scope.directions.includes(direction))revisionScope=scope;}
  catch(error){if(error.code!=='ENOENT')throw error;}
  for(const p of ledger.parts)parts[p.id]=await sharp(path.join(ROOT,p.file)).ensureAlpha().raw().toBuffer();
  const armMasks={};for(const[id,part]of Object.entries(parts))armMasks[id]=id.startsWith('arm_')?protectRange(part,0,H-1,1).mask:Buffer.alloc(part.length);
  let previousLedger=null;const previousParts={},ownershipRepairs=[];
  if(revisionScope){
    previousLedger=JSON.parse(await fs.readFile(path.join(ROOT,revisionScope.reference_root,direction,'rig_and_poses.json'),'utf8'));
    for(const p of previousLedger.parts){
      const oldPart=await sharp(path.join(ROOT,revisionScope.reference_root,direction,'parts',p.id+'.png')).ensureAlpha().raw().toBuffer();
      if(sha(oldPart)!==p.raw_sha256)throw Error('Previous source part changed');
      previousParts[p.id]=oldPart;
      if(sha(parts[p.id])===p.raw_sha256)continue;
      for(let at=0;at<oldPart.length;at+=4)if(!oldPart.subarray(at,at+4).equals(parts[p.id].subarray(at,at+4))){
        const x=(at/4)%W,y=Math.floor(at/4/W);
        // NE 的一枚腕部轮廓像素曾落在 body 分区；摆臂反相后暴露成孤点。
        // 只改源像素归属：同一个 (22,59) 从 body 移入左前臂，颜色不重画。
        if(direction!=='up_right'||x!==22||y!==59||!['body','arm_left_lower'].includes(p.id))throw Error('Unexpected fixed source art change');
        ownershipRepairs.push({part:p.id,source_xy:[x,y],before:[...oldPart.subarray(at,at+4)],after:[...parts[p.id].subarray(at,at+4)]});
      }
    }
    if(ownershipRepairs.length){
      const from=ownershipRepairs.find(r=>r.part==='body'),to=ownershipRepairs.find(r=>r.part==='arm_left_lower');
      if(ownershipRepairs.length!==2||!from||!to||from.after.some(Boolean)||to.before.some(Boolean)||JSON.stringify(from.before)!==JSON.stringify(to.after))throw Error('Ownership repair did not conserve the exact source RGBA');
    }
  }
  for(const[id,part]of Object.entries(parts)){
    if(id==='body'){protectedParts[id]=Buffer.from(part);protection.push({part:id,rule:'all opaque body source pixels'});continue;}
    const limbId=id.replace(/_(upper|lower|end)$/,''),limb=rig.limbs[limbId];let range;
    if(id.endsWith('_end'))range=[0,H-1];
    else if(limb.kind==='leg')range=id.endsWith('_upper')?[0,Math.floor(limb.joint[1]-2.5)]:[Math.ceil(limb.joint[1]+2),Math.floor(limb.end[1]-2)];
    else range=id.endsWith('_upper')?[0,Math.floor(limb.joint[1]-1.5)]:[Math.ceil(limb.joint[1]+2),H-1];
    const protectedRange=protectRange(part,...range);protectedParts[id]=protectedRange.mask;
    protection.push({part:id,source_y:range,source_rect:protectedRange.rect,rule:'rigid shell and transparent contour'});
  }
  const sourceFile=revisionScope?`source/walk_${direction}_joint_edit_b1_rc02.png`:`source/walk_${direction}_joint_edit_raw_v011.png`;
  const sourceBytes=await fs.readFile(path.join(ROOT,sourceFile)),meta=await sharp(sourceBytes).metadata();
  if(Math.abs(meta.width/meta.height-4/3)>.001)throw Error('Unexpected joint edit grid ratio');
  const patch=await sharp(sourceBytes).resize(256,192,{kernel:'nearest'}).ensureAlpha().raw().toBuffer();
  for(let at=0;at<patch.length;at+=4)if(patch[at+3]<160)patch.fill(0,at,at+4);else patch.set([...nearest(patch.subarray(at,at+3)),255],at);
  await sharp(patch,{raw:{width:256,height:192,channels:4}}).png().toFile(path.join(ROOT,`source/walk_${direction}_joint_edit_quantized_v011.png`));
  const frames=[],records=[],maskFrames=[],guardFrames=[];
  for(let i=0;i<8;i++){
    const stem=String(i).padStart(2,'0'),name=`robot_walk_${direction}_f${stem}_v011.png`;
    const original=await sharp(path.join(pilot,name)).ensureAlpha().raw().toBuffer(),state=ledger.states[i];
    const guard=render(protectedParts,rig,state),mask=Buffer.alloc(W*H*4),output=Buffer.from(original),regions=[];
    for(const[id,j]of Object.entries(state.joints)){
      if(id.startsWith('leg'))regions.push({id:id+'_hip',center:j.root,rx:3.2,ry:3.2},{id:id+'_knee',center:j.joint,rx:4.8,ry:4.8},{id:id+'_ankle',center:j.ankle,rx:4,ry:3.5});
      else regions.push({id:id+'_shoulder',center:j.root,rx:3.4,ry:3.4},{id:id+'_elbow',center:j.joint,rx:3.5,ry:3.5});
    }
    let changed=0,protectedDiff=0,outsideDiff=0;
    for(let y=0;y<H;y++)for(let x=0;x<W;x++){
      const at=(y*W+x)*4,from=(((i>>2)*H+y)*256+(i%4)*W+x)*4;
      if(y<45||guard[at+3]||!regions.some(r=>((x+.5-r.center[0])/r.rx)**2+((y+.5-r.center[1])/r.ry)**2<=1))continue;
      // 关节修补不得把原来连续的暗色内芯擦成透明缝；透明编辑像素保留原源。
      mask.set([255,255,255,255],at);
      if(!patch[from+3]&&original[at+3])continue;
      patch.copy(output,at,from,from+4);
    }
    let phaseRevision=null;
    if(revisionScope){
      const previous=previousLedger.states[i],before=await sharp(path.join(ROOT,revisionScope.reference_root,direction,name)).ensureAlpha().raw().toBuffer();
      for(const key of['body',...Object.keys(state.transforms).filter(k=>k.startsWith('leg_'))])if(JSON.stringify(state.transforms[key])!==JSON.stringify(previous.transforms[key]))throw Error('Arm revision moved body or legs');
      const previousArmMasks={},oldOwnershipMasks={},newOwnershipMasks={};
      for(const[id,part]of Object.entries(parts)){
        previousArmMasks[id]=id.startsWith('arm_')?protectRange(previousParts[id],0,H-1,1).mask:Buffer.alloc(part.length);
        oldOwnershipMasks[id]=Buffer.alloc(part.length);newOwnershipMasks[id]=Buffer.alloc(part.length);
      }
      // 一像素归属修复必须同时覆盖旧身体位置与新前臂位置；否则保留旧稿时会把孤点带回。
      for(const repair of ownershipRepairs){
        const at=(repair.source_xy[1]*W+repair.source_xy[0])*4;
        if(repair.before[3])oldOwnershipMasks[repair.part].set([255,255,255,255],at);
        if(repair.after[3])newOwnershipMasks[repair.part].set([255,255,255,255],at);
      }
      const oldArmMask=render(previousArmMasks,previousLedger.rig,previous),newArmMask=render(armMasks,rig,state),revisionMask=Buffer.alloc(W*H*4);
      const oldOwnershipMask=render(oldOwnershipMasks,previousLedger.rig,previous),newOwnershipMask=render(newOwnershipMasks,rig,state);
      const armRegions=[];
      for(const s of[previous,state])for(const[id,j]of Object.entries(s.joints))if(id.startsWith('arm_'))armRegions.push({center:j.root,rx:3.4,ry:3.4},{center:j.joint,rx:3.5,ry:3.5});
      let revisedPixels=0;
      for(let y=0;y<H;y++)for(let x=0;x<W;x++){
        const at=(y*W+x)*4,inside=y>=45&&(oldArmMask[at+3]||newArmMask[at+3]||oldOwnershipMask[at+3]||newOwnershipMask[at+3]||armRegions.some(r=>((x+.5-r.center[0])/r.rx)**2+((y+.5-r.center[1])/r.ry)**2<=1));
        if(inside)revisionMask.set([255,255,255,255],at);else before.copy(output,at,at,at+4);
        if(!output.subarray(at,at+4).equals(before.subarray(at,at+4)))revisedPixels++;
      }
      await png(revisionMask,path.join(ROOT,`qa/${direction}_arm_revision_mask_f${stem}.png`));
      phaseRevision={reference_revision:revisionScope.reference_revision,changed_pixels:revisedPixels,outside_old_new_arm_union_changed:0,body_and_leg_transforms_unchanged:true,source_ownership_repair_pixels:ownershipRepairs.length/2};
    }
    const boundaryViolations=[];
    for(let at=0;at<output.length;at+=4)if(!output.subarray(at,at+4).equals(original.subarray(at,at+4))){
      changed++;if(guard[at+3])protectedDiff++;if(!mask[at+3])outsideDiff++;
      if(guard[at+3]||!mask[at+3])boundaryViolations.push({xy:[at/4%W,Math.floor(at/4/W)],protected:!!guard[at+3],outside_mask:!mask[at+3],raw:[...original.subarray(at,at+4)],final:[...output.subarray(at,at+4)]});
    }
    if(protectedDiff||outsideDiff)throw Error(`Joint edit crossed a fixed source protection boundary: ${JSON.stringify({direction,frame:i,protectedDiff,outsideDiff,pixels:boundaryViolations})}`);
    const file=`frames/walk/${direction}/${name}`;await png(output,path.join(ROOT,file));await png(mask,path.join(ROOT,`qa/${direction}_joint_mask_f${stem}.png`));
    frames.push(output);maskFrames.push(mask);guardFrames.push(guard);records.push({frame:i,file,sha256:sha(await fs.readFile(path.join(ROOT,file))),changed_pixels:changed,protected_pixels_changed:protectedDiff,outside_mask_changed:outsideDiff,phase_revision:phaseRevision,regions});
  }
  for(const scale of[1,4])for(const[name,bg]of[['light',[236,233,216]],['dark',[24,38,49]],['transparent',null]])await contact(frames,path.join(ROOT,`previews/walk_${direction}_${name}_${scale}x_v011.png`),scale,bg);
  await contact(guardFrames,path.join(ROOT,`qa/${direction}_rigid_protection_4x.png`),4,[88,103,113]);
  await contact(maskFrames,path.join(ROOT,`qa/${direction}_joint_masks_4x.png`),4,[24,38,49]);
  const report={status:'PHASE_B_CANDIDATE_PENDING_VISUAL_REVIEW',direction,source_file:sourceFile,source_sha256:sha(sourceBytes),source_size:[meta.width,meta.height],common_sheet_transform:[256/meta.width,192/meta.height],no_per_frame_bbox_fit:true,preserve_existing_opaque_joint_core:true,source_ownership_repairs:ownershipRepairs,protection,records};
  await fs.writeFile(path.join(ROOT,`qa/${direction}_joint_patch_v011.json`),JSON.stringify(report,null,2)+'\n');
  return {direction,changed:records.map(r=>r.changed_pixels),protectedDiff:0,outsideDiff:0};
}
module.exports={processDirection,protectRange};
if(require.main===module)(async()=>{for(const d of process.argv.slice(2))console.log(JSON.stringify(await processDirection(d)));})().catch(e=>{console.error(e);process.exitCode=1;});
