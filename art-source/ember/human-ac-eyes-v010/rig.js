// 可编辑二维绑定：所有帧复用同一组纹理，骨长、关节端点与root显式登记。
const rig={root:[32,80],head:{width:19,height:20},torso:{width:23,height:27},
  thighLength:12,shinLength:11,upperArmLength:9,forearmLength:11,
  stride:10,lift:1.5,projection:{forwardX:.65,forwardY:.23,vertical:.96},
  walkDuration:960,frameCount:8};
const sources={},nativeParts={},names=['head','torso','near_upper_arm','near_forearm','far_upper_arm','far_forearm','near_thigh','far_thigh','near_shin','far_shin','near_boot','far_boot'];
let mode='walk',time=0,last=0,paused=false,showBones=false,light=false,speed=1;
const beforeSheet=new Image();beforeSheet.src='../human-ac-body-eyes-v009/final/A-walk-down_right-body-eyes-v009.png';
const $=id=>document.getElementById(id);
function add(a,b){return[a[0]+b[0],a[1]+b[1]]}
// 每条腿在角色前后方向的矢状平面内求解，再投影到画布。
// 固定的是空间骨长，二维投影长度允许随朝向缩短，不能强锁屏幕骨长。
function footPath(phase){phase=(phase+1)%1;const half=rig.stride/2;let forward,lift=0;
  if(phase<.5)forward=half-2*rig.stride*phase;
  else{const u=(phase-.5)*2,u2=u*u,u3=u2*u;
    forward=-half*(2*u3-3*u2+1)-rig.stride*(u3-2*u2+u)+half*(-2*u3+3*u2)-rig.stride*(u3-u2);
    lift=rig.lift*Math.sin(Math.PI*u)**2;}
  return {forward,lift,support:phase<.5,phase};
}
function project(point,origin){return [origin[0]+point[0]*rig.projection.forwardX,
  origin[1]+point[0]*rig.projection.forwardY+point[1]*rig.projection.vertical];}
function kneeInPlane(ankle){const [x,y]=ankle,d=Math.hypot(x,y),a=(12**2-11**2+d*d)/(2*d);
  if(d>=23||d<=1)throw Error('Leg target is outside fixed bone reach');
  const h=Math.sqrt(Math.max(0,12**2-a*a));return [x/d*a+y/d*h,y/d*a-x/d*h];}
