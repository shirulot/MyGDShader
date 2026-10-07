// W/E 侧向：将一次生成的完整隐藏肢体登记到母版，保留母版可见像素，再排八帧。
// 这里只裁切/登记/遮挡/刚性排姿已有图像；不绘制补造关节，不做逐帧bbox归一化。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {render,pose,contact,png}=require('./build_fixed_rig_v011.cjs');
const {poseForDirection}=require('./build_remaining_walk_v011.cjs');
const root=__dirname,W=64,H=96,sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const palette=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A'].map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
const nearest=p=>palette.reduce((best,c)=>{const d=c.reduce((s,v,i)=>s+(v-p[i])**2,0);return d<best.d?{d,c}:best;},{d:Infinity,c:palette[0]}).c;
const limb=(kind,side,r,j,e,bend)=>({kind,side,root:r,joint:j,end:e,bend,split:[j[1],e[1]],end_part:kind==='leg'});
const rigs={
 left:{forward:[-1,0],limb_order:['arm_right','leg_right','leg_left','body','arm_left'],limbs:{
  arm_left:limb('arm','left',[31,47],[31,53],[28,60],1),arm_right:limb('arm','right',[27,45],[26,51],[26,58],-1),
  leg_left:limb('leg','left',[29,55],[29,65],[29,72],1),leg_right:limb('leg','right',[32,55],[32,64.5],[32,71],1)}},
 right:{forward:[1,0],limb_order:['arm_left','leg_left','leg_right','body','arm_right'],limbs:{
  arm_right:limb('arm','right',[28,47],[28,53],[31,60],-1),arm_left:limb('arm','left',[34,45],[35,51],[35,58],1),
  leg_right:limb('leg','right',[31,55],[31,65],[31,72],-1),leg_left:limb('leg','left',[28,55],[28,64.5],[28,71],-1)}}
};
const nearArmPolys={left:[[28,47],[37,47],[37,61],[33,64],[23,64],[22,61],[22,56],[27,53]],right:[[23,47],[31,47],[32,51],[38,54],[38,64],[24,64],[24,59],[22,55]]};
const inPoly=(x,y,poly)=>{let hit=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;};
const registration={left:[{id:'leg_left',column:0,height:26,xy:[23,54]},{id:'leg_right',column:1,height:26,xy:[26,54]},{id:'arm_right',column:2,height:20,xy:[23,44]}],right:[{id:'leg_right',column:0,height:26,xy:[25,54]},{id:'leg_left',column:1,height:26,xy:[22,54]},{id:'arm_left',column:2,height:20,xy:[30,44]}]};

async function registerHidden(direction,mother,owners){
 const file='source/side_hidden_parts_raw_v011.png',bytes=await fs.readFile(path.join(root,file)),meta=await sharp(bytes).metadata(),raw=await sharp(bytes).ensureAlpha().raw().toBuffer();
 const row=direction==='left'?0:1,registered={},records=[];
 for(const spec of registration[direction]){
  const x0=Math.floor(meta.width*spec.column/3),x1=Math.floor(meta.width*(spec.column+1)/3),y0=Math.floor(meta.height*row/2),y1=Math.floor(meta.height*(row+1)/2);
  let bx0=x1,bx1=-1,by0=y1,by1=-1;
  // 仅用于固定源的一次登记。后续所有动画帧直接复用这份登记结果。
  for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++)if(raw[(y*meta.width+x)*4+3]>=160){bx0=Math.min(bx0,x);bx1=Math.max(bx1,x);by0=Math.min(by0,y);by1=Math.max(by1,y);}
  if(bx1<0)throw Error('Empty hidden source cell');
  const crop={left:bx0,top:by0,width:bx1-bx0+1,height:by1-by0+1},height=spec.height,width=Math.round(crop.width*height/crop.height);
  const small=await sharp(bytes).extract(crop).resize(width,height,{kernel:'nearest'}).ensureAlpha().raw().toBuffer(),part=Buffer.alloc(W*H*4);
  let removedOutsideMother=0,removedNearOverFar=0;
  for(let y=0;y<height;y++)for(let x=0;x<width;x++){
   const at=(y*width+x)*4,dx=x+spec.xy[0],dy=y+spec.xy[1],dest=(dy*W+dx)*4;
   if(small[at+3]<160)continue;
   if(!mother[dest+3]){removedOutsideMother++;continue;}
   const nearLeg=direction==='left'?'leg_left':'leg_right',farLeg=direction==='left'?'leg_right':'leg_left';
   if(spec.id===nearLeg&&owners[dy*W+dx]===farLeg){removedNearOverFar++;continue;}
   part.set([...nearest(small.subarray(at,at+3)),255],dest);
  }
  registered[spec.id]=part;
  const output=`source/registered-hidden-parts/${direction}/${spec.id}.png`;await png(part,path.join(root,output));
  records.push({...spec,source_crop:crop,registered_size:[width,height],registered_file:output,removed_outside_neutral_silhouette:removedOutsideMother,removed_near_over_far_visible_pixels:removedNearOverFar,raw_sha256:sha(part)});
 }
 return{registered,registration:{source_file:file,source_sha256:sha(bytes),source_size:[meta.width,meta.height],direction,one_time_source_registration:true,no_per_frame_bbox_fit:true,parts:records}};
}

