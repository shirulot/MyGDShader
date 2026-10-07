// 独立候选运行工程：仅替换采集动作，原版文件和主工程保持只读。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,base=path.resolve(root,'../..'),prior=path.join(base,'revisions/collect-knee-v012/runtime'),runtime=path.join(root,'runtime');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function put(file,data){const target=path.join(runtime,file);await fs.mkdir(path.dirname(target),{recursive:true});await fs.writeFile(target,data);}
async function run(){
 const meta=JSON.parse(await fs.readFile(path.join(prior,'full-action-metadata.json'),'utf8')),atlas=Buffer.alloc(512*2304*4);let same=0,changed=0;
 for(const clip of meta.clips){
  clip.art_status=clip.action==='collect'?'CANDIDATE_PENDING_USER_REVIEW':'PASS_RETAINED';
  for(const frame of clip.frames){
   const original=await fs.readFile(path.join(prior,frame.file));let bytes=original;
   if(clip.action==='collect'){frame.file=frame.file.replaceAll('v012','v013');bytes=await fs.readFile(path.join(root,frame.file));}
   if(bytes.equals(original))same++;else changed++;
   frame.sha256=sha(bytes);await put(frame.file,bytes);
   const raw=await sharp(bytes).ensureAlpha().raw().toBuffer();for(let y=0;y<96;y++)raw.copy(atlas,((frame.region[1]+y)*512+frame.region[0])*4,y*64*4,(y+1)*64*4);
  }
 }
 if(same!==96||changed!==16)throw Error('Unexpected frame change scope');
 const asset='assets/ember/robot_v013',atlasName='robot_eight_way_actions_atlas_v013.png';
 const bytes=await sharp(atlas,{raw:{width:512,height:2304,channels:4}}).png().toBuffer();await put(asset+'/'+atlasName,bytes);
 Object.assign(meta,{revision:'v013-knee-flexion',release:'robot-v013-candidate',status:'PENDING_USER_VISUAL_REVIEW',atlas:asset+'/'+atlasName,atlas_sha256:sha(bytes),unchanged_frames:same,changed_frames:changed,art_acceptance:{status:'PENDING_USER_VISUAL_REVIEW',reason:'v012 legs locked; user requires knee flexion'}});
 await put('full-action-metadata.json',JSON.stringify(meta,null,2));
 for(const file of['project.godot','preview/preview_full_actions.gd','preview/preview_full_actions.tscn','verify_import.gd','verify_collect.gd']){
  let source=(await fs.readFile(path.join(prior,file),'utf8')).replaceAll('v012','v013').replaceAll('REUSED_UNCHANGED_C2_SOURCE_VALIDATION','SEPARATE_V013_CHECK_REQUIRED');
  await put(file,source);
 }
 await put(asset+'/robot_eight_way_v013.tres',(await fs.readFile(path.join(prior,'assets/ember/robot_v012/robot_eight_way_v012.tres'),'utf8')).replaceAll('v012','v013'));
 await put(asset+'/'+atlasName+'.import',(await fs.readFile(path.join(prior,'assets/ember/robot_v012/robot_eight_way_actions_atlas_v012.png.import'),'utf8')).replaceAll('v012','v013').replace(/^uid=.*\r?\n/m,''));
 for(const folder of['frames','previews','evidence'])await put(folder+'/.gdignore','');
 for(const file of await fs.readdir(path.join(prior,'previews/full')))if(!file.startsWith('collect_'))await put('previews/full/'+file,await fs.readFile(path.join(prior,'previews/full',file)));
 for(const file of await fs.readdir(path.join(root,'previews')))if(file.endsWith('.gif')){
  const bytes=await fs.readFile(path.join(root,'previews',file));await put('previews/full/'+file,bytes);
  await put('previews/full/'+file.replace('.gif','.webp'),await sharp(bytes,{animated:true}).webp({lossless:true,loop:1}).toBuffer());
 }
 let preview=(await fs.readFile(path.join(prior,'preview.html'),'utf8')).replaceAll('v012','v013');
 preview=preview.replace('采集膝盖修订候选，等待新的视觉审查；待机与行走保持原帧。','v013 弯膝采集候选：髋下沉、膝向前、脚掌落地。等待用户视觉反馈。');await put('preview.html',preview);
 let compare=await fs.readFile(path.join(prior,'../compare.html'),'utf8');
 compare=compare.replace('下半身保持稳定支撑，上身与工具臂完成前探','恢复膝关节弯曲：髋部下沉后移，双膝沿脚尖方向前移，脚靴保持落地').replace('原 v011','v012 · 腿部锁定').replace('膝盖修订 v012','v013 · 恢复弯膝').replaceAll('_v012.gif','_v013.gif').replaceAll('_hip_knee_ankle_','_before_after_').replaceAll('_6x.png','_4x.png').replace('value="down_right" selected','value="down_right"').replace('value="left"','value="left" selected').replace('准备 → 前探 → 保持 → 回位','准备 → 屈膝前探 → 保持 → 回位');
 compare=compare.replace('</footer>','<br>网络参考：<a href="https://jonasz-o.itch.io/character-sprites-prototype-template-animation" target="_blank">像素下蹲序列</a> · <a href="https://www.fab.com/listings/38420cbf-0776-4a95-aab7-685564215b28" target="_blank">低位拾取支撑姿态</a>。当前为动作修订候选，未标记为已验收。</footer>');
 await fs.writeFile(path.join(root,'compare.html'),compare);
 const manifest=JSON.parse(await fs.readFile(path.join(root,'run-manifest.json'),'utf8'));Object.assign(manifest,{status:'CANDIDATE_PENDING_USER_VISUAL_REVIEW',generation:JSON.parse(await fs.readFile(path.join(root,'source/imagegen-ledger.json'),'utf8')),preserved_frames:same,changed_frames:changed,source_upper_body:'retained v012 actual PNG with translated upper-body mask',atlas_sha256:meta.atlas_sha256,main_project_modified:false});
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify(manifest,null,2));
 console.log(JSON.stringify({same,changed,atlas_sha256:meta.atlas_sha256}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
