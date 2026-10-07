/* 只读结构诊断：按真实八邻域Alpha计算脱块，结合GPU owner标记定位。
 * 绝不写PNG、填洞、对齐或修改任何源像素。连通也不代表美术/动作通过。 */
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const sharp = require("C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp");
const options = Object.fromEntries(process.argv.slice(2).map(value => value.replace(/^--/, "").split("=")));
const live = path.resolve(__dirname, "..");
const base = options.base ? path.resolve(options.base) : live;
const rigPath = path.join(live, "source/rig_down_v009.json");
const rig = JSON.parse(fs.readFileSync(rigPath, "utf8"));
const hash = file => crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const ownerName = id => id >= 100 ? rig.cap_definitions[id - 100]?.id : rig.parts[id - 1]?.id;
(async () => {
  const frames = [];
  for (let frame = 0; frame < 8; frame++) {
    const stem = String(frame).padStart(2, "0");
    const file = path.join(base, `frames/robot_walk_down_f${stem}_v009.png`);
    const ownerFile = path.join(base, `owner_maps/walk_down_f${stem}_owner_v009.png`);
    const {data, info} = await sharp(file).ensureAlpha().raw().toBuffer({resolveWithObject: true});
    const owners = await sharp(ownerFile).ensureAlpha().raw().toBuffer();
    const seen = new Set(), components = [];
    for (let index = 0; index < info.width * info.height; index++) {
      if (seen.has(index) || data[index * 4 + 3] === 0) continue;
      const stack = [index], counts = {};
      let count = 0, x0 = 64, x1 = 0, y0 = 96, y1 = 0;
      seen.add(index);
      while (stack.length) {
        const current = stack.pop(), x = current % info.width, y = Math.floor(current / info.width);
        count++; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
        const owner = ownerName(owners[current * 4]) || "UNREGISTERED_OWNER";
        counts[owner] = (counts[owner] || 0) + 1;
        for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
          const xx = x + dx, yy = y + dy;
          if (xx < 0 || xx >= info.width || yy < 0 || yy >= info.height) continue;
          const next = yy * info.width + xx;
          if (!seen.has(next) && data[next * 4 + 3] > 0) { seen.add(next); stack.push(next); }
        }
      }
      components.push({pixel_count: count, bbox_xywh: [x0, y0, x1 - x0 + 1, y1 - y0 + 1], owners: counts});
    }
    components.sort((a, b) => b.pixel_count - a.pixel_count);
    frames.push({frame, file: path.relative(base, file), sha256: hash(file), owner_map_sha256: hash(ownerFile), components,
      all_visible_pixels_one_component: components.length === 1});
  }
  const report = {status: "STRUCTURAL_DIAGNOSTIC_NO_ART_ACCEPTANCE", source_rig_sha256: hash(rigPath),
    frame_render_report_sha256: hash(path.join(base, "fixed_rig_render_v009.json")),
    inspector_sha256: hash(__filename), connectivity: "eight_neighbor_real_RGBA_alpha", frames,
    detached_frames: frames.filter(frame => !frame.all_visible_pixels_one_component).map(frame => frame.frame),
    art_acceptance: "NOT_CLAIMED", note: "An Alpha component check cannot prove joint volume, art quality, gait, or target style."};
  fs.writeFileSync(path.join(base, "alpha_structure_diagnostic_v009.json"), JSON.stringify(report, null, 2) + "\n");
  process.stdout.write(JSON.stringify({base, detached_frames: report.detached_frames,
    components_per_frame: frames.map(frame => frame.components.map(component => component.pixel_count))}));
})();
