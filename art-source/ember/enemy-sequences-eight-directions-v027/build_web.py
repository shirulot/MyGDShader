"""Build a small actual-frame player for the complete immutable assembly."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
old=(ROOT.parent/'enemy-patrol-idle-hit-v025/previews/index.html').read_text(encoding='utf-8')
style=old[old.index('<style>'):old.index('</style>')+8]
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ember · 四款敌人八向五动作 v027</title>
'''+style+'''
<header><h1>Ember · 四款敌人八向五动作</h1><p>v027 汇总 · 160 条动作 · 960 帧 · 128×128 原生画布</p><p>查看实际交付序列。切换方向保持动作相位；攻击、受击和死亡播放一次后停留。</p></header>
<div class="controls"><label>单位 <select id="unit" aria-label="单位"><option value="enemy_patrol">巡逻兵</option><option value="enemy_tracked_heavy">履带重装机</option><option value="enemy_cutter">切割者</option><option value="enemy_scout_drone">悬浮侦察机</option></select></label>
<label>动作 <select id="action" aria-label="动作"><option value="idle">待机 · 4 FPS</option><option value="move">移动 · 8 FPS</option><option value="attack">攻击 · 10 FPS</option><option value="hit">受击 · 12 FPS</option><option value="death">死亡 · 10 FPS</option></select></label>
<button id="play">暂停</button><button id="replay">从头播放</button><button id="prev">前一帧</button><button id="next">后一帧</button>
<label>速度 <select id="speed" aria-label="速度"><option value="normal">正常速度</option><option value="slow">慢速 1 FPS</option></select></label><button id="zoom">切到 1×</button><button id="bg">切到深底</button></div>
<div class="pair"><section class="panel"><h2 id="current-title"></h2><div class="stage"><canvas id="current" width="128" height="128"></canvas></div><p class="detail" id="current-info"></p></section>
<section class="panel"><h2>原正向 · 同相位对照</h2><div class="stage"><canvas id="approved" width="128" height="128"></canvas></div><p class="detail" id="approved-info"></p></section></div>
<div class="directions" id="directions" aria-label="八方向"></div><details><summary>资源说明</summary><p>正向20条保持v012文件；新增140条均绑定各自正式回执。左右不对称工具保持本体侧别。Nearest显示，所有帧共享根坐标(64,104)。本页不模拟世界位移、碰撞或伤害。</p><p id="build"></p></details>
<script>
'use strict';
const $=id=>document.getElementById(id),dirs=['down','down_left','left','up_left','up','up_right','right','down_right'],labels=['↓ 正下','↙ 左下','← 正左','↖ 左上','↑ 正上','↗ 右上','→ 正右','↘ 右下'];
const names={enemy_patrol:'巡逻兵',enemy_tracked_heavy:'履带重装机',enemy_cutter:'切割者',enemy_scout_drone:'悬浮侦察机'},actions={idle:'待机',move:'移动',attack:'攻击',hit:'受击',death:'死亡'};
const cache=new Map();let catalog,unit='enemy_patrol',kind='idle',direction='down_left',frame=0,progress=0,playing=true,zoom=4,dark=false,last=performance.now();
function clip(d=direction){return catalog?.clips.find(c=>c.unit===unit&&c.action===kind+'_'+d)}
function img(path){if(!cache.has(path)){const image=new Image();image.onload=draw;image.onerror=()=>{$('current-info').textContent='素材加载失败：'+path};image.src=path;cache.set(path,image)}return cache.get(path)}
function render(canvas,path){const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,128,128);const im=img(path);if(im.complete&&im.naturalWidth)ctx.drawImage(im,frame*128,0,128,128,0,0,128,128);canvas.style.width=`${zoom*128}px`;canvas.style.height=`${zoom*128}px`}
function draw(){if(!catalog)return;const c=clip();render($('current'),c.atlas.replace('res://',''));render($('approved'),clip('down').atlas.replace('res://',''));
$('current-title').textContent=`${names[unit]} · ${labels[dirs.indexOf(direction)]} · ${actions[kind]}`;
$('current-info').textContent=`第 ${frame+1} / ${c.frame_count} 帧 · ${zoom}× · ${c.loop?'循环播放':'单次播放'} · ${playing?'播放中':'停留'}`;
$('approved-info').textContent=`原正向 · 同相位第 ${frame+1} / ${c.frame_count} 帧 · ${zoom}×`;
document.querySelectorAll('.stage,.dir img').forEach(el=>el.style.background=dark?'#070b10':'#d2d6dc');document.querySelectorAll('.dir').forEach(el=>el.setAttribute('aria-pressed',String(el.dataset.dir===direction)));
document.body.dataset.unit=unit;document.body.dataset.frame=frame;document.body.dataset.direction=direction;document.body.dataset.action=kind;document.body.dataset.playing=playing;}
function replay(){frame=0;progress=0;playing=true;last=performance.now();$('play').textContent='暂停';draw()}
function step(delta){playing=false;frame=(frame+delta+clip().frame_count)%clip().frame_count;progress=0;$('play').textContent='继续';draw()}
function thumbnails(){document.querySelectorAll('.dir').forEach(el=>el.querySelector('img').src=`output/${unit}/neutral_${el.dataset.dir}.png`)}
$('unit').onchange=()=>{unit=$('unit').value;thumbnails();replay()};$('action').onchange=()=>{kind=$('action').value;replay()};$('replay').onclick=replay;$('next').onclick=()=>step(1);$('prev').onclick=()=>step(-1);
$('play').onclick=()=>{if(!playing&&!clip().loop&&frame===clip().frame_count-1){replay();return}playing=!playing;$('play').textContent=playing?'暂停':'继续';last=performance.now();draw()};
$('zoom').onclick=()=>{zoom=zoom===4?1:4;$('zoom').textContent=zoom===4?'切到 1×':'切到 4×';draw()};$('bg').onclick=()=>{dark=!dark;$('bg').textContent=dark?'切到浅底':'切到深底';draw()};
function tick(now){if(playing&&catalog){progress+=Math.min((now-last)/1000,.1)*($('speed').value==='slow'?1:clip().fps);while(progress>=1){progress-=1;if(frame===clip().frame_count-1&&!clip().loop){playing=false;progress=0;$('play').textContent='从头播放当前动作';break}frame=(frame+1)%clip().frame_count}draw()}last=now;requestAnimationFrame(tick)}
fetch('catalog.json').then(r=>{if(!r.ok)throw Error(r.status);return r.json()}).then(c=>{catalog=c;dirs.forEach((d,i)=>{const b=document.createElement('button');b.className='dir';b.dataset.dir=d;b.setAttribute('aria-label',labels[i]);b.innerHTML=`<img alt=""><span>${labels[i]}</span>`;b.onclick=()=>{direction=d;draw()};$('directions').append(b)});thumbnails();$('build').textContent='v027 · 4款 × 8方向 × 5动作，160条 / 960帧；各批次的原始固定包和回执随资源汇总提供。';draw();requestAnimationFrame(tick)}).catch(e=>$('current-info').textContent='加载失败：'+e.message);
</script></html>'''
(ROOT/'previews').mkdir(exist_ok=True)
(ROOT/'previews/index.html').write_text(html,encoding='utf-8')
