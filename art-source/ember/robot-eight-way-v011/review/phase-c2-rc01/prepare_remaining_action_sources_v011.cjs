// 只准备其余七向的固定动作源片；小样未通过前不批量输出新动作帧。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {extractParts,png,contact}=require('./build_fixed_rig_v011.cjs');
const {renderAction,actionState}=require('./build_action_pilot_v011.cjs');
const root=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const arm=(side,root,joint,end,polygon)=>({kind:'arm',side,root,joint,end,bend:side==='left'?-1:1,polygon,split:[joint[1],end[1]],end_part:false});
const leg=(side,root,joint,end,bend,polygon)=>({kind:'leg',side,root,joint,end,bend,polygon,split:[joint[1],end[1]],end_part:true});
const downRig={forward:[0,.4],limb_order:['arm_right','arm_left','leg_right','leg_left','body'],limbs:{
 arm_right:arm('right',[21.7,45.3],[16.7,52.3],[16.7,61.2],[[14,43],[22,43],[23,49],[21,51],[21,66],[19,67],[15,67],[12,65],[12,49]]),
 arm_left:arm('left',[42.7,45.3],[46.7,52.3],[47.7,60.1],[[42,43],[49,43],[51,48],[54,53],[54,67],[44,67],[44,51],[42,48]]),
 leg_right:leg('right',[26.7,60],[24,68],[22,74],1,[[22,56],[28,56],[29,61],[30,64],[30,71],[30,81],[16,81],[16,70],[20,69],[21,68],[21,63],[21,59]]),
 leg_left:leg('left',[38.7,60],[39,68.5],[39,74.5],-1,[[36,56],[40,56],[43,61],[44,65],[45,72],[46,81],[33,81],[33,71],[34,66],[34,60]])
}};
async function prepare(direction){
 let rig,parts={},sourceFile,baseReport;
 if(direction==='down'){
  rig=downRig;sourceFile='source/action-candidate-masters/robot_neutral_down_v011.png';
  const source=await sharp(path.join(root,sourceFile)).ensureAlpha().raw().toBuffer();parts=extractParts(source,rig).parts;
 }else{
  baseReport=JSON.parse(await fs.readFile(path.join(root,`qa/${direction}_fixed_rig_v011.json`),'utf8'));
  rig=baseReport.rig;sourceFile=`source/candidate-masters/robot_idle_${direction}_v011.png`;
  for(const p of baseReport.parts)parts[p.id]=await sharp(path.join(root,p.file)).ensureAlpha().raw().toBuffer();
 }
 const overlap=direction==='down'?[58,59]:[54,55],whole=Buffer.from(parts.body);parts.pelvis=Buffer.alloc(whole.length);
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){const at=(y*W+x)*4;if(y>=overlap[0])whole.copy(parts.pelvis,at,at,at+4);if(y>overlap[1])parts.body.fill(0,at,at+4);}
 rig.action_waist_overlap=overlap;
 const source=await sharp(path.join(root,sourceFile)).ensureAlpha().raw().toBuffer(),neutral=renderAction(parts,rig,actionState(rig,'idle',0));
 if(!neutral.equals(source))throw Error('Neutral source mismatch: '+direction);
 const bodyBelow=[];for(let y=64;y<H;y++)for(let x=0;x<W;x++)if(whole[(y*W+x)*4+3])bodyBelow.push([x,y]);
 if(bodyBelow.length)throw Error('Body contains lower limbs: '+direction+' '+JSON.stringify(bodyBelow));
 const entries=[];for(const[id,raw]of Object.entries(parts)){
  const file=`source/action-fixed-parts/${direction}/${id}.png`;await png(raw,path.join(root,file));entries.push({id,file,raw_sha256:sha(raw)});
 }
 const report={status:'FIXED_SOURCE_PREPARATION_ONLY',direction,source_file:sourceFile,source_sha256:sha(await fs.readFile(path.join(root,sourceFile))),
  rig,parts:entries,neutral_reassembly_pixel_mismatch:0,body_pixels_below_y64:bodyBelow,waist_overlap_source_rows:overlap,
  source_art_status:direction==='down'?'NEW_DOUBLE_SUPPORT_SOURCE_PENDING_TA':'STATIC_IDENTITY_PASS_ACTIONS_NOT_ACCEPTED',walk_frames_modified:false};
 const folder=path.join(root,'source/action-source-registration',direction);await fs.mkdir(folder,{recursive:true});
 await fs.writeFile(path.join(folder,'registration.json'),JSON.stringify(report,null,2)+'\n');
 await contact(Object.values(parts),path.join(root,`qa/${direction}_action_fixed_parts_4x.png`),4,[88,103,113]);
 return{direction,parts:entries.length,neutralMismatch:0};
}
module.exports={prepare,downRig};
if(require.main===module)(async()=>{for(const direction of process.argv.slice(2))console.log(JSON.stringify(await prepare(direction)));})().catch(error=>{console.error(error);process.exitCode=1;});
