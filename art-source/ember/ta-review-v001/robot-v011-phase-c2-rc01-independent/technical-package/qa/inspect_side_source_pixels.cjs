// 只读诊断：列出侧面身体尾部以及小连通块坐标，帮助修正部件归属。
const path=require('node:path'),fs=require('node:fs/promises');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {components}=require('./audit_walk_components.cjs');
const root=path.resolve(__dirname,'..');
(async()=>{for(const d of['left','right']){
 const body=await sharp(path.join(root,`source/fixed-parts/${d}/body.png`)).ensureAlpha().raw().toBuffer(),tail=[];
 for(let y=55;y<96;y++)for(let x=0;x<64;x++)if(body[(y*64+x)*4+3])tail.push({xy:[x,y],rgba:[...body.subarray((y*64+x)*4,(y*64+x)*4+4)]});
 const stray=[];for(let i=0;i<8;i++){const raw=await sharp(path.join(root,`source/fixed-rig-pilot/${d}/robot_walk_${d}_f${String(i).padStart(2,'0')}_v011.png`)).ensureAlpha().raw().toBuffer();for(const c of components(raw).slice(1))stray.push({frame:i,pixels:c.indices.map(p=>[p%64,Math.floor(p/64)])});}
 console.log(JSON.stringify({direction:d,body_tail:tail,stray}));
}})().catch(e=>{console.error(e);process.exitCode=1;});