function pose(frame,action){const phase=frame/8,walking=action==='walk';
  // 触地略低，单腿经过身体下方时略高；两步同周期，不在换腿时整身跳移。
  const height=walking?22.3-.25*Math.cos(4*Math.PI*phase):22.5;
  const sway=walking?.35*Math.sin(2*Math.PI*phase):0;
  const swayDepth=sway*rig.projection.forwardY/rig.projection.forwardX;
  const bodyY=(22.5-height)*rig.projection.vertical+swayDepth;
  // 恢复早期步态的下沉→回升节奏，显式登记整数像素，不让微小曲线被取整抹掉。
  // 这是骨盆以上的压缩/回弹；腿部目标保持v008，避免再次扩大屈膝。
  const upperBob=walking?[0,1,0,-1][frame%4]:0;
  const upperY=Math.round(bodyY)+upperBob;
  const p={head:[32,23+upperY],torso:[32,42+upperY],root:rig.root,phase,height,upperBob,upperY};
  for(const [side,offset] of [['near',0],['far',.5]]){
    const near=side==='near',path=walking?footPath(phase+offset):{forward:0,lift:0,support:true,phase:0};
    const ground=[near?28:36,near?75:73],hip=[ground[0]+sway,ground[1]-height*rig.projection.vertical+swayDepth];
    const localAnkle=[path.forward-sway/rig.projection.forwardX,height-path.lift];
    const localKnee=kneeInPlane(localAnkle),ankle=project(localAnkle,hip),knee=project(localKnee,hip);
    // 手臂沿行走方向摆动，与同侧腿反相，不追随IK脚回收曲线突然横甩。
    const shoulder=[near?24+sway:40+sway,(near?34:33)+upperY];
    const armAngle=walking?-.22*Math.cos(2*Math.PI*(phase+offset)):0;
    const elbowLocal=[Math.sin(armAngle)*9,Math.cos(armAngle)*9];
    const foreAngle=armAngle+.17;
    const handLocal=[elbowLocal[0]+Math.sin(foreAngle)*11,elbowLocal[1]+Math.cos(foreAngle)*11];
    const elbow=project(elbowLocal,shoulder),wrist=project(handLocal,shoulder);
    // 支撑时平脚；离地后轻微脚尖下垂，落脚前恢复水平，鞋底始终刚性。
    const bootAngle=path.support?0:.10*Math.sin((path.phase-.5)*2*Math.PI);
    p[side]={hip,knee,ankle,shoulder,elbow,wrist,support:path.support,bootAngle,
      spatial:{hip:[0,0],knee:localKnee,ankle:localAnkle},armForward:handLocal[0]};
  }return p;
}
// 生图把膝甲同时画在大腿和小腿；绑定源只取小腿下段，膝甲由大腿唯一拥有。
// 这里登记静态纹理区域，所有帧完全共用，不逐帧变更裁片。
const textureRegions={near_shin:[0,.34,1,.66],far_shin:[0,.34,1,.66],near_boot:[0,.12,1,.88],far_boot:[0,.12,1,.88]};
// 头胸先在固定原生像素格中最近邻取样一次，再用整数左上角放置。
// 原来的居中19px宽会产生半像素左边界，细小眼白因此被重采样吞掉。
function prepareNativeParts(){for(const name of ['head','torso']){
  const size=rig[name],c=document.createElement('canvas');c.width=size.width;c.height=size.height;
  const ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.drawImage(sources[name],0,0,c.width,c.height);nativeParts[name]=c;
}}
function blit(ctx,name,x,y,w,h){const im=nativeParts[name]||sources[name];
  ctx.drawImage(im,Math.round(x-w/2),Math.round(y-h/2),w,h);}
// 静态安装点位于各片有效取样区，比例来自源分件：骨头端点不能默认等于裁片边缘。
const mounts={near_thigh:{top:[.49,.13],bottom:[.56,.80]},far_thigh:{top:[.50,.13],bottom:[.58,.80]},
  near_shin:{top:[.50,.05],bottom:[.50,.90]},far_shin:{top:[.50,.05],bottom:[.50,.90]},
  near_upper_arm:{top:[.50,.12],bottom:[.49,.88]},far_upper_arm:{top:[.50,.12],bottom:[.50,.88]},
  near_forearm:{top:[.48,.10],bottom:[.50,.87]},far_forearm:{top:[.48,.10],bottom:[.50,.87]}};
function bone(ctx,name,a,b,width){const im=sources[name],r=textureRegions[name]||[0,0,1,1],m=mounts[name];
  const length=Math.hypot(b[0]-a[0],b[1]-a[1]);
  const dx=(m.bottom[0]-m.top[0])*width;
  const height=Math.sqrt(Math.max(.01,length*length-dx*dx))/(m.bottom[1]-m.top[1]);
  const sourceAngle=Math.atan2((m.bottom[1]-m.top[1])*height,dx);
  const angle=Math.atan2(b[1]-a[1],b[0]-a[0])-sourceAngle;
  ctx.save();ctx.translate(...a);ctx.rotate(angle);
  ctx.drawImage(im,r[0]*im.width,r[1]*im.height,r[2]*im.width,r[3]*im.height,-m.top[0]*width,-m.top[1]*height,width,height);ctx.restore();}
