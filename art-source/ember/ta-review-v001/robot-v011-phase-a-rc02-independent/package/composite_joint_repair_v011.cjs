// 把 imagegen 的局部关节编辑装回固定部件动画；只采样/量化/裁取，不画补缝像素。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {rigs,extractParts,render,contact,png}=require('./build_fixed_rig_v011.cjs');
const ROOT=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const colors=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A'];
const palette=colors.map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
const nearest=p=>palette.reduce((b,c)=>{const d=c.reduce((s,v,i)=>s+(v-p[i])**2,0);return d<b.d?{d,c}:b;},{d:Infinity,c:palette[0]}).c;
async function run(){
 const direction='down_left',rig=rigs[direction],pilot=path.join(ROOT,'source/fixed-rig-pilot',direction);
 const ledger=JSON.parse(await fs.readFile(path.join(pilot,'rig_and_poses.json'),'utf8'));
 const master=await sharp(path.join(ROOT,ledger.source_file)).ensureAlpha().raw().toBuffer();
 const {parts}=extractParts(master,rig),protectedParts={},armorParts={};
 // TA P2：远侧右腿的刚性大腿甲必须沿原源片排姿，不能由逐格关节补丁重画。
 // y54..62 是母版中这块甲的完整明暗/轮廓区域，y63往下才进入膝部连接。
 const rigidArmor={part:'leg_right_upper',max_source_y:62,contour_margin_x:1};
 for(const[id,part]of Object.entries(parts)){
   const keep=Buffer.alloc(part.length);
   for(let y=0;y<H;y++)for(let x=0;x<W;x++){
     const at=(y*W+x)*4;
     if(id==='body'||id.endsWith('_end')||(id.startsWith('arm_')&&y>=57)||(id===rigidArmor.part&&y<=rigidArmor.max_source_y))part.copy(keep,at,at,at+4);
   }
   // 手和靴子连同轮廓外的透明区域一起保护，避免补丁虽不改旧像素却添加新鞋边。
   if(id.endsWith('_end')||id.startsWith('arm_')){
     let minX=W,minY=H,maxX=-1,maxY=-1;
     for(let y=0;y<H;y++)for(let x=0;x<W;x++)if(keep[(y*W+x)*4+3]){
       minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);
     }
     if(maxX>=0)for(let y=minY;y<=Math.min(H-1,maxY+2);y++)for(let x=Math.max(0,minX-2);x<=Math.min(W-1,maxX+2);x++)keep.set([255,255,255,255],(y*W+x)*4);
   }
   if(id===rigidArmor.part){
     let minX=W,minY=H,maxX=-1;
     for(let y=0;y<=rigidArmor.max_source_y;y++)for(let x=0;x<W;x++)if(keep[(y*W+x)*4+3]){minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);}
     // 连透明轮廓边一起锁住，防止在不改旧像素的同时把甲片向侧面画胖。
     for(let y=minY;y<=rigidArmor.max_source_y;y++)for(let x=Math.max(0,minX-rigidArmor.contour_margin_x);x<=Math.min(W-1,maxX+rigidArmor.contour_margin_x);x++)keep.set([255,255,255,255],(y*W+x)*4);
     rigidArmor.source_protection_rect=[minX-rigidArmor.contour_margin_x,minY,maxX-minX+1+2*rigidArmor.contour_margin_x,rigidArmor.max_source_y-minY+1];
     armorParts[id]=Buffer.from(keep);
   }else armorParts[id]=Buffer.alloc(part.length);
   protectedParts[id]=keep;
 }
 const sourceFile=path.join(ROOT,'source/walk_down_left_joint_edit_raw_v011.png'),sourceBytes=await fs.readFile(sourceFile),meta=await sharp(sourceBytes).metadata();
 if(meta.width/meta.height!==4/3)throw Error('Edit sheet changed aspect ratio');
 const patch=await sharp(sourceBytes).resize(256,192,{kernel:'nearest'}).ensureAlpha().raw().toBuffer();
 for(let at=0;at<patch.length;at+=4){if(patch[at+3]<160)patch.fill(0,at,at+4);else patch.set([...nearest(patch.subarray(at,at+3)),255],at);}
 await sharp(patch,{raw:{width:256,height:192,channels:4}}).png().toFile(path.join(ROOT,'source/walk_down_left_joint_edit_quantized_v011.png'));
 const frames=[],records=[],maskFrames=[];
 for(let i=0;i<8;i++){
   const stem=String(i).padStart(2,'0'),name=`robot_walk_${direction}_f${stem}_v011.png`;
   const original=await sharp(path.join(pilot,name)).ensureAlpha().raw().toBuffer();
   const state=ledger.states[i],protectedPixels=render(protectedParts,rig,state),armorMask=render(armorParts,rig,state),regions=[];
   for(const[id,j]of Object.entries(state.joints)){
     if(id.startsWith('leg'))regions.push({id:id+'_hip',center:j.root,rx:3.4,ry:3.4},{id:id+'_knee',center:j.joint,rx:4.8,ry:5.6},{id:id+'_ankle',center:j.ankle,rx:4,ry:3.5});
     else regions.push({id:id+'_shoulder',center:j.root,rx:3.4,ry:3.4},{id:id+'_elbow',center:j.joint,rx:3.5,ry:4});
   }
   const output=Buffer.from(original),mask=Buffer.alloc(W*H*4),changes=[];
   for(let y=0;y<H;y++)for(let x=0;x<W;x++){
     const at=(y*W+x)*4,s=(((i>>2)*H+y)*256+(i%4)*W+x)*4;
     const selected=regions.filter(r=>((x+.5-r.center[0])/r.rx)**2+((y+.5-r.center[1])/r.ry)**2<=1);
     if(!selected.length||protectedPixels[at+3]||y<=46)continue;
     mask.set([255,255,255,255],at);patch.copy(output,at,s,s+4);
     if(!original.subarray(at,at+4).equals(output.subarray(at,at+4)))changes.push({xy:[x,y],regions:selected.map(r=>r.id),before:[...original.subarray(at,at+4)],after:[...output.subarray(at,at+4)]});
   }
   let protectedDiff=0,outsideDiff=0,armorDiff=0,restoredArmor=0,nonArmorRevision=0;
   const rc01=await sharp(path.join(ROOT,'source/reference-phase-a-rc01/frames',name)).ensureAlpha().raw().toBuffer();
   for(let at=0;at<output.length;at+=4)if(!output.subarray(at,at+4).equals(original.subarray(at,at+4))){if(protectedPixels[at+3])protectedDiff++;if(!mask[at+3])outsideDiff++;}
   for(let at=0;at<output.length;at+=4){
     if(armorMask[at+3]&&!output.subarray(at,at+4).equals(original.subarray(at,at+4)))armorDiff++;
     if(!output.subarray(at,at+4).equals(rc01.subarray(at,at+4))){if(armorMask[at+3])restoredArmor++;else nonArmorRevision++;}
   }
   if(protectedDiff||outsideDiff||armorDiff||nonArmorRevision)throw Error('Revision changed pixels outside the fixed armor correction');
   await png(output,path.join(ROOT,'frames/walk',direction,name));await png(mask,path.join(ROOT,`qa/${direction}_joint_patch_mask_f${stem}.png`));
   await png(armorMask,path.join(ROOT,`qa/${direction}_rigid_armor_mask_f${stem}.png`));
   frames.push(output);maskFrames.push(mask);records.push({frame:i,regions,changes,changed_pixels:changes.length,protected_pixels_changed:protectedDiff,outside_mask_changed:outsideDiff,rigid_armor_pixels_changed_from_fixed_rig:armorDiff,restored_armor_pixels_from_rc01:restoredArmor,non_armor_pixels_changed_from_rc01:nonArmorRevision,output_sha256:sha(await fs.readFile(path.join(ROOT,'frames/walk',direction,name)))});
 }
 for(const scale of [1,4])for(const[name,bg]of [['light',[236,233,216]],['dark',[24,38,49]],['transparent',null]])await contact(frames,path.join(ROOT,`previews/walk_${direction}_${name}_${scale}x_v011.png`),scale,bg);
 await contact(maskFrames,path.join(ROOT,`qa/${direction}_joint_patch_masks_4x.png`),4,[24,38,49]);
 await fs.writeFile(path.join(ROOT,`qa/${direction}_joint_patch_v011.json`),JSON.stringify({status:'PHASE_A_RC02_P2_REPAIR_CANDIDATE',source_file:path.relative(ROOT,sourceFile),source_sha256:sha(sourceBytes),source_size:[meta.width,meta.height],common_sheet_transform:[256/meta.width,192/meta.height],no_per_frame_bbox_fit:true,protected:['body','rigid_boots','hands','left_wrist_tool','far_anatomical_right_thigh_armor_and_contour'],rigid_armor_rule:rigidArmor,records},null,2)+'\n');
 console.log(JSON.stringify(records.map(r=>({frame:r.frame,changed:r.changed_pixels,restoredArmor:r.restored_armor_pixels_from_rc01,armorDiff:r.rigid_armor_pixels_changed_from_fixed_rig,nonArmorRevision:r.non_armor_pixels_changed_from_rc01}))));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
