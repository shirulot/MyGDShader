// Alpha 连通只用于定位碎点或独立部件，不能替代关节的视觉审查。
const fs=require('node:fs/promises'),path=require('node:path');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root=path.resolve(__dirname,'..'),W=64,H=96;
function components(raw){const seen=new Uint8Array(W*H),out=[];for(let start=0;start<W*H;start++){
  if(seen[start]||!raw[start*4+3])continue;const q=[start];seen[start]=1;let x0=W,x1=0,y0=H,y1=0;
  for(let j=0;j<q.length;j++){const n=q[j],x=n%W,y=Math.floor(n/W);x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);
    for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){const xx=x+dx,yy=y+dy,k=yy*W+xx;if(xx>=0&&xx<W&&yy>=0&&yy<H&&!seen[k]&&raw[k*4+3]){seen[k]=1;q.push(k);}}
  }out.push({pixels:q.length,bbox:[x0,y0,x1,y1],indices:q});
}return out.sort((a,b)=>b.pixels-a.pixels);}
module.exports={components};
if(require.main===module)(async()=>{for(const d of process.argv.slice(2)){let warnings=[];for(let i=0;i<8;i++){
 const name=`robot_walk_${d}_f${String(i).padStart(2,'0')}_v011.png`;
 for(const folder of['source/fixed-rig-pilot','frames/walk']){const raw=await sharp(path.join(root,folder,d,name)).ensureAlpha().raw().toBuffer();const c=components(raw);if(c.length>1)warnings.push({frame:i,kind:folder,components:c.map(({indices,...rest})=>rest)});}
}console.log(JSON.stringify({direction:d,warnings}));}})().catch(e=>{console.error(e);process.exitCode=1;});
