// 只采纳imagegen腰髋接缝的颜色修形；透明度、固定腿靴和上身其它区域不随生成稿变化。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const base=path.resolve(__dirname,'../..'),root=__dirname;
const {png,contact}=require(path.join(base,'build_fixed_rig_v011.cjs'));
const {renderAction}=require(path.join(base,'build_action_pilot_v011.cjs'));
const {components}=require(path.join(base,'qa/audit_walk_components.cjs'));
const W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const palette=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A'].map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
const nearest=p=>palette.reduce((best,c)=>{const d=c.reduce((s,v,i)=>s+(v-p[i])**2,0);return d<best.d?{d,c}:best;},{d:Infinity,c:palette[0]}).c;
async function run(direction='down_right'){
 const folder=direction==='down_left'?'action-rig-pilot':'action-rig-batch';
 const ledger=JSON.parse(await fs.readFile(path.join(base,`source/${folder}/collect/${direction}/rig_and_poses.json`),'utf8'));
 const poses=JSON.parse(await fs.readFile(path.join(root,'source',direction,'poses.json'),'utf8'));
 const guards={};
 for(const part of ledger.parts)guards[part.id]=(part.id==='body'||part.id.startsWith('arm_'))?await sharp(path.join(base,part.file)).ensureAlpha().raw().toBuffer():Buffer.alloc(W*H*4);
 const sourceFile=`source/${direction}/imagegen_waist_edit.png`,source=await fs.readFile(path.join(root,sourceFile)),info=await sharp(source).metadata();
 if(info.width/info.height!==2/3)throw Error('Imagegen changed fixed sheet aspect ratio');
 const edit=await sharp(source).resize(128,192,{kernel:'nearest'}).ensureAlpha().raw().toBuffer();
 const frames=[],originals=[],records=[];
 for(let frame=0;frame<4;frame++){
  const raw=await sharp(path.join(root,'source',direction,`fixed_support_raw_f${frame}.png`)).ensureAlpha().raw().toBuffer();
  const original=await sharp(path.join(root,'source',direction,`baseline_f${frame}.png`)).ensureAlpha().raw().toBuffer();
  const output=Buffer.from(raw),guard=renderAction(guards,ledger.rig,poses.frames[frame].state);
  let editCount=0;
  if(frame===1||frame===2)for(let y=direction==='down'?58:54;y<=62;y++)for(let x=21;x<=42;x++){
   const at=(y*W+x)*4;
   // 相同腰髋姿态共用F01编辑源，不把每格生成的不一致装入保持帧。
   const from=(y*128+64+x)*4;
   if(!raw[at+3]||guard[at+3]||edit[from+3]<160)continue;
   const rgb=nearest(edit.subarray(from,from+3));
   if(!raw.subarray(at,at+3).equals(Buffer.from(rgb))){output.set(rgb,at);editCount++;}
  }
  const groups=components(output);
  if(groups.length!==1)throw Error('Detached source residue: '+JSON.stringify(groups.map(({indices,...g})=>g)));
  if(frame===0||frame===3){if(!output.equals(original))throw Error('Unchanged endpoint was altered');}
  let belowKneeChanges=0;
  for(let y=63;y<H;y++)for(let x=0;x<W;x++){const at=(y*W+x)*4;if(!raw.subarray(at,at+4).equals(output.subarray(at,at+4)))belowKneeChanges++;}
  if(belowKneeChanges)throw Error('Imagegen changed fixed lower legs');
  const file=`frames/collect/${direction}/robot_collect_${direction}_f${String(frame).padStart(2,'0')}_v012.png`;
  await png(output,path.join(root,file));
  // 首尾保留原PNG字节，避免仅重编码也被误记为动作修改。
  if(frame===0||frame===3)await fs.copyFile(path.join(root,'source',direction,`baseline_f${frame}.png`),path.join(root,file));
  frames.push(output);originals.push(original);
  records.push({frame,file,sha256:sha(await fs.readFile(path.join(root,file))),imagegen_waist_pixels:editCount,alpha_components:groups.length,knee_and_boot_edit_changes:belowKneeChanges});
 }
 for(const [name,bg]of[['light',[236,233,216]],['dark',[24,38,49]]])await contact(originals.concat(frames),path.join(root,'qa',`${direction}_before_after_${name}_4x.png`),4,bg,4);
 await contact(frames,path.join(root,'previews',`${direction}_strip_4x.png`),4,null,4);
 const report={status:'CANDIDATE_PENDING_VISUAL_REVIEW',direction,source_file:sourceFile,source_sha256:sha(source),source_size:[info.width,info.height],common_sheet_scale:[128/info.width,192/info.height],method:'fixed source support plus local imagegen waist edit',records};
 await fs.writeFile(path.join(root,'qa',`${direction}_patch.json`),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({direction,waist_edits:records.map(r=>r.imagegen_waist_pixels),components:records.map(r=>r.alpha_components)}));
}
run(process.argv[2]).catch(error=>{console.error(error);process.exitCode=1;});
