// 先做已通过SW母版的 idle2 / collect4 小样。行走PNG与原固定片只读。
// idle只移动胸头和双臂1px，骨盆与两靴不动；collect由同源部件排姿，末帧回中性。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {stamp,png,contact,matrixBetween,solveTwoBone}=require('./build_fixed_rig_v011.cjs');
const root=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]);
const turn=(v,a)=>[v[0]*Math.cos(a)-v[1]*Math.sin(a),v[0]*Math.sin(a)+v[1]*Math.cos(a)];
const rigid=(sourcePivot,targetPivot,radians=0)=>({sourcePivot,targetPivot,radians});

function renderAction(parts,rig,state){
 const out=Buffer.alloc(W*H*4);
 for(const id of rig.limb_order){
  if(id==='body'){stamp(out,parts.pelvis,state.transforms.pelvis);stamp(out,parts.body,state.transforms.body);continue;}
  for(const segment of['end','lower','upper'])if(parts[id+'_'+segment])stamp(out,parts[id+'_'+segment],state.transforms[id+'_'+segment]);
 }
 return out;
}

function actionState(rig,action,frame){
 const idle=action==='idle',phase=idle?['neutral','servo_up'][frame]:['prepare','reach','hold','recover'][frame];
 const drop=idle?0:[0,2,2,0][frame],lean=idle?0:[0,.8,.8,0][frame];
 const pelvisShift=[rig.forward[0]*lean,drop],upperShift=idle?[0,frame===1?-1:0]:pelvisShift;
 const transforms={body:rigid([32,54],add([32,54],upperShift)),pelvis:rigid([32,56],add([32,56],pelvisShift))},joints={},notes=[];
 for(const[id,l]of Object.entries(rig.limbs)){
  if(l.kind==='leg'){
   const hip=add(l.root,pelvisShift);let knee=l.joint;
   if(drop||lean){
    const solved=solveTwoBone(hip,l.end,Math.hypot(...sub(l.joint,l.root)),Math.hypot(...sub(l.end,l.joint)),l.bend);
    if(solved.clamped)notes.push({limb:id,reason:'LEG_IK_CLAMPED',...solved});knee=solved.joint;
   }
   transforms[id+'_upper']=matrixBetween(l.root,l.joint,hip,knee);transforms[id+'_lower']=matrixBetween(l.joint,l.end,knee,l.end);
   transforms[id+'_end']=rigid(l.end,l.end);joints[id]={root:hip,joint:knee,ankle:l.end,lift:0,contact:true};
  }else{
   const shoulder=add(l.root,upperShift),sign=rig.forward[0]<0?1:-1;
   const a=idle?0:(l.side==='left'?[.12,.42,.46,0][frame]*sign:[-.05,-.12,-.12,0][frame]*sign);
   const elbow=add(shoulder,turn(sub(l.joint,l.root),a)),wrist=add(elbow,turn(sub(l.end,l.joint),a*.72));
   transforms[id+'_upper']=matrixBetween(l.root,l.joint,shoulder,elbow);transforms[id+'_lower']=matrixBetween(l.joint,l.end,elbow,wrist);
   joints[id]={root:shoulder,joint:elbow,wrist};
  }
 }
 return{action,frame,phase,transforms,joints,notes,pelvis_shift:pelvisShift,upper_body_shift:upperShift,both_feet_fixed:true};
}

async function build(direction='down_left'){
 if(direction!=='down_left')throw Error('Only the approved SW action pilot is authored here');
 const original=JSON.parse(await fs.readFile(path.join(root,`qa/${direction}_fixed_rig_v011.json`),'utf8'));
 const rig=original.rig,parts={},partEntries=[];
 for(const p of original.parts)parts[p.id]=await sharp(path.join(root,p.file)).ensureAlpha().raw().toBuffer();
 const wholeBody=Buffer.from(parts.body);parts.pelvis=Buffer.alloc(wholeBody.length);
 // 两行重叠的原色腰部承接区；没有新增像素或绘制连接线。
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){const at=(y*W+x)*4;if(y>=54)wholeBody.copy(parts.pelvis,at,at,at+4);if(y>55)parts.body.fill(0,at,at+4);}
 for(const[id,raw]of Object.entries(parts)){
  const file=`source/action-fixed-parts/${direction}/${id}.png`;await png(raw,path.join(root,file));partEntries.push({id,file,raw_sha256:sha(raw)});
 }
 const sourceFile=`source/candidate-masters/robot_idle_${direction}_v011.png`,mother=await sharp(path.join(root,sourceFile)).ensureAlpha().raw().toBuffer();
 const neutral=renderAction(parts,rig,actionState(rig,'idle',0));if(!neutral.equals(mother))throw Error('Idle neutral did not reassemble original identity');
 for(const action of['idle','collect']){
  const count=action==='idle'?2:4,states=[],frames=[],entries=[];
  for(let i=0;i<count;i++){
   const state=actionState(rig,action,i);if(state.notes.length)throw Error('Unreachable pilot pose');
   const raw=renderAction(parts,rig,state),name=`robot_${action}_${direction}_f${String(i).padStart(2,'0')}_v011.png`;
   const file=`source/action-rig-pilot/${action}/${direction}/${name}`;await png(raw,path.join(root,file));await png(raw,path.join(root,'frames',action,direction,name));
   states.push(state);frames.push(raw);entries.push({frame:i,file,raw_sha256:sha(raw)});
  }
  if(action==='collect'&&!frames[3].equals(neutral))throw Error('Collect recovery must equal idle neutral');
  const report={status:'ACTION_PILOT_RAW_NOT_ART_ACCEPTED',action,direction,canvas:[64,96],root:[32,80],fps:action==='idle'?2:6,loop:action==='idle',source_file:sourceFile,source_sha256:sha(await fs.readFile(path.join(root,sourceFile))),rig,neutral_reassembly_pixel_mismatch:0,waist_overlap_source_rows:[54,55],parts:partEntries,frames:entries,states};
  const folder=path.join(root,'source/action-rig-pilot',action,direction);await fs.writeFile(path.join(folder,'rig_and_poses.json'),JSON.stringify(report,null,2)+'\n');
  await contact(frames,path.join(folder,'edit_target_4x.png'),4,null,2);await contact(frames,path.join(root,`qa/${action}_${direction}_raw_4x.png`),4,[236,233,216],2);
 }
 console.log(JSON.stringify({direction,neutralDifference:0,idle:2,collect:4,feet_fixed:true,collect_recovery_equals_idle_base:true}));
}
module.exports={renderAction,actionState,build};
if(require.main===module)build(process.argv[2]).catch(e=>{console.error(e);process.exitCode=1;});
