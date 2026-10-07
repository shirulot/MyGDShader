// 仅整理现有图像作为生图输入；没有用代码绘制动作。
const fs=require('node:fs/promises'),path=require('node:path');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,base=path.resolve(root,'../..');
async function main(){
 const gif=path.join(root,'references/deadrevolver-crouch.gif');
 const {data,info}=await sharp(gif,{animated:true}).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 const h=168,w=192,frames=[];
 for(let f=0;f<6;f++)frames.push({input:data.subarray(f*w*h*4,(f+1)*w*h*4),raw:{width:w,height:h,channels:4},left:f*w,top:0});
 await sharp({create:{width:w*6,height:h,channels:4,background:'#182631'}}).composite(frames).png().toFile(path.join(root,'references/deadrevolver-six-frames.png'));
 const original=path.join(base,'revisions/collect-knee-v013/source/left/baseline_f0.png');
 await fs.copyFile(original,path.join(root,'source/robot-neutral.png'));
 const raw=await sharp(original).ensureAlpha().raw().toBuffer();
 const sheet=await sharp({create:{width:192,height:192,channels:4,background:'#00000000'}}).composite(Array.from({length:6},(_,i)=>({input:raw,raw:{width:64,height:96,channels:4},left:(i%3)*64,top:Math.floor(i/3)*96}))).png().toBuffer();
 await sharp(sheet).resize(1536,1536,{kernel:'nearest'}).png().toFile(path.join(root,'source/robot-six-cell-edit-target.png'));
 await fs.writeFile(path.join(root,'run-manifest.json'),JSON.stringify({status:'PILOT_IN_PROGRESS',scope:'left direction only; 6-frame crouching collect test',canvas:[64,96],root:[32,80],source_reference:'source/robot-neutral.png',motion_reference:'https://deadrevolver.itch.io/pixel-prototype-player-sprites',generation_method:'imagegen',main_project_modified:false,prior_assets_modified:false},null,2));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
