// 冻结登记与旧资源保护；不写任何角色 PNG。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const base=__dirname,workspace=path.resolve(base,'../../..'),ember=path.dirname(base);
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const hash=async file=>sha(await fs.readFile(file));
const json=async(file,obj)=>fs.writeFile(path.join(base,file),JSON.stringify(obj,null,2)+'\n');
async function run(){
 const baseline=await read(path.join(ember,'robot-fixed-rig-v007/source/production_baseline_sha256_v007.json'));
 const production=[];for(const item of baseline.files){const actual=await hash(item.file);production.push({file:item.file,sha256:actual,unchanged:actual===item.sha256});}
 const priorFrames=[];for(const version of ['v008','v009']){const manifest=await read(path.join(ember,`robot-fixed-rig-${version}/run-manifest.json`));for(const frame of manifest.frozen_frames){const file=path.join(workspace,frame.file.replace(/^res:\/\//,''));const actual=await hash(file);priorFrames.push({version,file,sha256:actual,unchanged:actual===frame.sha256});}}
 const oldArchives=[['robot_fixed_rig_v008_walk_down_candidate_2026-10-06.zip','ac74a58d6ac1751556751046571d5d983a9dcc4f9f85a146b4494706b055ff1b'],['robot_fixed_rig_v009_foot_revision_candidate_2026-10-06.zip','1abc164e76abc5e7f59978ae0d3062d07b37bd6edfe55c69335ec3f61318c60f']];
 const archiveChecks=[];for(const [name,expected]of oldArchives){const file=path.join(ember,'deliveries',name);const actual=await hash(file);archiveChecks.push({file,sha256:actual,unchanged:actual===expected});}
 const protection={status:[...production,...priorFrames,...archiveChecks].every(r=>r.unchanged)?'PASS':'FAIL',production_count:production.length,prior_frame_count:priorFrames.length,production,prior_frames:priorFrames,prior_archives:archiveChecks};
 await json('qa/production_protection_v010.json',protection);if(protection.status!=='PASS')throw Error('Existing asset protection failed; inspect report without overwriting originals');
 const validation=await read(path.join(base,'qa/export_validation_v010.json')),composite=await read(path.join(base,'qa/local_composite_v010.json')),manifest=await read(path.join(base,'run-manifest.json'));
 for(const frame of validation.frames)if(await hash(path.join(base,frame.file))!==frame.sha256)throw Error('Frozen frame changed');
 manifest.status='FROZEN_CANDIDATE_PENDING_TA';manifest.generation.source_output='source/joint_edit_raw_v010.png';manifest.generation.raw_sha256=composite.raw_ai_sha256;
 manifest.generation.raw_size=composite.raw_ai_size;manifest.generation.patch_transform=composite.single_global_grid_transform;manifest.generation.actual_pipeline='imagegen edit -> one shared nearest grid transform -> original 11-color palette -> joint-local pixel composite';
 manifest.scope.root_anchor=[32,80];manifest.scope.loop=true;manifest.frozen_frames=validation.frames.map(f=>({frame:f.frame,file:f.file,sha256:f.sha256}));
 manifest.frame_set_sha256=sha(Buffer.from(manifest.frozen_frames.map(f=>f.sha256).join('\n')));manifest.atlas={file:'robot_walk_down_atlas_v010.png',sha256:await hash(path.join(base,'robot_walk_down_atlas_v010.png')),size:[512,96]};
 manifest.edit_contract={protected_visible_parts:composite.protected_parts,changes_outside_mask:0,original_frame_resampling:false,per_frame_bbox_alignment:false,whole_joint_cover_repaint:['elbow','knee','ankle'],changed_pixels_per_frame:composite.frames.map(f=>f.changed_pixels),removed_original_opaque_pixels:validation.frames.map(f=>f.original_opaque_pixels_removed)};
 manifest.limitations=['Baked frame-local repair; original rig is a positioning reference, not a proof for new pixel contours','Down walk only; no acceptance claimed for other actions or directions','Visual acceptance remains separate from technical export tests'];
 manifest.validation={export:'qa/export_validation_v010.json',motion_skill:'qa/skill_motion_audit_v010.json',godot:'fixed_rig_playback_v010.json',protection:'qa/production_protection_v010.json'};
 await json('run-manifest.json',manifest);
 console.log(JSON.stringify({status:manifest.status,frame_set_sha256:manifest.frame_set_sha256,atlas_sha256:manifest.atlas.sha256,production:production.length,prior_frames:priorFrames.length,old_archives:archiveChecks.length}));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
