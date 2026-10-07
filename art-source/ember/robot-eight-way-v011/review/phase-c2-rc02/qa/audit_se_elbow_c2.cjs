// 只追踪东南肘外侧原像素的来源、变换与补丁变化，不修改任何素材。
const fs = require('node:fs/promises'), path = require('node:path');
const sharp = require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const {stamp} = require('../build_fixed_rig_v011.cjs');
const root = path.resolve(__dirname, '..');
const raw = async file => sharp(path.join(root, file)).ensureAlpha().raw().toBuffer();
(async () => {
  const registration = JSON.parse(await fs.readFile(path.join(root, 'source/action-source-registration/down_right/registration.json'), 'utf8'));
  const ledger = JSON.parse(await fs.readFile(path.join(root, 'source/action-rig-batch/collect/down_right/rig_and_poses.json'), 'utf8'));
  const parts = {};
  for (const part of registration.parts) parts[part.id] = await raw(part.file);
  const frames = [];
  for (let frame = 0; frame < 4; frame++) {
    const file = `robot_collect_down_right_f0${frame}_v011.png`;
    const base = await raw('source/action-rig-batch/collect/down_right/' + file);
    const final = await raw('frames/collect/down_right/' + file);
    const layers = {};
    for (const [id, part] of Object.entries(parts)) { const layer = Buffer.alloc(64*96*4); stamp(layer, part, ledger.states[frame].transforms[id]); layers[id] = layer; }
    const pixels = [];
    for (let y = 47; y <= 62; y++) for (let x = 12; x <= 15; x++) {
      const at = (y*64+x)*4;
      if (!final[at+3]) continue;
      pixels.push({x,y,rgba:[...final.subarray(at,at+4)],same_as_unedited_rig:final.subarray(at,at+4).equals(base.subarray(at,at+4)),rig_source_layers:Object.entries(layers).filter(([,layer])=>layer[at+3]).map(([id])=>id)});
    }
    frames.push({frame,pixels});
  }
  const report = {scope:'SE collect elbow outer edge x12..15 y47..62',mutations:false,frames};
  await fs.writeFile(path.join(root,'qa/se_elbow_c2_origin.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report));
})().catch(error=>{console.error(error);process.exitCode=1;});
