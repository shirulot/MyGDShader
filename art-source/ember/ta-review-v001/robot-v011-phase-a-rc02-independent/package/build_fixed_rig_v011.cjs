// 从同一 AI 母稿提取固定部件，用二维骨骼排姿；不绘制或补造角色像素。
// 每个方向只登记一次分区和支点。动作改变部件变换，不逐帧裁 bbox、改比例或重心。
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const sharp = require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const ROOT = __dirname, W = 64, H = 96;
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const add = (a,b) => [a[0]+b[0],a[1]+b[1]];
const sub = (a,b) => [a[0]-b[0],a[1]-b[1]];
const mul = (a,b) => [a[0]*b,a[1]*b];
const len = a => Math.hypot(...a);
const angle = a => Math.atan2(a[1],a[0]);
const rotate = (v,a) => [v[0]*Math.cos(a)-v[1]*Math.sin(a),v[0]*Math.sin(a)+v[1]*Math.cos(a)];
const inside = (x,y,poly) => {
  let hit=false;
  for(let i=0,j=poly.length-1;i<poly.length;j=i++) {
    const a=poly[i],b=poly[j];
    if((a[1]>y)!==(b[1]>y) && x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]) hit=!hit;
  }
  return hit;
};

// 多边形边界按母图像素登记，LEFT / RIGHT 均指解剖学一侧。
// SW 的左侧靠近相机，工具随该前臂始终保持同源。
const rigs = {
  down_left: {
    forward: [-1,0.34],
    limb_order: ['arm_right','leg_right','leg_left','body','arm_left'],
    limbs: {
      arm_right: {kind:'arm',side:'right',root:[19,47],joint:[18,52],end:[18,58],bend:-1,
        polygon:[[17,47],[21,47],[22,51],[21,55],[21,63],[14,63],[14,50]], split:[52,58],end_part:false},
      arm_left: {kind:'arm',side:'left',root:[40,47],joint:[41,52],end:[41,58],bend:1,
        polygon:[[37,47],[43,47],[47,54],[47,63],[37,63],[37,54],[36,52]], split:[52,58],end_part:false},
      leg_right: {kind:'leg',side:'right',root:[24,56],joint:[24.5,64.5],end:[25,70.5],bend:1,
        polygon:[[21,54],[27,54],[28,59],[31,62],[31,75],[30,75],[30,80],[16,80],[16,70],[20,64],[21,63]], split:[64.5,70.5],end_part:true},
      leg_left: {kind:'leg',side:'left',root:[34,56],joint:[35,65.5],end:[36,70.5],bend:1,
        polygon:[[31,54],[37,54],[37,63],[41,63],[42,71],[42,81],[30,81],[30,75],[31,75],[31,63]], split:[65.5,70.5],end_part:true}
    }
  }
};

function rigid(sourcePivot,targetPivot,radians=0) {
  return {sourcePivot,targetPivot,radians};
}
function transformPoint(p,t) {return add(t.targetPivot,rotate(sub(p,t.sourcePivot),t.radians));}
function matrixBetween(a,b,ta,tb) {return rigid(a,ta,angle(sub(tb,ta))-angle(sub(b,a)));}

// 两段骨骼保持原长度。足靴独立保持平底；不能用缩短腿长伪造可达目标。
function solveTwoBone(root,target,l1,l2,bend) {
  const v=sub(target,root),d=len(v),bounded=Math.min(l1+l2-0.0001,Math.max(Math.abs(l1-l2)+0.0001,d));
  const axis=mul(v,1/(d||1)),along=(l1*l1-l2*l2+bounded*bounded)/(2*bounded);
  const off=Math.sqrt(Math.max(0,l1*l1-along*along));
  return {joint:add(add(root,mul(axis,along)),mul([-axis[1],axis[0]],off*bend)),
    target:add(root,mul(axis,bounded)),clamped:Math.abs(d-bounded)>0.01,requestedDistance:d,boneReach:l1+l2};
}

// 源片最近邻反向采样。RGBA 直接来自母图，输出保持 11 色与二值 alpha。
function stamp(out,part,t) {
  const c=Math.cos(t.radians),s=Math.sin(t.radians);
  for(let y=0;y<H;y++)for(let x=0;x<W;x++) {
    const dx=x+.5-t.targetPivot[0],dy=y+.5-t.targetPivot[1];
    const sx=Math.floor(dx*c+dy*s+t.sourcePivot[0]);
    const sy=Math.floor(-dx*s+dy*c+t.sourcePivot[1]);
    if(sx<0||sx>=W||sy<0||sy>=H)continue;
    const at=(sy*W+sx)*4, dest=(y*W+x)*4;
    if(part[at+3])part.copy(out,dest,at,at+4);
  }
}

