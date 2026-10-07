// 冻结一次独立审查快照；已有版本绝不覆盖。Godot缓存/日志不进入交付。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,revision=process.argv[2]||'phase-a-rc02';
if(!/^phase-a-rc\d{2}$/.test(revision))throw Error('Invalid review revision');
const target=path.join(root,'review',revision);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function walk(folder){const out=[];for(const e of await fs.readdir(folder,{withFileTypes:true})){const p=path.join(folder,e.name);if(e.isDirectory())out.push(...await walk(p));else out.push(p);}return out;}
async function run(){
 try{await fs.access(target);throw Error('Frozen review folder already exists; create a new revision');}catch(e){if(e.code!=='ENOENT')throw e;}
 const manifest=JSON.parse(await fs.readFile(path.join(root,'run-manifest.json'),'utf8'));
 manifest.status=revision.toUpperCase().replaceAll('-','_')+'_READY_FOR_TA';manifest.phases[0].status='READY_FOR_TA';manifest.frozen_review='review/'+revision;
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
 await fs.mkdir(target,{recursive:true});
 const chosen=['README.md','WORKLOG.md','eight_way_action_contract_v011.json','run-manifest.json','phase-a-metadata.json','robot_phase_a_atlas_v011.png','review.html','source','prompts','frames','previews','qa','gpu-playback','godot-review','build_fixed_rig_v011.cjs','composite_joint_repair_v011.cjs','export_phase_a_v011.cjs','validate_phase_a_assets.cjs','prepare_masters_v011.cjs'];
 for(const item of chosen)await fs.cp(path.join(root,item),path.join(target,item),{recursive:true,filter:src=>!src.split(path.sep).includes('.godot')&&!src.endsWith('.log')});
 await fs.writeFile(path.join(target,'FROZEN.md'),'# 冻结审查快照 '+revision+'\n\n本目录只读审查，不运行生成脚本覆盖这里的PNG。后续改动在v011工作目录中进行并另建rc版本。独立Godot工程允许生成自己的导入缓存。\n');
 const files=[];for(const p of (await walk(target)).sort()){const b=await fs.readFile(p);files.push({file:path.relative(target,p).split(path.sep).join('/'),bytes:b.length,sha256:sha(b)});}
 const catalog={revision,status:'CANDIDATE_PENDING_TA',files};
 await fs.writeFile(path.join(target,'sha256-manifest.json'),JSON.stringify(catalog,null,2)+'\n');
 console.log(JSON.stringify({frozen:target,files:files.length,bytes:files.reduce((s,f)=>s+f.bytes,0),catalog_sha256:sha(await fs.readFile(path.join(target,'sha256-manifest.json')))}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
