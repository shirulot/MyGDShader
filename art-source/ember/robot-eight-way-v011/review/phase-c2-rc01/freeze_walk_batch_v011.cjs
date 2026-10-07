// 冻结一个新的行走批次。既有快照绝不覆盖；Godot 缓存和日志不进入交付。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,revision=process.argv[2]||'phase-b1-rc01',sha=b=>crypto.createHash('sha256').update(b).digest('hex');
if(!/^phase-b\d-rc\d{2}$/.test(revision))throw Error('Invalid batch revision');
async function walk(folder){const found=[];for(const e of await fs.readdir(folder,{withFileTypes:true})){const p=path.join(folder,e.name);if(e.isDirectory())found.push(...await walk(p));else found.push(p);}return found;}
async function run(){
 const target=path.join(root,'review',revision);
 try{await fs.access(target);throw Error('Frozen batch already exists; choose a new revision');}catch(e){if(e.code!=='ENOENT')throw e;}
 const meta=JSON.parse(await fs.readFile(path.join(root,'walk-batch-metadata.json'),'utf8'));
 if(meta.revision!=='v011-'+revision)throw Error('Metadata revision mismatch');
 for(const file of['qa/export_validation_walk_batch.json','qa/godot_walk_batch_v011.json','qa/godot_walk_transitions_v011.json']){
  const report=JSON.parse(await fs.readFile(path.join(root,file),'utf8'));
  if(report.technical_checks!=='PASS'||report.atlas_sha256!==meta.atlas_sha256)throw Error('Validation is failed or stale: '+file);
 }
 const manifest=JSON.parse(await fs.readFile(path.join(root,'run-manifest.json'),'utf8'));
 manifest.status=revision.toUpperCase().replaceAll('-','_')+'_READY_FOR_TA';manifest.frozen_review='review/'+revision;
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 await fs.mkdir(target,{recursive:true});
 const chosen=['README-walk-batch.md','WORKLOG.md','eight_way_action_contract_v011.json','run-manifest.json','walk-batch-metadata.json','robot_walk_batch_atlas_v011.png','walk-review.html','review.html','source','prompts','frames','previews','qa','gpu-walk-playback','godot-walk-review','godot-review','build_fixed_rig_v011.cjs','build_remaining_walk_v011.cjs','composite_remaining_joints_v011.cjs','export_walk_batch_v011.cjs','validate_walk_batch_v011.cjs','verify_walk_transitions.gd'];
 if(revision.startsWith('phase-b2-'))chosen.push('build_side_walk_v011.cjs');
 if(revision.startsWith('phase-b2-'))chosen[chosen.indexOf('README-walk-batch.md')]='README-side-walk-batch.md';
 for(const item of chosen)await fs.cp(path.join(root,item),path.join(target,/^README-.*\.md$/.test(item)?'README.md':item),{recursive:true,filter:src=>!src.split(path.sep).includes('.godot')&&!src.endsWith('.log')});
 await fs.writeFile(path.join(target,'FROZEN.md'),`# ${revision}\n\n固定审查候选。编辑和重新生成请使用另一工作副本，不回写本包。独立 Godot 工程可以建立自己的导入缓存。入口 walk-review.html 与 godot-walk-review/project.godot。\n`);
 const files=[];for(const p of(await walk(target)).sort()){const b=await fs.readFile(p);files.push({file:path.relative(target,p).split(path.sep).join('/'),bytes:b.length,sha256:sha(b)});}
 await fs.writeFile(path.join(target,'sha256-manifest.json'),JSON.stringify({revision,status:'CANDIDATE_PENDING_TA',files},null,2)+'\n');
 console.log(JSON.stringify({frozen:target,files:files.length,bytes:files.reduce((s,f)=>s+f.bytes,0),catalog_sha256:sha(await fs.readFile(path.join(target,'sha256-manifest.json')))}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
