// 审查用共同ROI裁切与放大。只拼接证据图，不修改角色帧。
const fs=require('node:fs/promises'),path=require('node:path');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=path.dirname(__dirname),roi={left:15,top:53,width:21,height:21},scale=10;
async function run(){
 const inputs=[],labels=[],cell=roi.width*scale,height=roi.height*scale,head=56;
 let i=0;
 for(const f of [1,4])for(const version of ['rig','rc01','rc02']){
  const name=`robot_walk_down_left_f${String(f).padStart(2,'0')}_v011.png`;
  const file=version==='rig'?`source/fixed-rig-pilot/down_left/${name}`:version==='rc01'?`review/phase-a-rc01/frames/walk/down_left/${name}`:`frames/walk/down_left/${name}`;
  const image=await sharp(path.join(root,file)).extract(roi).resize(cell,height,{kernel:'nearest'}).flatten({background:'#ece9d8'}).png().toBuffer();
  inputs.push({input:image,left:i*cell,top:head});
  labels.push(`<text x="${i*cell+6}" y="20">F0${f} / ${version}</text><text x="${i*cell+6}" y="40">same source ROI (15,53)</text>`);i++;
 }
 const svg=`<svg width="${cell*6}" height="${height+head}"><g font-family="sans-serif" font-size="13" fill="#182631">${labels.join('')}</g></svg>`;
 await sharp({create:{width:cell*6,height:height+head,channels:4,background:'#ece9d8'}}).composite([...inputs,{input:Buffer.from(svg),left:0,top:0}]).png().toFile(path.join(root,'qa/far_right_armor_f01_f04_rc02_comparison.png'));
 const strip=[];
 for(let f=0;f<8;f++){
  const im=await sharp(path.join(root,`frames/walk/down_left/robot_walk_down_left_f${String(f).padStart(2,'0')}_v011.png`)).extract({left:14,top:51,width:31,height:31}).resize(248,248,{kernel:'nearest'}).flatten({background:'#ece9d8'}).png().toBuffer();
  strip.push({input:im,left:(f%4)*248,top:Math.floor(f/4)*248});
 }
 await sharp({create:{width:992,height:496,channels:4,background:'#ece9d8'}}).composite(strip).png().toFile(path.join(root,'qa/sw_legs_rc02_8x.png'));
 console.log('Saved fixed ROI comparison and eight-frame leg strip');
}
run().catch(e=>{console.error(e);process.exitCode=1;});
