
const el=id=>document.getElementById(id);
const ui=Object.fromEntries(['action','speed','bg','guides','play','step','seam','status','note'].map(id=>[id,el(id)]));
let clips=[],images={},direction='down_left',elapsed=0,last=null,playing=true;
const extras=['crouch','jump','collect','push','pull'];
const clip=ch=>clips.find(c=>c.character===ch&&c.action===ui.action.value&&c.direction===direction);
// 帧索引始终取模，不追加重复首帧，也不反向播放。
function frameAt(ms,c){return Math.floor(ms/c.duration_ms)%c.frame_count;}
function drawFrame(canvas,c,f,corrected){
 const g=canvas.getContext('2d');g.imageSmoothingEnabled=false;g.fillStyle=ui.bg.value;g.fillRect(0,0,canvas.width,canvas.height);
 if(!c)return;
 const shift=corrected?c.draw_offsets[f]:[0,0];
 // 64x96原图按4倍显示，左右各留16原像素，偏移不裁切贴图内容。
 g.drawImage(images[c.key],f*64,0,64,96,64+shift[0]*4,shift[1]*4,256,384);
 if(ui.guides.checked){
  g.strokeStyle='#637975';g.beginPath();g.moveTo(192,0);g.lineTo(192,384);g.moveTo(0,320);g.lineTo(384,320);g.stroke();
  const p=c.waist_landmarks?.[f];if(p){g.fillStyle='#e2b77a';g.fillRect(64+(p[0]+shift[0])*4-2,(p[1]+shift[1])*4-2,5,5);}
 }
}
function draw(){
 for(const ch of ['A','C']){const c=clip(ch);if(!c)continue;const f=frameAt(elapsed,c);drawFrame(el(ch+'-old'),c,f,false);drawFrame(el(ch+'-new'),c,f,true);el(ch+'-offset').textContent=c.direction==='left'?'左向保留，偏移为 0':`F${f} · 修正 (${c.draw_offsets[f].join(', ')}) px`;}
 const c=clip('A');if(c)ui.status.textContent=`F${frameAt(elapsed,c)} / ${c.frame_count-1} · ${Math.floor(elapsed/(c.duration_ms*c.frame_count))} 个周期`;
}
function refresh(){
 for(const b of document.querySelectorAll('[data-dir]')){b.setAttribute('aria-pressed',String(b.dataset.dir===direction));b.disabled=extras.includes(ui.action.value)&&b.dataset.dir!=='left';}
 ui.note.textContent=direction==='left'?'保留的左向动作，前后应完全相同。':'本次只修正全身位置；重点比较尾首和 F03 → F04。';
 const g=el('seams').getContext('2d');g.imageSmoothingEnabled=false;g.fillStyle=ui.bg.value;g.fillRect(0,0,768,384);
 for(const [row,ch] of ['A','C'].entries()){const c=clip(ch);if(!c)continue;for(const [col,f] of [c.frame_count-2,c.frame_count-1,0,1].entries()){const [dx,dy]=c.draw_offsets[f];g.drawImage(images[c.key],f*64,0,64,96,col*192+32+dx*2,row*192+dy*2,128,192);}}
 draw();
}
function tick(t){if(last!==null&&playing)elapsed+=Math.min(200,t-last)*Number(ui.speed.value);last=t;draw();requestAnimationFrame(tick);}
ui.action.onchange=()=>{if(extras.includes(ui.action.value))direction='left';elapsed=0;refresh();};
for(const b of document.querySelectorAll('[data-dir]'))b.onclick=()=>{const old=clip('A'),phase=old?(elapsed%(old.duration_ms*old.frame_count))/(old.duration_ms*old.frame_count):0;direction=b.dataset.dir;const next=clip('A');elapsed=phase*next.duration_ms*next.frame_count;refresh();};
ui.play.onclick=()=>{playing=!playing;ui.play.textContent=playing?'暂停':'播放';};
ui.step.onclick=()=>{playing=false;ui.play.textContent='播放';const c=clip('A');elapsed=(Math.floor(elapsed/c.duration_ms)+1)*c.duration_ms;draw();};
ui.seam.onclick=()=>{playing=false;ui.play.textContent='播放';const c=clip('A');elapsed=(c.frame_count-1)*c.duration_ms;draw();};
ui.bg.onchange=refresh;ui.guides.onchange=draw;
(async()=>{clips=(await(await fetch('catalog.json',{cache:'no-store'})).json()).clips;await Promise.all(clips.map(async c=>{const im=new Image();im.src=c.atlas;await im.decode();images[c.key]=im;}));refresh();requestAnimationFrame(tick);})().catch(e=>ui.note.textContent='载入失败：'+e.message);
