// 采集膝盖返修小样：保留原始像素部件，腿与骨盆保持中性支撑；仅重组，不绘制新像素。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const base=path.resolve(__dirname,'../..'),root=__dirname;
const {renderAction}=require(path.join(base,'build_action_pilot_v011.cjs'));
const {png,contact}=require(path.join(base,'build_fixed_rig_v011.cjs'));
const W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const rigid=p=>({sourcePivot:p,targetPivot:p,radians:0});
const empty=()=>Buffer.alloc(W*H*4);
function dilated(mask,x,y,radius){
 for(let dy=-radius;dy<=radius;dy++)for(let dx=-radius;dx<=radius;dx++){
  const xx=x+dx,yy=y+dy;if(xx>=0&&xx<W&&yy>=0&&yy<H&&mask[(yy*W+xx)*4+3])return true;
 }
 return false;
}
async function run(direction='down_right'){
 const folder=direction==='down_left'?'action-rig-pilot':'action-rig-batch';
 const ledger=JSON.parse(await fs.readFile(path.join(base,`source/${folder}/collect/${direction}/rig_and_poses.json`),'utf8'));
 const parts={},lowerParts={},upperParts={},armParts={};
 for(const p of ledger.parts){
  parts[p.id]=await sharp(path.join(base,p.file)).ensureAlpha().raw().toBuffer();
  const lower=p.id==='pelvis'||p.id.startsWith('leg_');
  lowerParts[p.id]=lower?parts[p.id]:empty();upperParts[p.id]=lower?empty():parts[p.id];armParts[p.id]=p.id.startsWith('arm_')?parts[p.id]:empty();
 }
 const originals=[],candidates=[],records=[];
 for(let frame=0;frame<4;frame++){
  const name=`robot_collect_${direction}_f${String(frame).padStart(2,'0')}_v011.png`;
  const originalFile=`frames/collect/${direction}/${name}`,bytes=await fs.readFile(path.join(base,'delivery/robot-v011',originalFile));
  const original=await sharp(bytes).ensureAlpha().raw().toBuffer();
  originals.push(original);let output=Buffer.from(original),changed=0,state=structuredClone(ledger.states[frame]);
  if(frame===1||frame===2){
   // 去掉屏幕平面IK的横向膝外翻，保持髋、膝、踝的母版坐标；上身和工具臂沿用原动作。
   state.transforms.pelvis=rigid([32,56]);state.pelvis_shift=[0,0];
   for(const[id,limb]of Object.entries(ledger.rig.limbs))if(limb.kind==='leg'){
    for(const[segment,pivot]of [['upper',limb.root],['lower',limb.joint],['end',limb.end]])state.transforms[id+'_'+segment]=rigid(pivot);
    state.joints[id]={root:limb.root,joint:limb.joint,ankle:limb.end,lift:0,contact:true};
   }
   const raw=renderAction(parts,ledger.rig,state);
   const oldLower=renderAction(lowerParts,ledger.rig,ledger.states[frame]);
   const newLower=renderAction(lowerParts,ledger.rig,state);
   const upper=renderAction(upperParts,ledger.rig,state);
   const arms=renderAction(armParts,ledger.rig,state);
   // 覆盖旧腿及其接缝范围，同时保留在其前方的胸甲、手臂和此前修好的肘外边。
   for(let y=53;y<H;y++)for(let x=0;x<W;x++){
    const at=(y*W+x)*4;
    if(upper[at+3]||dilated(arms,x,y,1)||!(dilated(oldLower,x,y,3)||dilated(newLower,x,y,3)))continue;
    raw.copy(output,at,at,at+4);
   }
  }
  for(let at=0;at<output.length;at+=4)if(!output.subarray(at,at+4).equals(original.subarray(at,at+4)))changed++;
  await fs.mkdir(path.join(root,'source',direction),{recursive:true});
  await fs.writeFile(path.join(root,'source',direction,`baseline_f${frame}.png`),bytes);
  await png(output,path.join(root,'source',direction,`fixed_support_raw_f${frame}.png`));
  candidates.push(output);records.push({frame,original:originalFile,original_sha256:sha(bytes),changed_pixels:changed,state});
 }
 await contact(candidates,path.join(root,'source',direction,'edit_target_4x.png'),4,null,2);
 await contact(originals.concat(candidates),path.join(root,'qa',`${direction}_before_after_light_4x.png`),4,[236,233,216],4);
 await fs.writeFile(path.join(root,'source',direction,'poses.json'),JSON.stringify({status:'ASSEMBLY_FOR_IMAGEGEN_NOT_FINAL',direction,canvas:[W,H],frames:records},null,2)+'\n');
 const note={status:'PILOT_PREPARATION',scope:'collect knee correction only',direction,method:'existing_imagegen_source_parts_then_local_imagegen_edit',approved_baseline:'../../delivery/robot-v011',no_per_frame_bbox_fit:true,preserved_actions:['idle','walk'],production_ready:false};
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify(note,null,2)+'\n');
 console.log(JSON.stringify({direction,changed:records.map(r=>r.changed_pixels),preview:`qa/${direction}_before_after_light_4x.png`}));
}
run(process.argv[2]).catch(error=>{console.error(error);process.exitCode=1;});
