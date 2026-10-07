// TA独立脚本：在制作方明确的Sharp Nearest采样契约下核整张源板，不运行生产脚本。
const fs=require('node:fs/promises'),path=require('node:path'),crypto=require('node:crypto');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=__dirname,base=path.join(root,'package/source');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const palette=['101820','182631','2B3E4B','4D6470','829BA3','BECBC4','566B78','ECE9D8','7B4D35','B77C4B','E2B77A'].map(h=>[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)));
(async()=>{
 const source=await fs.readFile(path.join(base,'walk_down_left_joint_edit_raw_v011.png'));
 const target=await fs.readFile(path.join(base,'walk_down_left_joint_edit_quantized_v011.png'));
 const sampled=await sharp(source).resize(256,192,{kernel:'nearest'}).ensureAlpha().raw().toBuffer();
 const actual=await sharp(target).ensureAlpha().raw().toBuffer();
 for(let at=0;at<sampled.length;at+=4){
  if(sampled[at+3]<160){sampled.fill(0,at,at+4);continue;}
  let best=palette[0],distance=Infinity;
  for(const color of palette){
   const score=color.reduce((n,v,i)=>n+(v-sampled[at+i])**2,0);
   if(score<distance){distance=score;best=color;}
  }
  sampled.set([...best,255],at);
 }
 let mismatch=0;
 for(let at=0;at<actual.length;at+=4)if(!sampled.subarray(at,at+4).equals(actual.subarray(at,at+4)))mismatch++;
 const result={status:mismatch?'SOURCE_SAMPLING_DIFFERENCE':'SOURCE_SHEET_CONTRACT_ZERO_DIFF',method:'declared Sharp Nearest whole-sheet sampling; independent quantization / comparison',
  source_sha256:sha(source),quantized_png_sha256:sha(target),recomputed_raw_sha256:sha(sampled),stored_quantized_raw_sha256:sha(actual),
  full_rgba_different_pixels:mismatch,source_transform:'1448x1086 -> 256x192 once; not per-frame normalization',
  sampling_library:sharp.versions};
 await fs.writeFile(path.join(root,'patch-source-sharp-contract.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));
 if(mismatch)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
