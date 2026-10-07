// 将本次真实来源与回执加入工作清单；冻结目录由单独步骤创建，既有包不改。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function run(){
 const file=path.join(root,'run-manifest.json'),m=JSON.parse(await fs.readFile(file,'utf8'));
 m.current_revision_fix={revision:'phase-b1-rc02',reference_revision:'phase-b1-rc01',scope:'N/NE/SE arm phase, shoulder/elbow connections and local occlusion',source_ownership_exception:{direction:'up_right',source_xy:[22,59],from:'body',to:'arm_left_lower',rgba_preserved:true},unchanged:['24 S/SW/NW walk frames byte-for-byte','eight identity masters byte-for-byte','body and leg/boot transforms','fixed source artwork except one pixel ownership transfer'],evidence:'qa/arm_phase_revision_evidence.json',art_acceptance:'PENDING_TA_RECHECK'};
 if(!m.review_history.some(r=>r.revision==='phase-b1-rc01'))m.review_history.push({revision:'phase-b1-rc01',decision:'NEEDS_REVISION',issue:'P2 NE/SE same-side arm and leg phase',review:'qa/ta-receipt-phase-b1-rc01.md',review_sha256:sha(await fs.readFile(path.join(root,'qa/ta-receipt-phase-b1-rc01.md')))});
 for(const d of['up_left','up','up_right','down_right']){
  const source=`source/walk_${d}_joint_edit_raw_v011.png`;
  if(!m.generation.some(g=>g.source===source))m.generation.push({scope:`B1 rc01 ${d} local joints`,method:'imagegen_edit',source,sha256:sha(await fs.readFile(path.join(root,source))),prompt:`prompts/walk_${d}_joint_edit_v011.txt`,usage:d==='up_left'?'CURRENT_JOINT_PATCH':'HISTORICAL_RC01_PATCH'});
 }
 for(const d of['up','up_right','down_right']){
  const source=`source/walk_${d}_joint_edit_b1_rc02.png`,input=`source/arm_edit_inputs_b1_rc02/${d}.png`;
  const entry={scope:`B1 rc02 ${d} shoulder and elbow`,method:'imagegen_edit',source,sha256:sha(await fs.readFile(path.join(root,source))),prompt:`prompts/walk_${d}_joint_edit_b1_rc02.txt`,actual_input:input,input_sha256:sha(await fs.readFile(path.join(root,input))),usage:'ARM_SCOPE_PATCH_ON_CORRECTED_FIXED_RIG',note:d==='up_right'?'Input predates the one-pixel ownership repair; exact input preserved separately.':'Fixed canvas; no per-frame registration.'};
  m.generation=m.generation.filter(g=>g.source!==source);m.generation.push(entry);
 }
 await fs.writeFile(file,JSON.stringify(m,null,2)+'\n');
 console.log('Manifest updated for rc02');
}
run().catch(e=>{console.error(e);process.exitCode=1;});
