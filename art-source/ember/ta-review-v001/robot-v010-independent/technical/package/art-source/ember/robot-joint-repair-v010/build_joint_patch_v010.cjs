// 局部合成：视觉修改来自 imagegen 编辑稿；本脚本只固定格降采样、量化、裁取和合成。
// 不绘制肢体、不按透明洞补点、不按帧 bbox 缩放/齐底。输出只是待视觉审阅候选。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const base=__dirname, prior=path.join(base,'source/reference-v009');
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const sha=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const W=64,H=96,N=8;
// 膝轴在护膝下端；需包含上方护膝承接口，而不能只围住解算器骨端。
const regionDefs=[['shoulder',3.5,3.5],['elbow',4,5],['wrist',3,3.2],['hip',4,4],['knee',5.5,8],['ankle',4.5,4]];
const nearest=(rgb,palette)=>palette.reduce((best,p)=>{const d=p.reduce((s,v,i)=>s+(v-rgb[i])**2,0);return d<best.d?{p,d}:best;},{p:palette[0],d:Infinity}).p;
async function png(raw,width,height,file){await sharp(raw,{raw:{width,height,channels:4}}).png().toFile(path.join(base,file));}
function board(frames){const b=Buffer.alloc(256*192*4);frames.forEach((frame,i)=>{for(let y=0;y<H;y++)frame.copy(b,(((i>>2)*H+y)*256+(i%4)*W)*4,y*W*4,(y+1)*W*4);});return b;}
async function run(){
 const rig=await read(path.join(prior,'source/rig_down_v009.json'));
 const palette=rig.palette.map(hex=>[1,3,5].map(at=>parseInt(hex.slice(at,at+2),16)));
 const protectedIds=new Set(rig.parts.map((p,i)=>['head','chest_shell','left_wrist_tool','hand_left','hand_right'].includes(p.id)?i+1:-1));
 const rawFile=path.join(base,'source/joint_edit_raw_v010.png'),rawBytes=await fs.readFile(rawFile),meta=await sharp(rawBytes).metadata();
 if(meta.width/meta.height!==4/3)throw new Error('AI sheet aspect changed; do not stretch frame geometry');
 // 整张板唯一共同变换；原帧完全不缩放。输出声明为降采样的 AI 局部补丁。
 const edit=await sharp(rawBytes).resize(256,192,{kernel:'nearest',fit:'fill'}).ensureAlpha().raw().toBuffer();
 for(let i=0;i<edit.length;i+=4){if(edit[i+3]<160){edit.fill(0,i,i+4);continue;}const color=nearest(edit.subarray(i,i+3),palette);edit.set([...color,255],i);}
 await png(edit,256,192,'source/joint_edit_quantized_fixed_grid_1x.png');
 const frames=[],diagnostics=[],records=[],masks=[];
 for(let frame=0;frame<N;frame++){
  const stem=String(frame).padStart(2,'0'),originalFile=path.join(prior,`frames/robot_walk_down_f${stem}_v009.png`);
  const original=await sharp(originalFile).ensureAlpha().raw().toBuffer();
  const owner=await sharp(path.join(prior,`owner_maps/walk_down_f${stem}_owner_v009.png`)).ensureAlpha().raw().toBuffer();
  const pose=await read(path.join(prior,`poses/walk_down_f${stem}_v009.json`));
  const regions=[];for(const side of ['left','right'])for(const [joint,rx,ry]of regionDefs){const center=pose.keypoints_projected[`${joint}_${side}`];regions.push({id:`${joint}_${side}`,viewer_side:side==='left'?'right':'left',center,rx,ry});}
  const output=Buffer.from(original),mask=Buffer.alloc(W*H*4),diag=Buffer.from(original),changed=[];let protectedDiff=0,outsideDiff=0;
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){
   const at=(y*W+x)*4;
   const selected=regions.filter(r=>((x+.5-r.center[0])/r.rx)**2+((y+.5-r.center[1])/r.ry)**2<=1);
   const src=((((frame>>2)*H+y)*256+(frame%4)*W+x)*4);
   const originalLight=original[at]*.2126+original[at+1]*.7152+original[at+2]*.0722;
   const patchLight=edit[src]*.2126+edit[src+1]*.7152+edit[src+2]*.0722;
   // 主装甲保留原亮面；膝/踝/肘的关节盖允许跟随同一 AI 补丁一起修改，
   // 避免只换暗面却留下旧的横向亮边，造成新旧表面互相切断。
   // 膝/踝/肘使用完整的重画盖面（含边缘透明像素），去掉旧零件外伸的断面。
   // 肩/髋/腕仍只采用不透明中间调；禁止影响受保护的头胸、手与工具。
   const redrawCover=selected.some(r=>/^(knee|ankle|elbow)_/.test(r.id));
   const allowed=selected.length>0&&!protectedIds.has(owner[at])&&y>43
    &&(redrawCover||((original[at+3]===0||originalLight<125)&&edit[src+3]===255&&patchLight>=65));
   if(allowed){
    mask.set([255,255,255,255],at);
    edit.copy(output,at,src,src+4);
    if(!output.subarray(at,at+4).equals(original.subarray(at,at+4))){changed.push({xy:[x,y],joint_regions:selected.map(r=>r.id),before:[...original.subarray(at,at+4)],after:[...output.subarray(at,at+4)]});diag.set([226,183,122,255],at);}
   }
   const differs=!output.subarray(at,at+4).equals(original.subarray(at,at+4));
   if(protectedIds.has(owner[at])&&differs)protectedDiff++;
   if(!allowed&&differs)outsideDiff++;
  }
  const file=`frames/robot_walk_down_f${stem}_v010.png`;await png(output,W,H,file);
  await png(mask,W,H,`qa/edit_mask_f${stem}_v010.png`);
  frames.push(output);diagnostics.push(diag);masks.push(mask);
  records.push({frame,source_v009_sha256:sha(await fs.readFile(originalFile)),output_sha256:sha(await fs.readFile(path.join(base,file))),regions,changed_pixels:changed.length,protected_identity_pixels_changed:protectedDiff,outside_edit_mask_pixels_changed:outsideDiff,changes:changed});
 }
 const atlas=Buffer.alloc(W*N*H*4);frames.forEach((f,i)=>{for(let y=0;y<H;y++)f.copy(atlas,(y*W*N+i*W)*4,y*W*4,(y+1)*W*4);});
 await png(atlas,W*N,H,'robot_walk_down_atlas_v010.png');
 for(const [name,images]of [['contact',frames],['edit_regions',diagnostics],['masks',masks]]){
  const b=board(images);await png(b,256,192,`previews/${name}_1x_v010.png`);
  await sharp(b,{raw:{width:256,height:192,channels:4}}).resize(1024,768,{kernel:'nearest'}).png().toFile(path.join(base,`previews/${name}_4x_v010.png`));
 }
 const report={status:'LOCAL_COMPOSITE_CANDIDATE',raw_ai_sha256:sha(rawBytes),raw_ai_size:[meta.width,meta.height],single_global_grid_transform:[256/meta.width,192/meta.height],no_per_frame_bbox_alignment:true,original_source_resampling:false,patch_source:'imagegen local edit, jointly resampled and palette quantized',source_palette:rig.palette,protected_parts:['head','chest_shell','left_wrist_tool','hand_left','hand_right'],frames:records,art_acceptance:'NOT_CLAIMED'};
 await fs.writeFile(path.join(base,'qa/local_composite_v010.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({frames:records.map(r=>({frame:r.frame,changed:r.changed_pixels,protectedDiff:r.protected_identity_pixels_changed,outsideDiff:r.outside_edit_mask_pixels_changed})),rawSize:report.raw_ai_size}));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
