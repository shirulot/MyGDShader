// 固定整格导出与可复核量测；不改变角色像素，也不把数据检查当美术验收。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const base=__dirname,prior=path.join(base,'source/reference-v009'),W=64,H=96;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const pad=n=>String(n).padStart(2,'0');
function components(raw,diagonal){const seen=new Set(),out=[];for(let p=0;p<W*H;p++){if(seen.has(p)||raw[p*4+3]===0)continue;const todo=[p];seen.add(p);let count=0;while(todo.length){const q=todo.pop(),x=q%W,y=Math.floor(q/W);count++;for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){if(!diagonal&&Math.abs(dx)+Math.abs(dy)!==1)continue;const xx=x+dx,yy=y+dy,r=yy*W+xx;if(xx>=0&&xx<W&&yy>=0&&yy<H&&!seen.has(r)&&raw[r*4+3]){seen.add(r);todo.push(r);}}}out.push(count);}return out.sort((a,b)=>b-a);}
function background(raw,color){const b=Buffer.from(raw);for(let p=0;p<b.length;p+=4)if(b[p+3]===0)b.set([...color,255],p);return b;}
async function scaled(raw,factor){return factor===1?Buffer.from(raw):sharp(raw,{raw:{width:W,height:H,channels:4}}).resize(W*factor,H*factor,{kernel:'nearest'}).raw().toBuffer();}
async function run(){
 const composite=await read(path.join(base,'qa/local_composite_v010.json'));
 const frames=[],oldFrames=[],entries=[];
 const palette=new Set(composite.source_palette.map(c=>c.slice(1).toLowerCase()));
 for(let i=0;i<8;i++){
  const file=`frames/robot_walk_down_f${pad(i)}_v010.png`,bytes=await fs.readFile(path.join(base,file));
  const r=await sharp(bytes).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  if(r.info.width!==W||r.info.height!==H)throw Error('Unexpected cell size');
  const old=await sharp(path.join(prior,`frames/robot_walk_down_f${pad(i)}_v009.png`)).ensureAlpha().raw().toBuffer();
  const mask=await sharp(path.join(base,`qa/edit_mask_f${pad(i)}_v010.png`)).ensureAlpha().raw().toBuffer();
  let outsideChanged=0,alphaRemoved=0,paletteBad=0,alphaBad=0;
  for(let p=0;p<r.data.length;p+=4){if(![0,255].includes(r.data[p+3]))alphaBad++;if(r.data[p+3]&& !palette.has(r.data.subarray(p,p+3).toString('hex')))paletteBad++;
   if(!mask[p+3]&&!r.data.subarray(p,p+4).equals(old.subarray(p,p+4)))outsideChanged++;
   if(old[p+3]===255&&r.data[p+3]===0)alphaRemoved++;}
  const c8=components(r.data,true),c4=components(r.data,false);
  entries.push({frame:i,file,sha256:sha(bytes),binary_alpha:alphaBad===0,registered_palette:paletteBad===0,rgba_changes_outside_mask:outsideChanged,original_opaque_pixels_removed:alphaRemoved,alpha_components_8:c8,alpha_components_4:c4,protected_pixels_changed:composite.frames[i].protected_identity_pixels_changed});
  // 局部重画允许清除旧关节外伸断面；删除数记录供审阅，越出编辑范围才失败。
  if(outsideChanged||paletteBad||alphaBad||c8.length!==1)throw Error(`Technical repair regression in frame ${i}: ${JSON.stringify(entries.at(-1))}`);
  frames.push(r.data);oldFrames.push(old);
 }
 for(const [name,color]of [['dark',[24,38,49]],['light',[236,233,216]]]){
  for(const factor of [1,4]){
   const adjusted=await Promise.all(frames.map(f=>scaled(background(f,color),factor)));
   const file=`previews/walk_down_v010_${name}_${factor}x.gif`;
   await sharp(Buffer.concat(adjusted),{raw:{width:W*factor,height:H*factor*8,channels:4,pageHeight:H*factor}}).gif({colours:256,effort:7,dither:0,loop:0,delay:[130,120,130,120,130,120,130,120],interFrameMaxError:0,interPaletteMaxError:0}).toFile(path.join(base,file));
   const decoded=await sharp(path.join(base,file),{animated:true}).ensureAlpha().raw().toBuffer();
   if(!decoded.equals(Buffer.concat(adjusted)))throw Error('GIF decoded pixels differ');
  }
  let b=Buffer.alloc(256*192*4);for(let i=0;i<8;i++){const f=background(frames[i],color);for(let y=0;y<H;y++)f.copy(b,(((i>>2)*H+y)*256+(i%4)*W)*4,y*W*4,(y+1)*W*4);}
  await sharp(b,{raw:{width:256,height:192,channels:4}}).png().toFile(path.join(base,`previews/contact_${name}_1x_v010.png`));
  await sharp(b,{raw:{width:256,height:192,channels:4}}).resize(1024,768,{kernel:'nearest'}).png().toFile(path.join(base,`previews/contact_${name}_4x_v010.png`));
 }
 await sharp(Buffer.concat(frames),{raw:{width:W,height:H*8,channels:4,pageHeight:H}}).webp({lossless:true,effort:6,loop:0,delay:Array(8).fill(125)}).toFile(path.join(base,'previews/walk_down_v010_transparent_1x.webp'));
 // 修前标记仅为 QA 图：S肩 E肘 W腕 H髋 K膝 A踝。框定位检查范围，不遮改成品。
 const sourceBoard=await sharp(path.join(base,'source/v009_edit_target_4x.png')).flatten({background:'#ece9d8'}).png().toBuffer();
 const parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="768">'];
 const codes={shoulder:'S',elbow:'E',wrist:'W',hip:'H',knee:'K',ankle:'A'};
 for(let i=0;i<8;i++){
  const ox=(i%4)*256,oy=(i>>2)*384;parts.push(`<text x="${ox+10}" y="${oy+22}" font-size="14" fill="#2b3e4b">F${pad(i)} / BEFORE</text>`);
  const labelPositions=new Map();
  for(const side of ['left','right']){let last=oy+30;for(const r of composite.frames[i].regions.filter(r=>r.viewer_side===side).sort((a,b)=>a.center[1]-b.center[1])){last=Math.max(last+14,oy+r.center[1]*4);labelPositions.set(r.id,last);}}
  for(const r of composite.frames[i].regions){const x=ox+r.center[0]*4,y=oy+r.center[1]*4,code=codes[r.id.split('_')[0]],left=r.viewer_side==='left',labelX=left?ox+18:ox+224;const labelY=labelPositions.get(r.id);
   parts.push(`<rect x="${x-r.rx*4}" y="${y-r.ry*4}" width="${r.rx*8}" height="${r.ry*8}" fill="none" stroke="#b45e30" stroke-width="1"/><path d="M${labelX+6},${labelY-4}L${x},${y}" stroke="#b45e30" stroke-width="1"/><text x="${labelX}" y="${labelY}" font-size="12" font-family="sans-serif" fill="#6b3320">${code}</text>`);
  }
 }
 parts.push('</svg>');await sharp(sourceBoard).composite([{input:Buffer.from(parts.join(''))}]).png().toFile(path.join(base,'qa/before_joint_regions_v010.png'));
 const ledger=composite.frames.map(f=>({frame:f.frame,joints:f.regions.map(r=>({id:r.id,viewer_side:r.viewer_side,center:r.center,review:'thickness, overlap, dark cut-through, temporal continuity',changed_pixels:f.changes.filter(c=>c.joint_regions.includes(r.id)).length})),note:'Region markers identify the complete audit scope; not every marker independently asserts a literal alpha gap.'}));
 await fs.writeFile(path.join(base,'qa/joint_review_regions_v010.json'),JSON.stringify({legend:codes,frames:ledger},null,2)+'\n');
 const validation={status:'TECHNICAL_EXPORT_PASS',art_acceptance:'PENDING_VISUAL_REVIEW',cell:[W,H],fps:8,frames:entries,gif_pixel_fidelity:'EXACT_RGBA',loop_duration_ms:1000,meaning:'Data checks do not prove joint readability. Assess normal-speed 1x/4x on light and dark backgrounds.'};
 await fs.writeFile(path.join(base,'qa/export_validation_v010.json'),JSON.stringify(validation,null,2)+'\n');
 console.log(JSON.stringify({status:validation.status,frames:entries.map(f=>({frame:f.frame,components8:f.alpha_components_8,components4:f.alpha_components_4,outsideChanged:f.rgba_changes_outside_mask}))}));
}
run().catch(error=>{console.error(error);process.exitCode=1;});