function extractParts(source,rig) {
  const body=Buffer.from(source),parts={body},owners=Array(W*H).fill('body');
  // 先确定每个实际可见像素所属的肢体，避免近侧前臂带走大腿等无关像素。
  for(let y=0;y<H;y++)for(let x=0;x<W;x++) {
    if(!source[(y*W+x)*4+3])continue;
    const hits=Object.entries(rig.limbs).filter(([,l])=>inside(x+.5,y+.5,l.polygon));
    if(hits.length>1)throw Error(`Ambiguous source ownership at ${x},${y}: ${hits.map(h=>h[0])}`);
    if(hits.length){owners[y*W+x]=hits[0][0];body.fill(0,(y*W+x)*4,(y*W+x)*4+4);}
  }
  for(const[id,l]of Object.entries(rig.limbs)){
    for(const segment of ['upper','lower',...(l.end_part?['end']:[])])parts[id+'_'+segment]=Buffer.alloc(W*H*4);
    for(let y=0;y<H;y++)for(let x=0;x<W;x++){
      if(owners[y*W+x]!==id)continue;
      const at=(y*W+x)*4;
      // 关节处保留同源重叠区；不是另画细线或不透明胶囊补连接。
      if(y<l.split[0]+2)source.copy(parts[id+'_upper'],at,at,at+4);
      if(y>=l.split[0]-2 && (!l.end_part||y<l.split[1]+0.5))source.copy(parts[id+'_lower'],at,at,at+4);
      if(l.end_part&&y>=l.split[1]-0.5)source.copy(parts[id+'_end'],at,at,at+4);
    }
  }
  return {parts,owners};
}

function pose(rig,frame,neutral=false) {
  const phase=[1,0.6,0,-0.6,-1,-0.6,0,0.6];
  const lift=[0,0,0,0,0,0.5,1.1,0.7];
  const bob=neutral?0:[0.7,1.0,0.6,0.4,0.7,1.0,0.6,0.4][frame];
  const body=rigid([32,56],[32,56+bob]);
  const transforms={body},joints={},notes=[];
  for(const[id,l]of Object.entries(rig.limbs)){
    const root=transformPoint(l.root,body);
    if(neutral) {
      transforms[id+'_upper']=rigid(l.root,l.root);
      transforms[id+'_lower']=rigid(l.joint,l.joint);
      if(l.end_part)transforms[id+'_end']=rigid(l.end,l.end);
      continue;
    }
    const k=(frame+(l.side==='left'?0:4))%8;
    if(l.kind==='leg'){
      const requested=add(l.end,[rig.forward[0]*2.0*phase[k],rig.forward[1]*1.5*phase[k]-lift[k]]);
      const solved=solveTwoBone(root,requested,len(sub(l.joint,l.root)),len(sub(l.end,l.joint)),l.bend);
      transforms[id+'_upper']=matrixBetween(l.root,l.joint,root,solved.joint);
      transforms[id+'_lower']=matrixBetween(l.joint,l.end,solved.joint,solved.target);
      transforms[id+'_end']=rigid(l.end,solved.target,0);
      joints[id]={root,joint:solved.joint,ankle:solved.target,requested,lift:lift[k],contact:lift[k]===0};
      if(solved.clamped)notes.push({limb:id,reason:'IK_TARGET_OUT_OF_REACH',...solved});
    }else{
      const a=-phase[k]*0.25;
      const elbow=add(root,rotate(sub(l.joint,l.root),a));
      const wrist=add(elbow,rotate(sub(l.end,l.joint),a*0.65));
      transforms[id+'_upper']=matrixBetween(l.root,l.joint,root,elbow);
      transforms[id+'_lower']=matrixBetween(l.joint,l.end,elbow,wrist);
      joints[id]={root,joint:elbow,wrist};
    }
  }
  return {transforms,joints,notes,bob};
}

