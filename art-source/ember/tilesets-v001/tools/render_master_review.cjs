// 构件母稿审阅拼图；不改动源图，不生成生产瓦片，所有缩放仅用于预览。
const fs=require('fs'),path=require('path');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=path.resolve(__dirname,'../../../..');
const batch=path.join(root,'art-source/ember/tilesets-v001');
const rows=[
 ['新地板配色参考','art-source/ember/batch-01/generated/floor_clean_master_v001.png'],
 ['检修口关闭','art-source/ember/tilesets-v001/generated/hatch_closed_module_master_v001.png'],
 ['检修口开启','art-source/ember/tilesets-v001/generated/hatch_open_module_master_v001.png'],
 ['裂痕提取 v002','art-source/ember/tilesets-v001/generated/crack_decal_master_v002.png'],
 ['墙体材质模块','art-source/ember/tilesets-v001/generated/wall_module_master_v001.png'],
 ['栏杆材质模块','art-source/ember/tilesets-v001/generated/railing_module_master_v001.png'],
 ['桥面母稿：背景待清','art-source/ember/tilesets-v001/generated/bridge_module_master_v001.png'],
 ['维修碎屑贴花','art-source/ember/tilesets-v001/generated/debris_module_master_v001.png'],
 ['管线材质模块','art-source/ember/tilesets-v001/generated/pipe_module_master_v001.png'],
 ['水渠岸线模块','art-source/ember/tilesets-v001/generated/channel_module_master_v001.png'],
 ['电缆环贴花','art-source/ember/tilesets-v001/generated/cable_loop_module_master_v001.png'],
 ['裂痕 v001：整板，未选','art-source/ember/tilesets-v001/generated/crack_module_master_v001.png'],
];
const width=1536,height=1120,layers=[];
let labels='<text x="42" y="46" fill="#ECE9D8" font-size="30">《余烬采能站》通用瓦片集 · 构件母稿审阅</text>'+
'<text x="42" y="82" fill="#E5A44B" font-size="20">计划三套 12 / 26 / 24 块 · 原生32×32接口尚未整理 · 当前正式瓦片 0</text>';
(async()=>{
 for(let i=0;i<rows.length;i++){
  const [label,file]=rows[i],x=40+(i%4)*375,y=116+Math.floor(i/4)*300;
  const matte=await sharp({create:{width:340,height:238,channels:4,background:'#607079'}}).png().toBuffer();
  const thumb=await sharp(path.join(root,file)).resize(340,238,{fit:'contain',kernel:'nearest',background:{r:0,g:0,b:0,alpha:0}}).png().toBuffer();
  layers.push({input:matte,left:x,top:y});
  layers.push({input:thumb,left:x,top:y});
  labels+='<text x="'+x+'" y="'+(y+266)+'" fill="#BECBC4" font-size="18">'+label+'</text>';
 }
 labels+='<text x="42" y="1065" fill="#E5A44B" font-size="19">此图是已生成母稿的审阅拼图，不是可导入的生产atlas；连接变体、调色板、Alpha与接缝仍待处理。</text>'+
 '<text x="42" y="1100" fill="#829BA3" font-size="17">地面与检修细节 / 墙体栏杆桥面 / 管线水渠 · 可编辑TileSet构建与只读验收工具已准备</text>';
 const svg=Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="'+width+'" height="'+height+'"><g font-family="Microsoft YaHei,sans-serif">'+labels+'</g></svg>');
 layers.push({input:svg,left:0,top:0});
 const out=path.join(batch,'tileset_masters_review_v001.png');
 await sharp({create:{width,height,channels:4,background:'#182631'}}).composite(layers).png().toFile(out);
 const recordPath=path.join(batch,'generation-record.json'),record=JSON.parse(fs.readFileSync(recordPath,'utf8'));
 const crypto=require('crypto'),hashes=[];
 for(const item of record.records){
  item.sha256=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,item.file))).digest('hex');
  item.copy_matches_original_tool_output=item.sha256===crypto.createHash('sha256').update(fs.readFileSync(item.source)).digest('hex');
  if(!item.copy_matches_original_tool_output)throw Error('source mismatch '+item.id);
  hashes.push(item.sha256+'  '+item.file);
 }
 fs.writeFileSync(recordPath,JSON.stringify(record,null,2)+'\n');
 fs.writeFileSync(path.join(batch,'masters.sha256'),hashes.join('\n')+'\n');
 console.log(JSON.stringify({review_board:path.relative(root,out),source_hashes_match:record.records.length},null,2));
})().catch(e=>{console.error(e);process.exit(1)});

