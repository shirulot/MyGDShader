// 只读原始AI连接编辑图；使用声明的第三方nearest API独立核量化，不调用制作方合成函数。
const fs=require('node:fs/promises'),path=require('node:path');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const pal=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A'].map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
(async()=>{const records=[];for(const direction of ['up_left','up','up_right','down_right']){
 const root=path.join(__dirname,'package');
 const computed=await sharp(path.join(root,`source/walk_${direction}_joint_edit_raw_v011.png`)).resize(256,192,{kernel:'nearest'}).ensureAlpha().raw().toBuffer();
 for(let i=0;i<computed.length;i+=4){if(computed[i+3]<160){computed.fill(0,i,i+4);continue;}
  let best=pal[0],distance=Infinity;for(const c of pal){let d=0;for(let k=0;k<3;k++)d+=(c[k]-computed[i+k])**2;if(d<distance){distance=d;best=c;}}computed.set([...best,255],i);
 }
 const actual=await sharp(path.join(root,`source/walk_${direction}_joint_edit_quantized_v011.png`)).ensureAlpha().raw().toBuffer();let mismatch=0;for(let i=0;i<actual.length;i+=4)if(!actual.subarray(i,i+4).equals(computed.subarray(i,i+4)))mismatch++;
 records.push({direction,rgba_mismatch:mismatch});
 }await fs.writeFile(path.join(__dirname,'raw-quantized-source-binding.json'),JSON.stringify({scope:'CPU decoded source proof only, no GPU/browser/engine',nearest_api:'Sharp/Vips declared producer API, independently invoked without producer functions',records},null,2));console.log(JSON.stringify(records));})().catch(e=>{console.error(e);process.exitCode=1;});
