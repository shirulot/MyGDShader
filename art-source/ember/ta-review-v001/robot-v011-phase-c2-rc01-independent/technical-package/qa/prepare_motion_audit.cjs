// Skill 的审计器只支持正方形格。这里只加透明边，64×96 原像素不缩放不移动锚点相对角色。
// 96×96 文件仅为诊断适配，不是新的游戏资源或另一种原生尺寸。
const fs=require('node:fs/promises'),path=require('node:path');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
async function run(){
 const root=path.resolve(__dirname,'..'),meta=JSON.parse(await fs.readFile(path.join(root,'walk-batch-metadata.json'),'utf8'));
 const clips=meta.clips.filter(c=>c.action==='walk'),canvas=Buffer.alloc(96*8*96*clips.length*4);
 for(const[row,clip]of clips.entries())for(const[column,f]of clip.frames.entries()){
  const raw=await sharp(path.join(root,f.file)).ensureAlpha().raw().toBuffer();
  for(let y=0;y<96;y++)raw.copy(canvas,((row*96+y)*96*8+column*96+16)*4,y*64*4,(y+1)*64*4);
 }
 await sharp(canvas,{raw:{width:96*8,height:96*clips.length,channels:4}}).png().toFile(path.join(__dirname,'walk_motion_diagnostic_padded96.png'));
 console.log(JSON.stringify({rows:clips.length,columns:8,diagnostic_cell:96,source_cell:[64,96],scale:1,padding_x:16,directions:clips.map(c=>c.direction)}));
}
run().catch(e=>{console.error(e);process.exitCode=1;});
