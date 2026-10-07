// Independent read-only sampler. Uses the declared Sharp nearest kernel only;
// palette quantization and composite checks are independently computed in Python.
const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const out = __dirname;
const input = path.join(out, 'package/art-source/ember/robot-joint-repair-v010/source/joint_edit_raw_v010.png');
async function run() {
  const sample = await sharp(input).resize(256, 192, {kernel:'nearest', fit:'fill'}).ensureAlpha().raw().toBuffer();
  await fs.writeFile(path.join(out, 'independent_patch_sample.rgba'), sample);
  process.stdout.write(`sample_bytes=${sample.length}\n`);
}
run().catch(error => { process.stderr.write(String(error)); process.exitCode = 1; });
