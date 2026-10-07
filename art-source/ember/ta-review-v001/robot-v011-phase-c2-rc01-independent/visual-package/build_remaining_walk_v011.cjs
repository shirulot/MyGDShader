// 阶段 B：各方向独立登记分区/骨点，复用已通过的固定源片排姿方法。
// 本脚本拒绝重做 S / SW，防止覆盖已经审查通过的动画。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {extractParts,pose,render,contact,png,solveTwoBone,matrixBetween}=require('./build_fixed_rig_v011.cjs');
const ROOT=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const arm=(side,root,joint,end,polygon)=>({kind:'arm',side,root,joint,end,bend:side==='left'?1:-1,polygon,split:[joint[1],end[1]],end_part:false});
const leg=(side,root,joint,end,bend,polygon)=>({kind:'leg',side,root,joint,end,bend,polygon,split:[joint[1],end[1]],end_part:true});

// LEFT / RIGHT 是角色自身的左右。北向脚步在屏幕纵向投影较短，不能套用斜向的横向步幅。
const rigs={
  up_left:{forward:[-1,-.34],limb_order:['arm_right','leg_right','leg_left','body','arm_left'],limbs:{
    arm_left:arm('left',[20,47],[19,52],[19,58],[[13,47],[24,47],[24,54],[23,54],[23,63],[13,63]]),
    arm_right:arm('right',[43,47],[44,51],[44,57],[[39,47],[50,47],[50,62],[42,62],[41,56],[39,53]]),
    leg_left:leg('left',[26,55],[26,64.5],[25,72],1,[[24,54],[29,54],[32,57],[32,80],[19,80],[19,72],[22,70],[22,63],[23,63],[23,55]]),
    leg_right:leg('right',[38,55],[38,64.5],[39,72],1,[[36,54],[40,54],[41,57],[42,61],[44,67],[44,79],[34,79],[34,65],[35,62]])
  }},
  up:{forward:[0,-.40],limb_order:['arm_right','arm_left','leg_right','leg_left','body'],limbs:{
    arm_left:arm('left',[18,47],[17,52],[18,58],[[13,47],[23,47],[23,54],[22,54],[22,60],[20,63],[13,63]]),
    arm_right:arm('right',[44,47],[46,52],[45,58],[[40,47],[51,47],[51,63],[43,63],[42,57],[42,54],[40,54]]),
    leg_left:leg('left',[25,56],[24,65],[24,72],1,[[23,55],[28,55],[29,60],[30,64],[30,81],[17,81],[16,78],[17,73],[20,70],[20,64],[21,62],[22,61],[22,56]]),
    leg_right:leg('right',[38,56],[38,65],[39,72],-1,[[35,55],[40,55],[41,60],[44,63],[44,70],[47,73],[48,81],[33,81],[33,71],[34,65]])
  }},
  up_right:{forward:[1,-.34],limb_order:['arm_left','leg_left','leg_right','body','arm_right'],limbs:{
    arm_left:arm('left',[19,46],[18,50],[19,55],[[14,46],[23,46],[23,60],[14,60]]),
    arm_right:arm('right',[37,47],[39,51],[39,57],[[35,47],[47,47],[47,63],[38,63],[37,56],[35,53]]),
    leg_left:leg('left',[24,54],[24,64],[24,71],-1,[[23,53],[27,54],[28,59],[30,63],[30,79],[18,79],[18,72],[20,68],[20,60],[23,60]]),
    leg_right:leg('right',[34,55],[34,64],[35,72],-1,[[31,54],[35,54],[37,57],[38,62],[38,63],[41,63],[41,69],[44,71],[44,80],[30,81],[30,63],[30,59]])
  }},
  down_right:{forward:[1,.34],limb_order:['arm_left','leg_left','leg_right','body','arm_right'],limbs:{
    arm_right:arm('right',[19,47],[17,52],[18,58],[[13,47],[23,47],[23,57],[22,62],[21,64],[13,64]]),
    arm_left:arm('left',[43,47],[44,51],[44,57],[[40,47],[50,47],[50,62],[43,62],[42,56],[40,54]]),
    leg_right:leg('right',[26,56],[25,65],[25,72],1,[[24,54],[29,54],[31,58],[31,63],[30,67],[31,73],[31,80],[18,80],[18,72],[20,66],[22,64],[22,62],[23,58]]),
    leg_left:leg('left',[37,56],[37,65],[37,71],-1,[[34,54],[39,54],[40,58],[42,62],[43,67],[44,70],[47,73],[47,79],[33,79],[32,72],[32,64],[33,61]])
  }}
};

