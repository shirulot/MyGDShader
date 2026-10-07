// 可编辑二维绑定：所有帧复用同一组纹理，骨长、关节端点与root显式登记。
const rig={root:[32,80],head:{width:19,height:20},torso:{width:23,height:27},
  thighLength:12,shinLength:11,upperArmLength:9,forearmLength:12,
  stride:12,depthRatio:.35,walkDuration:960,frameCount:8};
const sources={},names=['head','torso','near_upper_arm','near_forearm','far_upper_arm','far_forearm','near_thigh','far_thigh','near_shin','far_shin','near_boot','far_boot'];
let mode='walk',time=0,last=0,paused=false,showBones=false,light=false;
const $=id=>document.getElementById(id);
function add(a,b){return[a[0]+b[0],a[1]+b[1]]}
// 支撑相脚相对身体线性后移，叠加+24px/周期的世界位移后接触点恒定。
function footPath(phase){phase=(phase+1)%1;let x,z=0;
  if(phase<.5)x=6-24*phase;
  else{const u=(phase-.5)*2,u2=u*u,u3=u2*u;
    x=-6*(2*u3-3*u2+1)-12*(u3-2*u2+u)+6*(-2*u3+3*u2)-12*(u3-u2);
    z=6*Math.sin(Math.PI*u);}
  return {x,y:x*rig.depthRatio-z,support:phase<.5};
}
// 二骨IK取朝屏幕右侧的弯膝解，接近伸直仍保持同一分支，不允许膝反折。
function knee(hip,ankle){const dx=ankle[0]-hip[0],dy=ankle[1]-hip[1];
  const raw=Math.hypot(dx,dy),d=Math.max(.01,Math.min(raw,rig.thighLength+rig.shinLength-.01));
  const a=(rig.thighLength**2-rig.shinLength**2+d*d)/(2*d),h=Math.sqrt(Math.max(0,rig.thighLength**2-a*a));
  return [hip[0]+dx/raw*a+dy/raw*h,hip[1]+dy/raw*a-dx/raw*h];
}
function pose(frame,action){const phase=frame/8,bob=action==='walk'?2+[0,.6,0,-.6][frame%4]:[0,0,0,0,0,0,0,0][frame];
  const p={head:[32,23+bob],torso:[32,42+bob],root:rig.root,phase};
  for(const [side,offset] of [['near',0],['far',.5]]){
    const path=action==='walk'?footPath(phase+offset):{x:0,y:0,support:true};
    const near=side==='near';const hip=[near?28:36,(near?52:50)+bob];
    const ankle=[(near?28:36)+path.x,(near?75:73)-(action==='walk'?1:0)+path.y];
    const shoulder=[near?24:40,(near?34:33)+bob];
    const swing=action==='walk'?-path.x*.055:0;
    const elbow=[shoulder[0]+Math.sin(swing)*rig.upperArmLength,shoulder[1]+Math.cos(swing)*rig.upperArmLength];
    const wrist=[elbow[0]+Math.sin(swing-.1)*rig.forearmLength,elbow[1]+Math.cos(swing-.1)*rig.forearmLength];
    p[side]={hip,knee:knee(hip,ankle),ankle,shoulder,elbow,wrist,support:path.support};
  }return p;
}
// 生图把膝甲同时画在大腿和小腿；绑定源只取小腿下段，膝甲由大腿唯一拥有。
// 这里登记静态纹理区域，所有帧完全共用，不逐帧变更裁片。
const textureRegions={near_shin:[0,.34,1,.66],far_shin:[0,.34,1,.66],near_boot:[0,.12,1,.88],far_boot:[0,.12,1,.88]};
function blit(ctx,name,x,y,w,h,angle=0,pivot=.5){const im=sources[name],r=textureRegions[name]||[0,0,1,1];ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.drawImage(im,r[0]*im.width,r[1]*im.height,r[2]*im.width,r[3]*im.height,-w/2,-h*pivot,w,h);ctx.restore();}
function bone(ctx,name,a,b,width,overlap=2){const len=Math.hypot(b[0]-a[0],b[1]-a[1]);
  const angle=Math.atan2(b[1]-a[1],b[0]-a[0])-Math.PI/2;
  // 上下圆帽覆盖连接区；贴图长度仅根据固定骨段绘制，关节不会脱离端点。
  blit(ctx,name,a[0],a[1],width,len+overlap*2,angle,overlap/(len+overlap*2));
}
function drawRig(ctx,p,ox=0,oy=0,debug=false){ctx.save();ctx.translate(ox,oy);ctx.imageSmoothingEnabled=false;
  for(const side of ['far','near']){const q=p[side];
    blit(ctx,side+'_boot',q.ankle[0]+1,q.ankle[1]+2,10,7);
    bone(ctx,side+'_shin',q.knee,q.ankle,side==='near'?8:7,2);
    bone(ctx,side+'_thigh',q.hip,q.knee,side==='near'?9:8,2);}
  const f=p.far;bone(ctx,'far_upper_arm',f.shoulder,f.elbow,6,2);bone(ctx,'far_forearm',f.elbow,f.wrist,6,2);
  blit(ctx,'torso',p.torso[0],p.torso[1],rig.torso.width,rig.torso.height);
  const n=p.near;bone(ctx,'near_upper_arm',n.shoulder,n.elbow,7,2);bone(ctx,'near_forearm',n.elbow,n.wrist,7,2);
  blit(ctx,'head',p.head[0],p.head[1],rig.head.width,rig.head.height);
  if(debug){ctx.lineWidth=.45;for(const side of ['far','near']){ctx.strokeStyle=side==='near'?'#ffcc66':'#51c5c2';const q=p[side];for(const chain of [[q.hip,q.knee,q.ankle],[q.shoulder,q.elbow,q.wrist]]){ctx.beginPath();chain.forEach((v,i)=>i?ctx.lineTo(...v):ctx.moveTo(...v));ctx.stroke();for(const v of chain){ctx.beginPath();ctx.arc(...v,1,0,Math.PI*2);ctx.stroke();}}}}
  ctx.restore();
}
// 导出时统一量化；阈值和18色表全帧一致，不移动像素坐标，不做逐帧修形。
const palette=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','ECE9D8','7B4D35','B77C4B','E2B77A','B9947B','D7B59B','EAC5A0','3A3436','635754','9B8170','F2D9B8','AAB7B1'].map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
function quantize(ctx){const im=ctx.getImageData(0,0,64,96),d=im.data;
  for(let i=0;i<d.length;i+=4){if(d[i+3]<128){d[i]=d[i+1]=d[i+2]=d[i+3]=0;continue;}
    let best=palette[0],distance=Infinity;for(const color of palette){const diff=(d[i]-color[0])**2+(d[i+1]-color[1])**2+(d[i+2]-color[2])**2;if(diff<distance){distance=diff;best=color;}}
    d[i]=best[0];d[i+1]=best[1];d[i+2]=best[2];d[i+3]=255;}
  ctx.putImageData(im,0,0);}
