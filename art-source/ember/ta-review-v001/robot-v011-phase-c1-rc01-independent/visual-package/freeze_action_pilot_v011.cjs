// 冻结动作小样；禁止覆盖既有审查版本，冻结前绑定本次图集的所有检查。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,revision=process.argv[2]||'phase-c1-rc01',sha=b=>crypto.createHash('sha256').update(b).digest('hex');
if(!/^phase-c\d-rc\d{2}$/.test(revision))throw Error('Invalid action revision');
async function filesIn(folder){const out=[];for(const item of await fs.readdir(folder,{withFileTypes:true})){const p=path.join(folder,item.name);if(item.isDirectory())out.push(...await filesIn(p));else out.push(p);}return out;}
async function main(){
 const target=path.join(root,'review',revision);
 try{await fs.access(target);throw Error('Frozen revision already exists');}catch(error){if(error.code!=='ENOENT')throw error;}
 const read=async name=>JSON.parse(await fs.readFile(path.join(root,name),'utf8'));
 const meta=await read('action-pilot-metadata.json');if(meta.revision!=='v011-'+revision)throw Error('Wrong metadata revision');
 for(const file of ['qa/export_validation_action_pilot.json','qa/godot_action_pilot_v011.json']){
  const report=await read(file);if(report.technical_checks!=='PASS'||report.atlas_sha256!==meta.atlas_sha256)throw Error('Stale or failed validation: '+file);
 }
 const visual=await read('qa/visual-review-c1-rc01.json');if(visual.atlas_sha256!==meta.atlas_sha256||visual.producer_review!=='READY_FOR_INDEPENDENT_REVIEW')throw Error('Missing visual review');
 const manifest=await read('run-manifest.json');manifest.status='PHASE_C1_RC01_READY_FOR_TA';manifest.frozen_review='review/'+revision;
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 const chosen=['README-action-pilot.md','WORKLOG.md','eight_way_action_contract_v011.json','run-manifest.json','action-pilot-metadata.json','robot_action_pilot_atlas_v011.png','action-review.html','walk-review.html','walk-batch-metadata.json','robot_walk_batch_atlas_v011.png','source','prompts','frames','previews','qa','gpu-action-playback','godot-action-review','godot-walk-review','build_fixed_rig_v011.cjs','build_remaining_walk_v011.cjs','build_side_walk_v011.cjs','composite_remaining_joints_v011.cjs','build_action_pilot_v011.cjs','composite_action_pilot_v011.cjs','export_action_pilot_v011.cjs','validate_action_pilot_v011.cjs','freeze_action_pilot_v011.cjs'];
 await fs.mkdir(target,{recursive:true});
 for(const item of chosen)await fs.cp(path.join(root,item),path.join(target,item==='README-action-pilot.md'?'README.md':item),{recursive:true,filter:src=>!src.split(path.sep).includes('.godot')&&!src.endsWith('.log')&&!src.split(path.sep).includes('cold-action-validation')});
 await fs.writeFile(path.join(target,'FROZEN.md'),`# ${revision}\n\n固定待审动作小样。请在另一副本中编辑或验证；不回写原包。入口action-review.html与godot-action-review/project.godot。\n`);
 const files=[];for(const p of (await filesIn(target)).sort()){const bytes=await fs.readFile(p);files.push({file:path.relative(target,p).split(path.sep).join('/'),bytes:bytes.length,sha256:sha(bytes)});}
 await fs.writeFile(path.join(target,'sha256-manifest.json'),JSON.stringify({revision,status:'CANDIDATE_PENDING_TA',files},null,2)+'\n');
 console.log(JSON.stringify({frozen:target,payload_files:files.length,manifest_sha256:sha(await fs.readFile(path.join(target,'sha256-manifest.json')))}));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