function poseForDirection(rig,frame){
  const state=pose(rig,frame),phase=[1,.6,0,-.6,-1,-.6,0,.6];
  const delta=(a,b)=>[a[0]-b[0],a[1]-b[1]],add=(a,b)=>[a[0]+b[0],a[1]+b[1]];
  const turn=(v,a)=>[v[0]*Math.cos(a)-v[1]*Math.sin(a),v[0]*Math.sin(a)+v[1]*Math.cos(a)];
  for(const[id,l]of Object.entries(rig.limbs))if(l.kind==='arm'){
    const root=state.joints[id].root;let elbow,wrist;
    if(rig.forward[0]>0){
      // 右向投影与左向相反，旋转符号必须同时反转，才与同侧腿交错。
      const a=-state.transforms[id+'_upper'].radians,b=-state.transforms[id+'_lower'].radians;
      elbow=add(root,turn(delta(l.joint,l.root),a));wrist=add(elbow,turn(delta(l.end,l.joint),b));
    }else if(rig.forward[0]===0){
      // 朝北沿屏幕纵向投影。手腕与同侧脚相反移动，肩肘仍由定长两骨解算承接。
      const k=(frame+(l.side==='left'?0:4))%8,target=add(l.end,[0,.60*phase[k]]);
      const solved=solveTwoBone(root,target,Math.hypot(...delta(l.joint,l.root)),Math.hypot(...delta(l.end,l.joint)),l.bend);
      if(solved.clamped)state.notes.push({limb:id,reason:'ARM_IK_TARGET_OUT_OF_REACH',...solved});
      elbow=solved.joint;wrist=solved.target;
    }else continue;
    state.transforms[id+'_upper']=matrixBetween(l.root,l.joint,root,elbow);
    state.transforms[id+'_lower']=matrixBetween(l.joint,l.end,elbow,wrist);
    state.joints[id]={root,joint:elbow,wrist};
  }
  state.arm_projection='opposite to same-side leg along the direction-specific ground projection';
  return state;
}

async function build(direction){
  const rig=rigs[direction];if(!rig)throw Error('No authored phase B rig for '+direction);
  const sourceFile=`source/candidate-masters/robot_idle_${direction}_v011.png`;
  const sourceBytes=await fs.readFile(path.join(ROOT,sourceFile)),source=await sharp(sourceBytes).ensureAlpha().raw().toBuffer();
  const {parts,owners}=extractParts(source,rig),partEntries=[];
  for(const[id,raw]of Object.entries(parts)){
    const file=`source/fixed-parts/${direction}/${id}.png`;await png(raw,path.join(ROOT,file));
    partEntries.push({id,file,raw_sha256:sha(raw)});
  }
  const neutral=render(parts,rig,pose(rig,0,true));
  let neutralMismatch=0;for(let at=0;at<source.length;at+=4)if(!source.subarray(at,at+4).equals(neutral.subarray(at,at+4)))neutralMismatch++;
  if(neutralMismatch)throw Error('Neutral reassembly lost '+neutralMismatch+' source pixels');
  // 身体分区不应带着下肢像素。此列表便于人工定位错误，不以连通性代替美术判断。
  const bodyBelow=[];for(let y=64;y<H;y++)for(let x=0;x<W;x++)if(parts.body[(y*W+x)*4+3])bodyBelow.push([x,y]);
  const frames=[],states=[],entries=[];
  for(let i=0;i<8;i++){
    const state=poseForDirection(rig,i),frame=render(parts,rig,state),name=`robot_walk_${direction}_f${String(i).padStart(2,'0')}_v011.png`;
    // 固定 rig 原帧留在 source；后续补丁只写 frames，方便独立重算。
    const file=`source/fixed-rig-pilot/${direction}/${name}`;await png(frame,path.join(ROOT,file));
    await png(frame,path.join(ROOT,'frames/walk',direction,name));frames.push(frame);states.push(state);entries.push({frame:i,file,raw_sha256:sha(frame)});
  }
  const opposition=['left','right'].map(side=>{
    const a0=states[0].joints['arm_'+side].wrist,a4=states[4].joints['arm_'+side].wrist;
    const l0=states[0].joints['leg_'+side].ankle,l4=states[4].joints['leg_'+side].ankle;
    const armProjection=(a0[0]-a4[0])*rig.forward[0]+(a0[1]-a4[1])*rig.forward[1];
    const legProjection=(l0[0]-l4[0])*rig.forward[0]+(l0[1]-l4[1])*rig.forward[1];
    return {side,contact_frame_pair:[0,4],arm_displacement_along_forward:armProjection,leg_displacement_along_forward:legProjection,opposed:armProjection*legProjection<0};
  });
  if(opposition.some(o=>!o.opposed))throw Error('Arm/leg projected phases are not opposed: '+direction);
  const report={status:'RAW_FIXED_RIG_NOT_ART_ACCEPTED',direction,canvas:[W,H],root:[32,80],fps:8,loop:true,source_file:sourceFile,source_sha256:sha(sourceBytes),rig,neutral_reassembly_pixel_mismatch:neutralMismatch,body_pixels_below_y64:bodyBelow,arm_leg_opposition:opposition,parts:partEntries,frames:entries,states};
  const pilot=path.join(ROOT,'source/fixed-rig-pilot',direction);
  await fs.writeFile(path.join(pilot,'rig_and_poses.json'),JSON.stringify(report,null,2)+'\n');
  await fs.writeFile(path.join(ROOT,`qa/${direction}_fixed_rig_v011.json`),JSON.stringify(report,null,2)+'\n');
  await contact(frames,path.join(pilot,'edit_target_4x.png'),4,null);
  await contact(frames,path.join(ROOT,`qa/${direction}_raw_walk_4x.png`),4,[236,233,216]);
  await contact(Object.values(parts),path.join(ROOT,`qa/${direction}_fixed_parts_4x.png`),4,[88,103,113]);
  return {direction,neutralMismatch,bodyBelow,opposition,ikWarnings:states.flatMap(s=>s.notes)};
}
module.exports={rigs,build,poseForDirection};
if(require.main===module)(async()=>{for(const d of process.argv.slice(2)){console.log(JSON.stringify(await build(d)));}})().catch(e=>{console.error(e);process.exitCode=1;});