function frameCanvas(p,debug=false){const c=document.createElement('canvas');c.width=64;c.height=96;drawRig(c.getContext('2d'),p,0,0,debug);if(!debug)quantize(c.getContext('2d'));return c;}
function draw(){const frame=Math.floor(time/120)%8,p=pose(frame,mode),canvas=$('stage'),ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.fillStyle=light?'#d4d9d4':'#182631';ctx.fillRect(0,0,384,384);ctx.strokeStyle='#4d6470';ctx.beginPath();ctx.moveTo(192,0);ctx.lineTo(192,384);ctx.moveTo(0,320);ctx.lineTo(384,320);ctx.stroke();ctx.drawImage(frameCanvas(p,showBones),64,0,256,384);$('state').textContent=`F${frame} · ${Math.floor(time/960)} 周期 · 近腿 ${p.near.support?'支撑':'摆动'} / 远腿 ${p.far.support?'支撑':'摆动'}`;
  // 接触验证用同相位加世界位移；背景随固定速度反向移动，标记支撑足世界轨迹。
  const world=$('world'),w=world.getContext('2d');w.imageSmoothingEnabled=false;w.fillStyle=light?'#d4d9d4':'#182631';w.fillRect(0,0,768,384);
  const progress=(time%3840)/960,wx=progress*24,wy=wx*.35;w.strokeStyle='#344c57';for(let x=-96;x<250;x+=16){w.beginPath();w.moveTo((x-wx)*4,0);w.lineTo((x-wx)*4,384);w.stroke();}for(let y=-20;y<150;y+=16){w.beginPath();w.moveTo(0,(y-wy)*4);w.lineTo(768,(y-wy)*4);w.stroke();}w.drawImage(frameCanvas(p,showBones),256,0,256,384);
  window.currentRigFrame=p;
}
function exportSheet(){const canvas=document.createElement('canvas');canvas.width=512;canvas.height=96;const c=canvas.getContext('2d');for(let i=0;i<8;i++)c.drawImage(frameCanvas(pose(i,mode)),i*64,0);$('sheet').src=canvas.toDataURL('image/png');const a=document.createElement('a');a.download=`A-${mode}-down_right-rig-v006.png`;a.href=canvas.toDataURL('image/png');$('download').href=a.href;$('download').download=a.download;}
function tick(t){if(last&&!paused)time+=t-last;last=t;draw();requestAnimationFrame(tick)}
Promise.all(names.map(name=>new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>{sources[name]=i;resolve()};i.onerror=reject;i.src=`parts/${name}.png`;}))).then(()=>{exportSheet();requestAnimationFrame(tick)}).catch(()=>$('state').textContent='分件加载失败');
$('action').onchange=e=>{mode=e.target.value;time=0;$('export').disabled=mode!=='walk';};$('pause').onclick=()=>{paused=!paused;$('pause').textContent=paused?'继续':'暂停';};$('step').onclick=()=>{paused=true;time=(Math.floor(time/120)+1)*120;$('pause').textContent='继续';draw();};$('bones').onclick=()=>{showBones=!showBones;};$('bg').onclick=()=>{light=!light;};$('export').onclick=exportSheet;
