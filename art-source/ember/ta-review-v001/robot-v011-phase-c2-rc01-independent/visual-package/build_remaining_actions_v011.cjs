// C1已通过后扩展其余七向；保留SW新动作及全部已过walk。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {png,contact,solveTwoBone,matrixBetween}=require('./build_fixed_rig_v011.cjs');
const {renderAction,actionState}=require('./build_action_pilot_v011.cjs');
const root=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const add=(a,b)=>a.map((v,i)=>v+b[i]),delta=(a,b)=>a.map((v,i)=>v-b[i]);
function stateForDirection(rig,action,frame){
 // 正背向下压在此投影中用1px，避免强行把纵向屈膝投影成明显的横向膝外翻。
 const state=actionState(rig,action,frame,{crouchDrop:rig.forward[0]===0?1:2});
 if(action==='collect'&&rig.forward[0]===0&&frame!==3){
  // 正背向沿屏幕纵向投影手腕的前探，用定长双骨确定肘部，不能套斜向横摆。
  for(const[id,limb]of Object.entries(rig.limbs))if(limb.kind==='arm'){
   const shoulder=add(limb.root,state.upper_body_shift),front=rig.forward[1]>0;
   const reach=limb.side==='left'?(front?[.03,.15,.20,0][frame]:[-.2,-.9,-1.0,0][frame]):[0,-.3,-.3,0][frame];
   const wrist=add(limb.end,add(state.upper_body_shift,[0,reach]));
   const solved=solveTwoBone(shoulder,wrist,Math.hypot(...delta(limb.joint,limb.root)),Math.hypot(...delta(limb.end,limb.joint)),limb.bend);
   if(solved.clamped)state.notes.push({limb:id,reason:'ARM_IK_CLAMPED',...solved});
   state.transforms[id+'_upper']=matrixBetween(limb.root,limb.joint,shoulder,solved.joint);
   state.transforms[id+'_lower']=matrixBetween(limb.joint,limb.end,solved.joint,wrist);
   state.joints[id]={root:shoulder,joint:solved.joint,wrist};
  }
 }
 return state;
}
async function build(direction){
 if(!['down','left','up_left','up','up_right','right','down_right'].includes(direction))throw Error('Refusing approved or unknown direction');
 const receipt=await fs.readFile(path.join(root,'qa/ta-receipt-phase-c1-rc01.md'),'utf8');
 if(!receipt.includes('PASS，仅SW/down_left新增idle2、collect4'))throw Error('C1 pilot has not passed');
 const registration=JSON.parse(await fs.readFile(path.join(root,'source/action-source-registration',direction,'registration.json'),'utf8'));
 const parts={};for(const part of registration.parts)parts[part.id]=await sharp(path.join(root,part.file)).ensureAlpha().raw().toBuffer();
 const neutral=await sharp(path.join(root,registration.source_file)).ensureAlpha().raw().toBuffer();
 for(const action of ['idle','collect']){
  const states=[],frames=[],records=[],count=action==='idle'?2:4;
  for(let frame=0;frame<count;frame++){
   const state=stateForDirection(registration.rig,action,frame);if(state.notes.length)throw Error(direction+' unreachable: '+JSON.stringify(state.notes));
   const pixels=renderAction(parts,registration.rig,state),name=`robot_${action}_${direction}_f${String(frame).padStart(2,'0')}_v011.png`;
   const file=`source/action-rig-batch/${action}/${direction}/${name}`;
   await png(pixels,path.join(root,file));await png(pixels,path.join(root,'frames',action,direction,name));
   frames.push(pixels);states.push(state);records.push({frame,file,raw_sha256:sha(pixels)});
  }
  if(!frames[action==='idle'?0:3].equals(neutral))throw Error('Neutral/recovery differs');
  const folder=path.join(root,'source/action-rig-batch',action,direction);
  const ledger={...registration,status:'RAW_ACTION_RIG_NOT_ART_ACCEPTED',action,canvas:[64,96],root:[32,80],fps:action==='idle'?2:6,loop:action==='idle',states,frames:records};
  await fs.writeFile(path.join(folder,'rig_and_poses.json'),JSON.stringify(ledger,null,2)+'\n');
  await contact(frames,path.join(folder,'edit_target_4x.png'),4,null,2);
  await contact(frames,path.join(root,`qa/${action}_${direction}_raw_4x.png`),4,[236,233,216],2);
 }
 return{direction,idle:2,collect:4,ikWarnings:0};
}
module.exports={build,stateForDirection};
if(require.main===module)(async()=>{for(const direction of process.argv.slice(2))console.log(JSON.stringify(await build(direction)));})().catch(error=>{console.error(error);process.exitCode=1;});
