// 按独立TA局部P2扩大原轮廓保护；核验仅两帧各恢复三个源像素。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {processAction}=require('../composite_action_pilot_v011.cjs');
const {contact}=require('../build_fixed_rig_v011.cjs');
const root=path.resolve(__dirname,'..'),frozen=path.join(root,'review/phase-c2-rc01');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const meta=JSON.parse(await fs.readFile(path.join(frozen,'full-action-metadata.json'),'utf8'));
 await fs.copyFile(path.join(frozen,'full-action-metadata.json'),path.join(root,'source/reference-phase-c2-rc01-metadata.json'));
 await processAction('collect','down_right',{batch:true});
 const records=[],comparison=[],crops=[];
 for(const clip of meta.clips)for(const frame of clip.frames){
  const bytes=await fs.readFile(path.join(root,frame.file)),oldBytes=await fs.readFile(path.join(frozen,frame.file));
  if(sha(oldBytes)!==frame.sha256)throw Error('Frozen baseline changed');
  const targeted=clip.name==='collect_down_right'&&[1,2].includes(frame.frame);
  if(!targeted){if(sha(bytes)!==frame.sha256)throw Error('Unrelated frame changed: '+frame.file);continue;}
  const before=await sharp(oldBytes).ensureAlpha().raw().toBuffer(),after=await sharp(bytes).ensureAlpha().raw().toBuffer();
  const raw=await sharp(path.join(root,frame.file.replace('frames/','source/action-rig-batch/'))).ensureAlpha().raw().toBuffer();
  const pixels=[];
  for(let y=0;y<96;y++)for(let x=0;x<64;x++){const at=(y*64+x)*4;if(!before.subarray(at,at+4).equals(after.subarray(at,at+4))){
   if(x!==14||![52,53,54].includes(y)||!after.subarray(at,at+4).equals(raw.subarray(at,at+4)))throw Error('Repair exceeded reviewed source contour');
   pixels.push({x,y,before:[...before.subarray(at,at+4)],after:[...after.subarray(at,at+4)],equals_original_rig:true});
  }}
  if(pixels.length!==3)throw Error('Expected three source contour pixels');
  records.push({frame:frame.frame,file:frame.file,before_sha256:frame.sha256,after_sha256:sha(bytes),pixels});
  comparison.push(before,after);
  for(const pixels of[raw,before,after])crops.push(await sharp(pixels,{raw:{width:64,height:96,channels:4}}).extract({left:10,top:45,width:16,height:20}).png().toBuffer());
 }
 for(const[bg,color]of[['light',[236,233,216]],['dark',[24,38,49]]]){
  await contact(comparison,path.join(root,`qa/se_elbow_rc02_before_after_${bg}_4x.png`),4,color,2);
  const layers=crops.map((input,i)=>({input,left:(i%3)*16,top:Math.floor(i/3)*20}));
  const board=await sharp({create:{width:48,height:40,channels:4,background:{r:color[0],g:color[1],b:color[2],alpha:1}}}).composite(layers).png().toBuffer();
  await sharp(board).resize(768,640,{kernel:'nearest'}).png().toFile(path.join(root,`qa/se_elbow_rc02_source_before_after_${bg}_16x.png`));
 }
 const report={revision:'phase-c2-rc02',finding:'SE collect F01/F02 outer elbow contour interrupted by local ivory patch',repair:'Protect original rig pixels only; no new drawing, source, pose or timing',changed_frames:2,unchanged_frames:110,total_changed_pixels:6,records};
 await fs.writeFile(path.join(root,'qa/se_elbow_rc02_revision.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({changed_frames:2,unchanged_frames:110,total_changed_pixels:6}));
})().catch(error=>{console.error(error);process.exitCode=1;});