async function build(direction){
 const rig=rigs[direction];if(!rig)throw Error('Only W/E are handled by this builder');
 const file=`source/candidate-masters/robot_idle_${direction}_v011.png`,bytes=await fs.readFile(path.join(root,file)),source=await sharp(bytes).ensureAlpha().raw().toBuffer();
 const nearSide=direction==='left'?'left':'right',farSide=direction==='left'?'right':'left',nearArm='arm_'+nearSide,nearLeg='leg_'+nearSide,farLeg='leg_'+farSide;
 const owners=Array(W*H).fill('body'),body=Buffer.from(source);
 for(let y=0;y<H;y++)for(let x=0;x<W;x++)if(source[(y*W+x)*4+3]){
  let owner='body';
  if(y>=64)owner=(direction==='left'?x>=34&&y>=70:x<=27&&y>=69)?farLeg:nearLeg;
  else if(inPoly(x+.5,y+.5,nearArmPolys[direction]))owner=nearArm;
  owners[y*W+x]=owner;if(owner!=='body')body.fill(0,(y*W+x)*4,(y*W+x)*4+4);
 }
 const hidden=await registerHidden(direction,source,owners),whole={};
 for(const id of Object.keys(rig.limbs))whole[id]=hidden.registered[id]?Buffer.from(hidden.registered[id]):Buffer.alloc(source.length);
 // 原母版实际可见像素是上层来源；隐藏图只补原先被遮挡的区域。
 for(let p=0;p<owners.length;p++)if(owners[p]!=='body'&&source[p*4+3])source.copy(whole[owners[p]],p*4,p*4,p*4+4);
 const parts={body};
 for(const[id,l]of Object.entries(rig.limbs)){
  for(const segment of['upper','lower',...(l.end_part?['end']:[])])parts[id+'_'+segment]=Buffer.alloc(source.length);
  for(let y=0;y<H;y++)for(let x=0;x<W;x++){
   const at=(y*W+x)*4;if(!whole[id][at+3])continue;
   if(y<l.joint[1]+2)whole[id].copy(parts[id+'_upper'],at,at,at+4);
   if(y>=l.joint[1]-2&&(!l.end_part||y<l.end[1]+.5))whole[id].copy(parts[id+'_lower'],at,at,at+4);
   if(l.end_part&&y>=l.end[1]-.5)whole[id].copy(parts[id+'_end'],at,at,at+4);
  }
 }
 const neutral=render(parts,rig,pose(rig,0,true));let neutralDiff=0;
 for(let at=0;at<source.length;at+=4)if(!source.subarray(at,at+4).equals(neutral.subarray(at,at+4)))neutralDiff++;
 await png(neutral,path.join(root,`qa/${direction}_neutral_reassembly_8x.png`),8);
 if(neutralDiff)throw Error('Side neutral changed '+neutralDiff+' original pixels');
 const partEntries=[];for(const[id,raw]of Object.entries(parts)){
  const file=`source/fixed-parts/${direction}/${id}.png`;await png(raw,path.join(root,file));partEntries.push({id,file,raw_sha256:sha(raw)});
 }
 const frames=[],states=[],entries=[];
 for(let i=0;i<8;i++){
  const state=poseForDirection(rig,i),raw=render(parts,rig,state),name=`robot_walk_${direction}_f${String(i).padStart(2,'0')}_v011.png`,file=`source/fixed-rig-pilot/${direction}/${name}`;
  if(state.notes.length)throw Error('Side IK is not reachable: '+JSON.stringify(state.notes));
  await png(raw,path.join(root,file));await png(raw,path.join(root,'frames/walk',direction,name));frames.push(raw);states.push(state);entries.push({frame:i,file,raw_sha256:sha(raw)});
 }
 const report={status:'RAW_SIDE_RIG_NOT_ART_ACCEPTED',direction,canvas:[W,H],root:[32,80],fps:8,loop:true,source_file:file,source_sha256:sha(bytes),hidden_source_registration:hidden.registration,rig,near_arm_ownership_polygon:nearArmPolys[direction],neutral_reassembly_pixel_mismatch:neutralDiff,body_pixels_below_y64:[],parts:partEntries,frames:entries,states};
 const pilot=path.join(root,'source/fixed-rig-pilot',direction);await fs.writeFile(path.join(pilot,'rig_and_poses.json'),JSON.stringify(report,null,2)+'\n');
 await fs.writeFile(path.join(root,`qa/${direction}_fixed_rig_v011.json`),JSON.stringify(report,null,2)+'\n');
 await contact(frames,path.join(pilot,'edit_target_4x.png'),4,null);await contact(frames,path.join(root,`qa/${direction}_raw_walk_4x.png`),4,[236,233,216]);
 await contact(Object.values(parts),path.join(root,`qa/${direction}_fixed_parts_4x.png`),4,[88,103,113]);
 return{direction,neutralDiff,parts:partEntries.length,frames:frames.length,registration:hidden.registration.parts};
}
module.exports={rigs,build};
if(require.main===module)(async()=>{for(const d of process.argv.slice(2))console.log(JSON.stringify(await build(d)));})().catch(e=>{console.error(e);process.exitCode=1;});
