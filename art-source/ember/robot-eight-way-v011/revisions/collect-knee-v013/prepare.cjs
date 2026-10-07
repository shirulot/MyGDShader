// v013：在角色自身的前后平面求弯膝，再投影到八向画面。
// 源图只做部件变换；关节接缝交给 imagegen 定向编辑，不用代码绘制角色。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const base=path.resolve(__dirname,'../..'),root=__dirname,W=64,H=96;
const {png,contact,solveTwoBone}=require(path.join(base,'build_fixed_rig_v011.cjs'));
const dirs=['down','down_left','left','up_left','up','up_right','right','down_right'];
const forward=[[0,1],[-Math.SQRT1_2,Math.SQRT1_2],[-1,0],[-Math.SQRT1_2,-Math.SQRT1_2],[0,-1],[Math.SQRT1_2,-Math.SQRT1_2],[1,0],[Math.SQRT1_2,Math.SQRT1_2]];
const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
function segment(a,b,ta,tb){const sv=sub(b,a),tv=sub(tb,ta);return{sourcePivot:a,targetPivot:ta,radians:Math.atan2(tv[1],tv[0])-Math.atan2(sv[1],sv[0]),sourceAxis:Math.atan2(sv[1],sv[0]),projectedScale:Math.hypot(...tv)/Math.hypot(...sv)};}
function stamp(out,part,t){
 const c=Math.cos(t.radians),s=Math.sin(t.radians),axis=t.sourceAxis||0,u=[Math.cos(axis),Math.sin(axis)],scale=t.projectedScale||1;
 for(let y=0;y<H;y++)for(let x=0;x<W;x++){
  const dx=x+.5-t.targetPivot[0],dy=y+.5-t.targetPivot[1];let vx=dx*c+dy*s,vy=-dx*s+dy*c;
  // 仅沿骨段轴做投影缩短，横向装甲厚度保持；不按逐帧 bbox 缩放。
  const along=vx*u[0]+vy*u[1];vx+=along*(1/scale-1)*u[0];vy+=along*(1/scale-1)*u[1];
  const sx=Math.floor(vx+t.sourcePivot[0]),sy=Math.floor(vy+t.sourcePivot[1]);if(sx<0||sx>=W||sy<0||sy>=H)continue;
  const at=(sy*W+sx)*4,to=(y*W+x)*4;if(part[at+3])part.copy(out,to,at,at+4);
 }
}
function render(parts,rig,state,predicate=()=>true){const out=Buffer.alloc(W*H*4);for(const limb of rig.limb_order){const ids=limb==='body'?['pelvis','body']:['end','lower','upper'].map(s=>limb+'_'+s);for(const id of ids)if(parts[id]&&predicate(id))stamp(out,parts[id],state.transforms[id]);}return out;}
function nearbyAlpha(raw,x,y){for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const xx=x+dx,yy=y+dy;if(xx>=0&&xx<W&&yy>=0&&yy<H&&raw[(yy*W+xx)*4+3])return true;}return false;}
async function main(){
 const all=[];
 for(let d=0;d<dirs.length;d++){
  const direction=dirs[d],[fx,fz]=forward[d],folder=direction==='down_left'?'action-rig-pilot':'action-rig-batch';
  const ledger=JSON.parse(await fs.readFile(path.join(base,`source/${folder}/collect/${direction}/rig_and_poses.json`),'utf8'));
  const parts={};for(const p of ledger.parts)parts[p.id]=await sharp(path.join(base,p.file)).ensureAlpha().raw().toBuffer();
  const frames=[],generationInputs=[],records=[],outputDir=path.join(root,'source',direction);await fs.mkdir(outputDir,{recursive:true});
  for(let f=0;f<4;f++){
   const state=structuredClone(ledger.states[f]);let raw,approvedUpper=null;
   const baseline=path.join(base,`revisions/collect-knee-v012/frames/collect/${direction}/robot_collect_${direction}_f0${f}_v012.png`);
   await fs.copyFile(baseline,path.join(outputDir,`baseline_f${f}.png`));
   if(f===0||f===3){raw=await sharp(baseline).ensureAlpha().raw().toBuffer();generationInputs.push(raw);}
   else{
    const shift=[-.7*fx,2.4-.7*fz*.35];
    // 胸头与手臂保留原有形状，只随下沉平移；工具仍跟随原来的解剖学左臂。
    const upperShift=[0,2.4],delta=sub(upperShift,state.upper_body_shift);
    for(const[id,t]of Object.entries(state.transforms))if(id==='body'||id.startsWith('arm_'))t.targetPivot=add(t.targetPivot,delta);
    for(const[id,j]of Object.entries(state.joints))if(id.startsWith('arm_'))for(const k of['root','joint','wrist'])j[k]=add(j[k],delta);
    state.transforms.pelvis={sourcePivot:[32,56],targetPivot:add([32,56],shift),radians:0};
    state.pelvis_shift=shift;state.upper_body_shift=upperShift;
    for(const[id,l]of Object.entries(ledger.rig.limbs))if(l.kind==='leg'){
     const l1=l.joint[1]-l.root[1],l2=l.end[1]-l.joint[1];
     // 统一选择朝脚尖的解；绝不能按屏幕左右腿分别选择相反的 IK 分支。
     const solved=solveTwoBone([-.7,2.4],[0,l1+l2],l1,l2,-1);
     if(solved.clamped)throw Error('Sagittal target unreachable');
     const hip=add(l.root,shift),knee=add(l.joint,[fx*solved.joint[0],solved.joint[1]-l1+fz*.35*solved.joint[0]]);
     state.transforms[id+'_upper']=segment(l.root,l.joint,hip,knee);
     state.transforms[id+'_lower']=segment(l.joint,l.end,knee,l.end);
     state.transforms[id+'_end']={sourcePivot:l.end,targetPivot:l.end,radians:0};
     state.joints[id]={root:hip,joint:knee,ankle:l.end,contact:true,lift:0,sagittal_joint:solved.joint,source_lengths:[l1,l2]};
    }
    generationInputs.push(render(parts,ledger.rig,state));
    raw=render(parts,ledger.rig,state,id=>id!=='body'&&!id.startsWith('arm_'));
    // 已通过的上身含有后续肘部修形；从 v012 实际 PNG 保留，而不是退回修形前的源片。
    const oldUpper=render(parts,ledger.rig,ledger.states[f],id=>id==='body'||id.startsWith('arm_'));
    const approved=await sharp(baseline).ensureAlpha().raw().toBuffer(),upper=Buffer.alloc(W*H*4);
    for(let y=0;y<H;y++)for(let x=0;x<W;x++){const at=(y*W+x)*4;if(y<53||nearbyAlpha(oldUpper,x,y))approved.copy(upper,at,at,at+4);}
    const upperTransform={sourcePivot:[0,0],targetPivot:delta,radians:0};stamp(raw,upper,upperTransform);
    approvedUpper=Buffer.alloc(W*H*4);stamp(approvedUpper,upper,upperTransform);
   }
   const guard=render(parts,ledger.rig,state,id=>id.endsWith('_end')||(!approvedUpper&&(id==='body'||id.startsWith('arm_'))));
   if(approvedUpper)for(let at=0;at<guard.length;at+=4)if(approvedUpper[at+3])approvedUpper.copy(guard,at,at,at+4);
   await png(raw,path.join(outputDir,`pose_f${f}.png`));await png(guard,path.join(outputDir,`guard_f${f}.png`));
   frames.push(raw);records.push({frame:f,state,baseline_sha256:sha(await fs.readFile(baseline))});
  }
  await contact(frames,path.join(outputDir,'edit_target_4x.png'),4,null,2);
  // 保存与实际调用时完全相同的源片输入；后续只保留了已验收上身，不冒充二次生成。
  await contact(generationInputs,path.join(outputDir,'actual_imagegen_input_4x.png'),4,null,2);
  await contact(frames,path.join(root,'qa',`${direction}_assembly_4x.png`),4,[236,233,216],4);
  await fs.writeFile(path.join(outputDir,'poses.json'),JSON.stringify({direction,forward:[fx,fz],status:'SOURCE_PART_ASSEMBLY_FOR_IMAGEGEN',frames:records},null,2));
  all.push({direction,reference:`source/${direction}/edit_target_4x.png`,method:'source_part_projection_then_imagegen_joint_edit'});
 }
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify({revision:'v013',status:'IN_PROGRESS_NOT_ACCEPTED',scope:{cell:[64,96],root:[32,80],action:'collect',directions:dirs,frames:4,fps:6,loop:false},reason:'User requires working knee hinges; v012 locked legs rejected',strips:all},null,2));
 console.log('Prepared eight direction inputs.');
}
main().catch(e=>{console.error(e);process.exitCode=1;});
