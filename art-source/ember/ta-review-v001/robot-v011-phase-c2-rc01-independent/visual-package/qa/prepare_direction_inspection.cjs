// 仅为分区审阅做最近邻放大和坐标叠加，不修改源母版。
const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root = path.resolve(__dirname, '..');
async function run() {
  for (const direction of ['left', 'up_left', 'up', 'up_right', 'right', 'down_right']) {
    const source = path.join(root, 'source/candidate-masters', `robot_idle_${direction}_v011.png`);
    await sharp(source).resize(512, 768, {kernel: 'nearest'}).png()
      .toFile(path.join(__dirname, `master_${direction}_8x.png`));
    const grid = [];
    for (let x = 0; x <= 64; x += 4) grid.push(`<line x1="${x*8}" y1="0" x2="${x*8}" y2="768" stroke="#d16a47" stroke-opacity=".3"/><text x="${x*8+2}" y="14" fill="#171f28" font-size="11">${x}</text>`);
    for (let y = 0; y <= 96; y += 4) grid.push(`<line x1="0" y1="${y*8}" x2="512" y2="${y*8}" stroke="#d16a47" stroke-opacity=".3"/><text x="2" y="${y*8+12}" fill="#171f28" font-size="11">${y}</text>`);
    const svg = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="768">${grid.join('')}</svg>`);
    await sharp(source).resize(512,768,{kernel:'nearest'}).flatten({background:'#cecbbb'}).composite([{input:svg}]).png()
      .toFile(path.join(__dirname, `master_${direction}_grid_8x.png`));
  }
}
run().catch(error => {console.error(error);process.exitCode=1;});