function boot(ctx,side,q){const im=sources[side+'_boot'],r=textureRegions[side+'_boot'];ctx.save();ctx.translate(...q.ankle);ctx.rotate(q.bootAngle);
  // 鞋口覆盖自己的小腿末端，脚尖和厚鞋底保留；仍位于整条近腿之后/之前的合理次序。
  ctx.drawImage(im,0,r[1]*im.height,im.width,r[3]*im.height,-3.8,-2.7,11,8);ctx.restore();}
function arm(ctx,side,q,part){if(part!=='lower')bone(ctx,side+'_upper_arm',q.shoulder,q.elbow,side==='near'?6.5:5.5);
  if(part!=='upper')bone(ctx,side+'_forearm',q.elbow,q.wrist,side==='near'?6:5.5);}
function drawRig(ctx,p,ox=0,oy=0,debug=false){ctx.save();ctx.translate(ox,oy);ctx.imageSmoothingEnabled=false;
  for(const side of ['far','near']){const q=p[side];
    bone(ctx,side+'_shin',q.knee,q.ankle,side==='near'?7.5:6.5);
    bone(ctx,side+'_thigh',q.hip,q.knee,side==='near'?8.5:7.5);
    boot(ctx,side,q);}
  const f=p.far;arm(ctx,'far',f,'upper');
  // 上臂保留远侧归属；只有已经摆到身体前方的前臂在衣身前合成。
  if(f.armForward<=0)arm(ctx,'far',f,'lower');
  blit(ctx,'torso',p.torso[0],p.torso[1],rig.torso.width,rig.torso.height);
  if(f.armForward>0)arm(ctx,'far',f,'lower');
  arm(ctx,'near',p.near,'all');
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
  const progress=(time%3840)/960,wx=progress*rig.stride*2*rig.projection.forwardX,wy=progress*rig.stride*2*rig.projection.forwardY;w.strokeStyle='#344c57';for(let x=-96;x<250;x+=16){w.beginPath();w.moveTo((x-wx)*4,0);w.lineTo((x-wx)*4,384);w.stroke();}for(let y=-20;y<150;y+=16){w.beginPath();w.moveTo(0,(y-wy)*4);w.lineTo(768,(y-wy)*4);w.stroke();}w.drawImage(frameCanvas(p,showBones),256,0,256,384);
  const old=$('before').getContext('2d');old.imageSmoothingEnabled=false;old.fillStyle=light?'#d4d9d4':'#182631';old.fillRect(0,0,384,384);if(beforeSheet.complete&&beforeSheet.naturalWidth)old.drawImage(beforeSheet,frame*64,0,64,96,64,0,256,384);
  window.currentRigFrame=p;
}
function exportSheet(){const canvas=document.createElement('canvas');canvas.width=512;canvas.height=96;const c=canvas.getContext('2d');for(let i=0;i<8;i++)c.drawImage(frameCanvas(pose(i,mode)),i*64,0);$('sheet').src=canvas.toDataURL('image/png');const a=document.createElement('a');a.download=`A-${mode}-down_right-eyes-v010.png`;a.href=canvas.toDataURL('image/png');$('download').href=a.href;$('download').download=a.download;}
function tick(t){if(last&&!paused)time+=(t-last)*speed;last=t;draw();requestAnimationFrame(tick)}
Promise.all(names.map(name=>new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>{sources[name]=i;resolve()};i.onerror=reject;i.src=`parts/${name}.png`;}))).then(()=>{prepareNativeParts();exportSheet();requestAnimationFrame(tick)}).catch(()=>$('state').textContent='分件加载失败');
$('action').onchange=e=>{mode=e.target.value;time=0;$('export').disabled=mode!=='walk';};$('pause').onclick=()=>{paused=!paused;$('pause').textContent=paused?'继续':'暂停';};$('step').onclick=()=>{paused=true;time=(Math.floor(time/120)+1)*120;$('pause').textContent='继续';draw();};$('bones').onclick=()=>{showBones=!showBones;};$('bg').onclick=()=>{light=!light;};$('export').onclick=exportSheet;

$('speed').onchange=e=>{speed=Number(e.target.value);};
