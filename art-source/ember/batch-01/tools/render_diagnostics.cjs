// 首批诊断预览：只做采样与验收拼图，绝不作为正式美术整理或定稿。
const fs = require('fs');
const path = require('path');
const sharp = require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root = path.resolve(__dirname, '../../../..');
const batch = path.join(root, 'art-source/ember/batch-01');
const dest = path.join(batch, 'diagnostics');
const refDir = path.join(root, 'art-source/ember/references');
const defs = [
  ['robot','robot_idle_down_master_v001.png',64,96,'C01 机器人'],
  ['station','station_master_v001.png',128,160,'B01 采能站'],
  ['floor_clean','floor_clean_master_v001.png',32,32,'干净'],
  ['floor_worn','floor_worn_master_v001.png',32,32,'磨损'],
  ['floor_grate','floor_grate_master_v001.png',32,32,'格栅'],
  ['floor_wet','floor_wet_master_v001.png',32,32,'潮湿']
];
const palette=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','7B4D35','B77C4B','E2B77A','51C5C2','E5A44B','E65B4A','566B78','203A4B','406B78','ECE9D8'];
const buf = {};
const xml = s => s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const text = (x,y,s,size=20,color='#ECE9D8') => '<text x="'+x+'" y="'+y+'" fill="'+color+'" font-size="'+size+'" font-family="Microsoft YaHei, sans-serif">'+xml(s)+'</text>';
const svg=(w,h,body)=>Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'">'+body+'</svg>');
const rect=(x,y,w,h,color,extra='')=>'<rect x="'+x+'" y="'+y+'" width="'+w+'" height="'+h+'" fill="'+color+'" '+extra+'/>';
const checker=(x,y,w,h,cell=16)=> {
 let out=''; for(let yy=0;yy<h;yy+=cell)for(let xx=0;xx<w;xx+=cell)out+=rect(x+xx,y+yy,Math.min(cell,w-xx),Math.min(cell,h-yy),((xx/cell+yy/cell)%2)?'#556169':'#46525B');return out;
};
async function canvas(w,h,items,overlay,name,bg='#182631'){
 const layers=items.map(i=>({input:i.input,left:i.x,top:i.y}));
 if(overlay)layers.push({input:svg(w,h,overlay),left:0,top:0});
 await sharp({create:{width:w,height:h,channels:4,background:bg}}).composite(layers).png().toFile(name);
}
async function scale(input,n){
 // 整数预览逐像素复制RGBA，避免图像库预乘Alpha时引入颜色舍入差。
 const {data,info}=await sharp(input).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 const width=info.width*n,height=info.height*n,out=Buffer.alloc(width*height*4);
 for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++){
  const offset=(y*info.width+x)*4;
  for(let dy=0;dy<n;dy++)for(let dx=0;dx<n;dx++){
   data.copy(out,((y*n+dy)*width+x*n+dx)*4,offset,offset+4);
  }
 }
 return sharp(out,{raw:{width,height,channels:4}}).png().toBuffer();
}
(async()=>{
 for(const d of [dest,path.join(dest,'native-grid'),path.join(dest,'integer-2x'),refDir])fs.mkdirSync(d,{recursive:true});
 const index=[];
 for(const [id,file,w,h,label] of defs){
  const src=path.join(batch,'generated',file);
  const metadata=await sharp(src).metadata();
  // 不裁切、不阈值Alpha、不量化颜色、不重新定位、不修接缝。
  const probe=await sharp(src).resize(w,h,{fit:'fill',kernel:'nearest'}).png().toBuffer();
  buf[id]=probe;
  const nativeFile=path.join(dest,'native-grid',id+'_grid_probe_v001.png');
  const previewFile=path.join(dest,'integer-2x',id+'_grid_probe_v001_2x.png');
  fs.writeFileSync(nativeFile,probe);fs.writeFileSync(previewFile,await scale(probe,2));
  index.push({id,source:path.relative(root,src).replaceAll('\\','/'),source_size:[metadata.width,metadata.height],probe:path.relative(root,nativeFile).replaceAll('\\','/'),probe_size:[w,h],preview_2x:path.relative(root,previewFile).replaceAll('\\','/'),status:'DIAGNOSTIC_ONLY_NOT_PRODUCTION',resampling:'nearest; full canvas; no artistic correction'});
 }
 // 比例图：对象共同4倍；标注标准接地点基线，不伪造实际已对齐。
 const w=1536,h=1024,robot={x:110,y:376},station={x:452,y:120},baseline=696;
 let base=checker(robot.x,robot.y,256,384)+checker(station.x,station.y,512,640);
 const items=[{input:svg(w,h,base),x:0,y:0},{input:await scale(buf.robot,4),...robot},{input:await scale(buf.station,4),...station}];
 let overlay=text(48,46,'《余烬采能站》首批风格 / 比例诊断',30)+text(48,80,'六项已生图 · 目标网格为粗采样 · 正式合格 0 项',20,'#E5A44B');
 overlay+=text(50,120,'机器人、采能站采用相同 4× 原生目标尺度',20);
 overlay+='<path d="M60 '+baseline+' H990" stroke="#E5A44B" stroke-width="2" stroke-dasharray="10 6"/>';
 for(const [p,ww,hh,ax,ay] of [[robot,256,384,32,80],[station,512,640,64,144]]){
  overlay+=rect(p.x,p.y,ww,hh,'none','stroke="#829BA3" stroke-width="1"');
  const cx=p.x+ax*4,cy=p.y+ay*4;
  overlay+='<path d="M'+(cx-12)+' '+cy+' H'+(cx+12)+' M'+cx+' '+(cy-12)+' V'+(cy+12)+'" stroke="#E5A44B" stroke-width="3"/>';
 }
 overlay+=text(110,800,'C01 64×96 · 目标脚底 (32,80)',18)+text(452,800,'B01 128×160 · 目标基座 (64,144)',18);
 overlay+=text(1050,140,'T01 四种地板：32×32，4×预览',20);
 for(let i=0;i<4;i++){
  const id=defs[i+2][0],x=1070+(i%2)*220,y=176+Math.floor(i/2)*210;
  items.push({input:await scale(buf[id],4),x,y});
  overlay+=text(x,y+158,defs[i+2][4],20);
 }
 overlay+=text(1050,640,'黄十字仅为标准锚点参考',18)+text(1050,672,'Alpha外晕、色数与留边待修',18)+text(1050,704,'本批未生成门，不提供门比例验收',17);
 overlay+=text(48,872,'视觉基准：圆角浅装甲 / 蓝灰钢板 / 黄铜接口 / 中性未点亮窗口',21);
 overlay+=text(48,906,'本图为验收拼图，未裁切、量化、清Alpha或校正接缝；不得当作生产定稿。',19,'#E5A44B');
 for(let i=0;i<palette.length;i++){overlay+=rect(50+i*89,936,74,32,'#'+palette[i])+text(50+i*89,994,'#'+palette[i],13);}
 await canvas(w,h,items,overlay,path.join(refDir,'batch01_style_scale_diagnostic_v001.png'));
 // 每种地板自身3×3，先按目标网格重复，再整数4×展示。
 for(const name of ['clean','worn','grate','wet']){
  const tile=buf['floor_'+name], layers=[];
  for(let yy=0;yy<3;yy++)for(let xx=0;xx<3;xx++)layers.push({input:tile,left:xx*32,top:yy*32});
  const tiled=await sharp({create:{width:96,height:96,channels:4,background:'#4D6470'}}).composite(layers).png().toBuffer();
  fs.writeFileSync(path.join(dest,'tiling_'+name+'_3x3_4x.png'),await scale(tiled,4));
 }
 // 全16种有向邻接，各做横向和竖向拼接；红色短线在图外标出接缝。
 const names=['clean','worn','grate','wet'], pairItems=[];
 let pairOverlay=text(40,44,'四种地板全部有向相邻接缝 · 目标32×32粗采样的2×预览',28)+text(40,78,'行=第一块；列=第二块。左表：右边接左边；右表：下边接上边。红标仅在图外。',18);
 for(let row=0;row<4;row++)for(let col=0;col<4;col++){
  const a=names[row],b=names[col],aa=await scale(buf['floor_'+a],2),bb=await scale(buf['floor_'+b],2);
  const hx=52+col*185,hy=180+row*172,vx=862+col*160,vy=168+row*185;
  pairItems.push({input:aa,x:hx,y:hy},{input:bb,x:hx+64,y:hy},{input:aa,x:vx,y:vy},{input:bb,x:vx,y:vy+64});
  pairOverlay+=text(hx,hy+94,a+' → '+b,14)+text(vx-8,vy+154,a+' ↓ '+b,13);
  pairOverlay+='<path d="M'+(hx+64)+' '+(hy-10)+' V'+(hy-3)+' M'+(vx-10)+' '+(vy+64)+' H'+(vx-3)+'" stroke="#E65B4A" stroke-width="3"/>';
 }
 pairOverlay+=text(52,132,'水平有向邻接（16组）',22)+text(862,132,'垂直有向邻接（16组）',22)+text(40,988,'接缝诊断不等于无缝合格；需统一边缘接口、母稿像素尺度与16色调色后重新验收。',19,'#E5A44B');
 await canvas(1536,1024,pairItems,pairOverlay,path.join(dest,'all_floor_adjacencies_v001.png'));
 fs.writeFileSync(path.join(dest,'index.json'),JSON.stringify({date:'2026-10-03',role:'DIAGNOSTIC_ONLY_NOT_PRODUCTION',assets:index},null,2)+'\n');
 console.log(JSON.stringify({diagnostic_probes:index.map(a=>({id:a.id,size:a.probe_size,source_size:a.source_size})),scale_board:'art-source/ember/references/batch01_style_scale_diagnostic_v001.png',floor_pair_board:'art-source/ember/batch-01/diagnostics/all_floor_adjacencies_v001.png',formal_pngs:0},null,2));
})().catch(e=>{console.error(e);process.exit(1)});

