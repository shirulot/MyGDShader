// 侧向隐藏源、相位与输出登记。它是技术/来源证据，不授予美术通过。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=path.resolve(__dirname,'..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=f=>fs.readFile(path.join(root,f)),json=async f=>JSON.parse(await read(f));
async function run(){
 const previous=await json('source/reference-phase-b1-rc02-metadata.json'),report={revision:'phase-b2-rc01',art_acceptance:'PENDING_TA',previous_batch_preserved:[],directions:[]};
 for(const f of previous.source_files){if(sha(await read(f.file))!==f.sha256)throw Error('Previous batch changed');report.previous_batch_preserved.push(f);}
 let md='# W/E 行走固定来源与步相\n\n新增W/E各8帧，64×96、root(32,80)、8FPS循环。B1 rc02的48行走帧与8身份图原字节保持。W/E不是镜像。完整隐藏肢体来自一次imagegen，分别一次裁切登记到母版坐标；登记尺寸不按动画帧变化。原母版可见像素覆盖隐藏源，静态实拼零差。随后每方向11个固定片排姿，局部imagegen只修连接。\n\n';
 for(const d of['left','right']){
  const ledger=await json(`source/fixed-rig-pilot/${d}/rig_and_poses.json`),patch=await json(`qa/${d}_joint_patch_v011.json`),opposition=[];
  for(const side of['left','right']){
   const a=ledger.states[0].joints,b=ledger.states[4].joints,f=ledger.rig.forward;
   const wrist=b['arm_'+side].wrist.map((v,i)=>v-a['arm_'+side].wrist[i]),ankle=b['leg_'+side].ankle.map((v,i)=>v-a['leg_'+side].ankle[i]);
   const ap=wrist[0]*f[0]+wrist[1]*f[1],lp=ankle[0]*f[0]+ankle[1]*f[1];
   if(ap*lp>=0)throw Error('Side phase mismatch');opposition.push({side,contact_frames:[0,4],wrist_delta_xy:wrist,ankle_delta_xy:ankle,arm_forward_delta:ap,leg_forward_delta:lp,opposed:true});
  }
  const body=await sharp(path.join(root,`source/fixed-parts/${d}/body.png`)).ensureAlpha().raw().toBuffer();let tail=0;
  for(let y=55;y<96;y++)for(let x=0;x<64;x++)if(body[(y*64+x)*4+3])tail++;
  if(tail)throw Error('Side body retains loose limb pixels');
  const toolPalette=new Set(['7b4d35','b77c4b','e2b77a']),brass={};
  for(const side of['left','right']){const p=await sharp(path.join(root,`source/fixed-parts/${d}/arm_${side}_lower.png`)).ensureAlpha().raw().toBuffer();brass[side]=0;for(let at=0;at<p.length;at+=4)if(p[at+3]&&toolPalette.has(p.subarray(at,at+3).toString('hex')))brass[side]++;}
  if(!brass.left||brass.right)throw Error('Tool chirality changed');
  report.directions.push({direction:d,neutral_difference:ledger.neutral_reassembly_pixel_mismatch,body_tail_pixels:tail,brass_pixels_by_anatomical_forearm:brass,registration:ledger.hidden_source_registration,opposition,states:ledger.states,final_frames:patch.records.map(r=>({frame:r.frame,file:r.file,sha256:r.sha256,changed_joint_pixels:r.changed_pixels,protected_pixels_changed:r.protected_pixels_changed,outside_mask_changed:r.outside_mask_changed}))});
  md+=`## ${d}\n\n![最终八帧](../previews/walk_${d}_light_4x_v011.png)\n\n解剖左前臂黄铜色像素${brass.left}，右前臂${brass.right}；右向工具由远侧左臂遮挡，不能加到近侧右臂。身体分区y55以下无残留手/腿像素。\n\n`;
  for(const o of opposition)md+=`${o.side}：F00→F04腕/踝沿朝向投影 ${o.arm_forward_delta.toFixed(3)} / ${o.leg_forward_delta.toFixed(3)}，异号。\n\n`;
  md+='| 帧/解剖侧 | 肩 → 肘 → 腕 | 髋 → 膝 → 踝 | 抬脚px |\n|---|---|---|---|\n';
  const p=v=>v.map(n=>n.toFixed(2)).join(',');
  ledger.states.forEach((state,i)=>{for(const side of['left','right']){const a=state.joints['arm_'+side],l=state.joints['leg_'+side];md+=`| F${String(i).padStart(2,'0')} ${side} | (${p(a.root)}) → (${p(a.joint)}) → (${p(a.wrist)}) | (${p(l.root)}) → (${p(l.joint)}) → (${p(l.ankle)}) | ${l.lift} |\n`;}});
 }
 await fs.writeFile(path.join(__dirname,'side_walk_evidence_v011.json'),JSON.stringify(report,null,2)+'\n');await fs.writeFile(path.join(__dirname,'side_walk_evidence_v011.md'),md);
 const manifest=await json('run-manifest.json');manifest.current_revision_fix={revision:'phase-b2-rc01',scope:'new W/E fixed-source walk, eight frames per direction',previous_batch:'phase-b1-rc02',unchanged_files:previous.source_files.length,evidence:'qa/side_walk_evidence_v011.json',art_acceptance:'PENDING_TA'};
 for(const d of['left','right']){
  const source=`source/walk_${d}_joint_edit_raw_v011.png`,input=`source/side_edit_inputs_b2_rc01/${d}.png`;
  manifest.generation=manifest.generation.filter(g=>g.source!==source);manifest.generation.push({scope:`B2 ${d} local joint edit`,method:'imagegen_edit',source,sha256:sha(await read(source)),prompt:`prompts/walk_${d}_joint_edit_v011.txt`,actual_input:input,input_sha256:sha(await read(input)),usage:'LOCAL_JOINT_PATCH_ON_FIXED_SIDE_RIG'});
 }
 const hidden='source/side_hidden_parts_raw_v011.png';if(!manifest.generation.some(g=>g.source===hidden))manifest.generation.push({scope:'W/E fixed hidden limbs',method:'imagegen_edit',source:hidden,sha256:sha(await read(hidden)),prompt:'prompts/side_hidden_parts_v011.txt',references:['qa/master_left_8x.png','qa/master_right_8x.png'],usage:'ONE_TIME_REGISTERED_HIDDEN_SOURCE',registration:'qa/side_walk_evidence_v011.json'});
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 console.log(JSON.stringify({status:'PASS',preserved_files:report.previous_batch_preserved.length,directions:report.directions.map(d=>({direction:d.direction,opposition:d.opposition,brass:d.brass_pixels_by_anatomical_forearm}))}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