function render(parts,rig,state){
  const out=Buffer.alloc(W*H*4);
  for(const id of rig.limb_order){
    if(id==='body'){stamp(out,parts.body,state.transforms.body);continue;}
    // 同一关节较下层先画，甲片由上层承接；末端靴子保持自己的刚性变换。
    for(const segment of ['end','lower','upper'])if(parts[id+'_'+segment])stamp(out,parts[id+'_'+segment],state.transforms[id+'_'+segment]);
  }
  return out;
}

async function png(raw,file,scale=1){await fs.mkdir(path.dirname(file),{recursive:true});await sharp(raw,{raw:{width:W,height:H,channels:4}}).resize(W*scale,H*scale,{kernel:'nearest'}).png().toFile(file);}
async function contact(frames,file,scale=4,bg=[236,233,216],columns=4){
  const ww=W*columns,hh=H*Math.ceil(frames.length/columns),out=Buffer.alloc(ww*hh*4);
  for(let y=0;y<hh;y++)for(let x=0;x<ww;x++)if(bg)out.set([...bg,255],(y*ww+x)*4);
  frames.forEach((frame,i)=>{for(let y=0;y<H;y++)for(let x=0;x<W;x++){const at=(y*W+x)*4;if(frame[at+3])frame.copy(out,((Math.floor(i/columns)*H+y)*ww+i%columns*W+x)*4,at,at+4);}});
  await fs.mkdir(path.dirname(file),{recursive:true});await sharp(out,{raw:{width:ww,height:hh,channels:4}}).resize(ww*scale,hh*scale,{kernel:'nearest'}).png().toFile(file);
}

async function run(){
  const direction=process.argv[2]||'down_left',rig=rigs[direction];
  if(!rig)throw Error('Direction rig not yet authored: '+direction);
  const sourceFile=path.join(ROOT,`source/candidate-masters/robot_idle_${direction}_v011.png`);
  const sourceBytes=await fs.readFile(sourceFile),source=await sharp(sourceBytes).ensureAlpha().raw().toBuffer();
  const {parts,owners}=extractParts(source,rig),partEntries=[];
  for(const[id,raw]of Object.entries(parts)){
    const file=`source/fixed-parts/${direction}/${id}.png`;
    await png(raw,path.join(ROOT,file));partEntries.push({id,file,raw_sha256:sha(raw),source_pixels:owners.filter(o=>o===id.replace(/_(upper|lower|end)$/,'')).length});
  }
  const neutral=render(parts,rig,pose(rig,0,true));
  let neutralMismatch=0;for(let i=0;i<source.length;i+=4)if(!source.subarray(i,i+4).equals(neutral.subarray(i,i+4)))neutralMismatch++;
  await png(neutral,path.join(ROOT,`qa/${direction}_neutral_reassembly_8x.png`),8);
  if(neutralMismatch)throw Error(`Neutral reassembly differs at ${neutralMismatch} pixels`);
  const frames=[],states=[],entries=[];
  for(let i=0;i<8;i++){
    const state=pose(rig,i),frame=render(parts,rig,state),file=`frames/walk/${direction}/robot_walk_${direction}_f${String(i).padStart(2,'0')}_v011.png`;
    await png(frame,path.join(ROOT,file));frames.push(frame);states.push(state);entries.push({frame:i,file,raw_sha256:sha(frame)});
  }
  for(const scale of [1,4])for(const[name,bg]of [['light',[236,233,216]],['dark',[24,38,49]],['transparent',null]])await contact(frames,path.join(ROOT,`previews/walk_${direction}_${name}_${scale}x_v011.png`),scale,bg);
  await contact(Object.values(parts),path.join(ROOT,`qa/${direction}_fixed_parts_4x.png`),4,[88,103,113]);
  const report={status:'PILOT_UNREVIEWED',direction,canvas:[W,H],root:[32,80],fps:8,loop:true,source_file:path.relative(ROOT,sourceFile),source_sha256:sha(sourceBytes),rig,neutral_reassembly_pixel_mismatch:neutralMismatch,parts:partEntries,frames:entries,states};
  await fs.writeFile(path.join(ROOT,`qa/${direction}_fixed_rig_v011.json`),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({direction,neutralMismatch,parts:partEntries.length,frames:entries.length,ikWarnings:states.flatMap(s=>s.notes)}));
}
module.exports={rigs,extractParts,pose,render,stamp,contact,png};
if(require.main===module)run().catch(e=>{console.error(e);process.exitCode=1;});
