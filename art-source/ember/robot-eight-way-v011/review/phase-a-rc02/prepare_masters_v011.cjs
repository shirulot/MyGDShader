// AI 八向母板统一转换到项目原生格。只采样/量化/装配，不画角色或镜像方向。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const base=__dirname,dirs=['down','down_left','left','up_left','up','up_right','right','down_right'];
const colors=['#101820','#182631','#2B3E4B','#4D6470','#829BA3','#BECBC4','#566B78','#ECE9D8','#7B4D35','#B77C4B','#E2B77A'];
const palette=colors.map(h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const nearest=rgb=>palette.reduce((b,p)=>{const d=p.reduce((s,v,i)=>s+(v-rgb[i])**2,0);return d<b.d?{d,p}:b;},{d:Infinity,p:palette[0]}).p;
const masterOffsetY=[1,0,-1,-1,3,2,2,2];
// 八张静态母版的足底一次性登记；不是每个动作帧按 bbox 自动齐底。
// 数值来自对源板靴底接触边的作者标定，之后同方向全部姿态共用此登记。
async function protectDownIdentity(generated){
 const ref=path.join(base,'source/reference-down-v001');
 const original=await sharp(path.join(ref,'robot_idle_down_v001.png')).ensureAlpha().raw().toBuffer();
 const rig=JSON.parse(await fs.readFile(path.join(ref,'rig_down_v009.json'),'utf8'));
 const masks=JSON.parse(await fs.readFile(path.join(ref,'part_masks_v009.json'),'utf8'));
 const keep=new Set();for(const p of masks.parts)if(['head','chest_shell','left_wrist_tool','hand_left','hand_right'].includes(p.id))for(const [x,y]of p.pixels)keep.add(y*64+x);
 const defs=[['shoulder',3.5,3.5],['elbow',4,5],['wrist',3,3.2],['hip',4,4],['knee',5.5,8],['ankle',4.5,4]];
 const regions=[];for(const side of ['left','right'])for(const[joint,rx,ry]of defs)regions.push({id:joint+'_'+side,center:rig.keypoints[joint+'_'+side],rx,ry});
 const out=Buffer.from(original),changed=[];
 for(let y=0;y<96;y++)for(let x=0;x<64;x++){
  const at=(y*64+x)*4,selected=regions.filter(r=>((x+.5-r.center[0])/r.rx)**2+((y+.5-r.center[1])/r.ry)**2<=1);
  const light=b=>b[0]*.2126+b[1]*.7152+b[2]*.0722;
  const full=selected.some(r=>/^(elbow|knee|ankle)_/.test(r.id));
  if(!selected.length||keep.has(y*64+x)||y<=43)continue;
  if(!full&&!((original[at+3]===0||light(original.subarray(at,at+3))<125)&&generated[at+3]===255&&light(generated.subarray(at,at+3))>=65))continue;
  generated.copy(out,at,at,at+4);
  if(!out.subarray(at,at+4).equals(original.subarray(at,at+4)))changed.push({xy:[x,y],joints:selected.map(r=>r.id),before:[...original.subarray(at,at+4)],after:[...out.subarray(at,at+4)]});
 }
 await fs.writeFile(path.join(base,'qa/idle_down_identity_composite_v011.json'),JSON.stringify({source_sha256:sha(await fs.readFile(path.join(ref,'robot_idle_down_v001.png'))),protected_parts:['head','chest_shell','left_wrist_tool','hand_left','hand_right'],protected_source_pixels:keep.size,regions,changed_pixels:changed.length,changes:changed},null,2)+'\n');
 return out;
}
async function run(){
 const file=path.join(base,'source/eight_direction_idle_master_raw_v011.png'),bytes=await fs.readFile(file),meta=await sharp(bytes).metadata();
 if(meta.width%4||meta.height%2)throw Error('Source sheet not divisible into the declared 4x2 grid');
 const sw=meta.width/4,sh=meta.height/2;
 // 母板较提示的角色尺寸偏大：所有方向使用同一 50×75 等比采样和 (7,11) 注册，
 // 不是逐帧 bbox 自适应。该登记将在视觉审阅后固定到每个方向母版及它的全部动作。
 const dw=50,dh=75,ox=7,oy=11,frames=[],entries=[];
 await fs.mkdir(path.join(base,'source/candidate-masters'),{recursive:true});
 for(let i=0;i<8;i++){
  const crop=await sharp(bytes).extract({left:(i%4)*sw,top:Math.floor(i/4)*sh,width:sw,height:sh}).resize(dw,dh,{kernel:'nearest',fit:'fill'}).ensureAlpha().raw().toBuffer();
  let raw=Buffer.alloc(64*96*4);const directionY=oy+masterOffsetY[i];
  for(let y=0;y<dh;y++)for(let x=0;x<dw;x++){const s=(y*dw+x)*4,d=((y+directionY)*64+x+ox)*4;if(crop[s+3]<160)continue;raw.set([...nearest(crop.subarray(s,s+3)),255],d);}
  if(i===0){
   // 正面采用已通过 v010 的 F02 稳定站姿候选。整帧复用，避免接回旧待机后
   // 又引入旧关节和新手臂位置的混合。静态用途与微动仍需本轮重新审查。
   raw=await sharp(path.join(base,'frames/walk/down/robot_walk_down_f02_v010.png')).ensureAlpha().raw().toBuffer();
  }
  const output=`source/candidate-masters/robot_idle_${dirs[i]}_v011.png`;
  if(i===0)await fs.copyFile(path.join(base,'frames/walk/down/robot_walk_down_f02_v010.png'),path.join(base,output));
  else await sharp(raw,{raw:{width:64,height:96,channels:4}}).png().toFile(path.join(base,output));frames.push(raw);
  let minX=64,minY=96,maxX=-1,maxY=-1,count=0;for(let y=0;y<96;y++)for(let x=0;x<64;x++)if(raw[(y*64+x)*4+3]){minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);count++;}
  entries.push({direction:dirs[i],file:output,sha256:sha(await fs.readFile(path.join(base,output))),source_kind:i===0?'APPROVED_V010_FRAME_F02_BYTES_REUSED_FOR_STATIC_REVIEW':'IMAGEGEN_DIRECTION_MASTER',source_cell:i===0?null:[(i%4)*sw,Math.floor(i/4)*sh,sw,sh],common_scale_destination:i===0?null:[dw,dh],authored_master_offset:i===0?[0,0]:[ox,directionY],registration_applies_to_all_future_frames:true,bbox:[minX,minY,maxX+1,maxY+1],opaque_pixels:count,status:'UNREVIEWED_STATIC_MASTER'});
 }
 for(const [name,bg]of [['light',[236,233,216]],['dark',[24,38,49]],['transparent',null]]){
  const board=Buffer.alloc(256*192*4);for(let i=0;i<8;i++)for(let y=0;y<96;y++)for(let x=0;x<64;x++){const s=(y*64+x)*4,d=(((Math.floor(i/4)*96+y)*256)+(i%4)*64+x)*4;board.set(frames[i].subarray(s,s+4),d);if(bg&&board[d+3]===0)board.set([...bg,255],d);}
  for(const scale of [1,4])await sharp(board,{raw:{width:256,height:192,channels:4}}).resize(256*scale,192*scale,{kernel:'nearest'}).png().toFile(path.join(base,`previews/idle_directions_${name}_${scale}x_v011.png`));
 }
 const report={status:'CANDIDATE_MASTERS',source_sha256:sha(bytes),source_size:[meta.width,meta.height],registered_palette:colors,common_source_cell:[sw,sh],common_scale_destination:[dw,dh],authored_master_y_offsets:masterOffsetY,frame_registration:'common scale, authored static master ground registration locked per direction for all future frames; no per-animation-frame bbox fitting',mirroring:false,entries};
 await fs.writeFile(path.join(base,'qa/master_registration_v011.json'),JSON.stringify(report,null,2)+'\n');
 const manifest=JSON.parse(await fs.readFile(path.join(base,'run-manifest.json'),'utf8'));
 manifest.generation=[{scope:'eight direction neutral mother poses',method:'imagegen_edit',source:'source/eight_direction_idle_master_raw_v011.png',sha256:report.source_sha256,prompt:'prompts/eight_direction_idle_master_v011.txt',references:['source/approved_walk_down_v010_4x.png','source/original_four_direction_identity_4x.png','../robot-structure-v005/robot_three_views_annotated_v005.png'],processed_output_note:'common grid conversion and original palette; raw output is not natively 64x96'}];
 manifest.generation[0].used_directions=dirs.slice(1);
 manifest.generation.push({scope:'down idle joint edit attempt',method:'imagegen_edit',source:'source/idle_down_joint_edit_raw_v011.png',prompt:'prompts/idle_down_joint_edit_v011.txt',status:'REJECTED_NOT_USED',reason:'generated limb placement cannot be composited into the original idle without structural regression'});
 manifest.down_idle_source={file:'frames/walk/down/robot_walk_down_f02_v010.png',sha256:entries[0].sha256,method:'exact frozen frame reuse',status:'STATIC_POSE_CANDIDATE_PENDING_NEW_REVIEW',note:'This reuse preserves approved identity, but does not automatically approve idle support or later micro-motion.'};
 await fs.writeFile(path.join(base,'run-manifest.json'),JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify({source_size:report.source_size,entries:entries.map(e=>({direction:e.direction,bbox:e.bbox,opaque:e.opaque_pixels}))}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
