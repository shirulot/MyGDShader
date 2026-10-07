// 仅给正式C1回执覆盖的SW两动作登记PASS；未审七向不继承。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const receipt='qa/ta-receipt-phase-c1-rc01.md',bytes=await fs.readFile(path.join(root,receipt));
 if(!bytes.toString('utf8').includes('PASS，仅SW/down_left新增idle2、collect4'))throw Error('Unexpected receipt');
 const meta=JSON.parse(await fs.readFile(path.join(root,'source/reference-phase-c1-rc01-metadata.json'),'utf8'));
 const clips=meta.clips.filter(c=>['idle','collect'].includes(c.action));
 for(const clip of clips)for(const frame of clip.frames)if(sha(await fs.readFile(path.join(root,frame.file)))!==frame.sha256)throw Error('Approved SW frame changed');
 await fs.writeFile(path.join(root,'source/action-acceptance-v011.json'),JSON.stringify({status:'SW_IDLE_COLLECT_ACCEPTED',receipt,receipt_sha256:sha(bytes),clips,excludes:['other seven directions idle/collect','main project integration']},null,2)+'\n');
 const file=path.join(root,'run-manifest.json'),manifest=JSON.parse(await fs.readFile(file,'utf8'));
 manifest.review_history=manifest.review_history.filter(r=>r.revision!=='phase-c1-rc01').concat({revision:'phase-c1-rc01',decision:'PASS',scope:'SW idle2 and collect4, six new frames',review:receipt,review_sha256:sha(bytes),zip_sha256:'0c62177198973b24bb3fbfcc306ba4617af3ad754eb5a0696bdfddb4f19f51df'});
 manifest.action_acceptance_registry='source/action-acceptance-v011.json';
 manifest.status='PHASE_C2_REMAINING_ACTIONS_IN_PROGRESS';manifest.phases.find(p=>p.id==='C').status='SW_PILOT_PASS_REMAINING_SEVEN_IN_PROGRESS';
 manifest.phase_c.art_acceptance='SW_PILOT_PASS_RETAINED';manifest.phase_c.approved_new_action_frames=6;
 await fs.writeFile(file,JSON.stringify(manifest,null,2)+'\n');console.log('Accepted 70 final-action frames: walk64 + SW idle2/collect4');
})().catch(error=>{console.error(error);process.exitCode=1;});
