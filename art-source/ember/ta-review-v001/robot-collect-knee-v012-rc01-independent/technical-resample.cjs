// TA 只读生成源，记录统一整张缩放后的真实 RGBA；不做逐帧 fit 或修改交付。
const fs=require('node:fs/promises'),path=require('node:path');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
async function run(){const root=__dirname,p=path.join(root,'technical-package'),ledger=JSON.parse(await fs.readFile(path.join(p,'source/imagegen-ledger.json'),'utf8')),records=[];
for(const e of ledger){const input=path.join(p,e.source),m=await sharp(input).metadata();await sharp(input).resize(128,192,{kernel:'nearest'}).ensureAlpha().png().toFile(path.join(root,`technical-resampled-${e.direction}.png`));records.push({direction:e.direction,width:m.width,height:m.height,hasAlpha:m.hasAlpha,scale:[128/m.width,192/m.height]});}
await fs.writeFile(path.join(root,'technical-resample.json'),JSON.stringify(records,null,2));console.log(JSON.stringify(records));}
run().catch(e=>{console.error(e);process.exitCode=1;});
