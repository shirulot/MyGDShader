"""Create the review UI with genuine one-shot hit playback and shared frame phase."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
old=(ROOT.parent/'enemy-heavy-directions-move-v014/previews/index.html').read_text(encoding='utf-8')
style=old[old.index('<style>'):old.index('</style>')+8]
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ember · 重装机八向待机与受击 v015</title>
'''+style+'''
<header><h1>Ember · 重装机八向待机与受击 v015</h1><p class="status">新增七向 × 两种动作待审；正向两条动作保留原通过文件。</p><p>待机循环播放，受击播放一次后停在恢复帧。左右同相位；切换方向保留当前帧。</p></header>
<div class="controls"><label>动作 <select id="action" aria-label="动作"><option value="idle">待机 · 4 FPS</option><option value="hit">受击 · 12 FPS</option></select></label>
<button id="play">暂停</button><button id="replay">从头播放</button><button id="prev">前一帧</button><button id="next">后一帧</button>
<label>速度 <select id="speed" aria-label="速度"><option value="normal">正常速度</option><option value="slow">慢速 1 FPS</option></select></label><button id="zoom">切到 1×</button><button id="bg">切到深底</button></div>
<div class="pair"><section class="panel"><h2 id="current-title"></h2><div class="stage"><canvas id="current" width="128" height="128"></canvas></div><p class="detail" id="current-info"></p></section>
<section class="panel"><h2>已通过的正向 · down</h2><div class="stage"><canvas id="approved" width="128" height="128"></canvas></div><p class="detail" id="approved-info"></p></section></div>
<div class="directions" id="directions" aria-label="八方向"></div><details><summary>检查说明</summary><p>128×128 完整原生画布，整数倍 Nearest；七向母版均已过静态审查，本批新增动作仍待独立验收。壳体为固定部件位移，履带支撑与外框不动，无逐帧生图。</p><p id="build"></p></details>
<script>
'use strict';
const $=id=>document.getElementById(id),dirs=['down','down_left','left','up_left','up','up_right','right','down_right'],labels=['↓ 正下','↙ 左下','← 正左','↖ 左上','↑ 正上','↗ 右上','→ 正右','↘ 右下'];
const cache=new Map();let catalog,kind='idle',direction='down_left',frame=0,progress=0,playing=true,zoom=4,dark=false,last=performance.now();
function clip(){return catalog?.clips.find(c=>c.action===kind+'_'+direction)}
function img(path){if(!cache.has(path)){const image=new Image();image.src=path;image.onload=draw;cache.set(path,image)}return cache.get(path)}
function render(canvas,path){const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,128,128);const image=img(path);if(image.complete&&image.naturalWidth)ctx.drawImage(image,frame*128,0,128,128,0,0,128,128);canvas.style.width=`${zoom*128}px`;canvas.style.height=`${zoom*128}px`}
function draw(){if(!catalog)return;render($('current'),clip().atlas.replace('res://',''));render($('approved'),`reference/enemy_tracked_heavy/${kind}_down.png`);
$('current-title').textContent=`重装机 · ${labels[dirs.indexOf(direction)]} · ${kind==='idle'?'待机':'受击'}`;
$('current-info').textContent=`第 ${frame+1} / 4 帧 · ${zoom}× · ${kind==='idle'?'循环':'单次播放'} · ${direction==='down'?'原动作已通过':'新增候选待审'}`;
$('approved-info').textContent=`原通过版本 · 同相位第 ${frame+1} / 4 帧 · ${zoom}×`;
document.querySelectorAll('.stage,.dir img').forEach(el=>el.style.background=dark?'#070b10':'#d2d6dc');document.querySelectorAll('.dir').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.dir===direction)));
document.body.dataset.frame=frame;document.body.dataset.direction=direction;document.body.dataset.action=kind;document.body.dataset.playing=playing;}
function replay(){frame=0;progress=0;playing=true;last=performance.now();$('play').textContent='暂停';draw()}
function step(delta){playing=false;frame=(frame+delta+4)%4;progress=0;$('play').textContent='继续';draw()}
$('action').onchange=()=>{kind=$('action').value;replay()};$('replay').onclick=replay;$('next').onclick=()=>step(1);$('prev').onclick=()=>step(-1);
$('play').onclick=()=>{if(!playing&&kind==='hit'&&frame===3){replay();return}playing=!playing;$('play').textContent=playing?'暂停':'继续';last=performance.now();draw()};
$('zoom').onclick=()=>{zoom=zoom===4?1:4;$('zoom').textContent=zoom===4?'切到 1×':'切到 4×';draw()};$('bg').onclick=()=>{dark=!dark;$('bg').textContent=dark?'切到浅底':'切到深底';draw()};
function tick(now){if(playing&&catalog){progress+=Math.min((now-last)/1000,.1)*($('speed').value==='slow'?1:clip().fps);while(progress>=1){progress-=1;if(frame===3&&!clip().loop){playing=false;progress=0;$('play').textContent='从头播放受击';break}frame=(frame+1)%4}draw()}last=now;requestAnimationFrame(tick)}
fetch('catalog.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).then(c=>{catalog=c;dirs.forEach((d,i)=>{const b=document.createElement('button');b.className='dir';b.dataset.dir=d;b.setAttribute('aria-label',labels[i]);b.innerHTML=`<img alt="" src="output/enemy_tracked_heavy/neutral_${d}.png"><span>${labels[i]}</span>`;b.onclick=()=>{direction=d;draw()};$('directions').append(b)});$('build').textContent='16 条动作共64帧：14条/56帧新增候选，2条/8帧原通过正向。其余三类动作不在本批。';draw();requestAnimationFrame(tick)}).catch(e=>$('current-info').textContent='加载失败：'+e.message);
</script></html>'''
(ROOT/'previews/index.html').write_text(html,encoding='utf-8')
