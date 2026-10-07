// 自有审查仅采样固定ZIP复制出的中间源，不调用生产生成/合成脚本。
const fs=require('node:fs/promises');
const path=require('node:path');
const sharp=require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
(async()=>{
 const data=await sharp(path.join(__dirname,'neutral-imagegen-source.png'))
  .resize(64,96,{kernel:'nearest'}).ensureAlpha().raw().toBuffer();
 await fs.writeFile(path.join(__dirname,'neutral-patch-nearest.rgba'),data);
})().catch(e=>{console.error(e);process.exitCode=1;});
