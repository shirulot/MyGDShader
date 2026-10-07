/*
 * v007 固定原生母稿步态的格式导出与只读测量。
 * 不裁 bbox、不齐底、不重居中、不修 Alpha、不改姿态；1× PNG 复制原字节，
 * 4× 仅复制每个完整画布像素为 4×4 块。编码 PASS 不代表动作或关节 TA 通过。
 * node tools/export_robot_fixed_rig_v007.cjs --root=<v007源目录>
 *      --sharp-module=<sharp模块目录>
 */
const fs = require("node:fs/promises");
const path = require("node:path");
const crypto = require("node:crypto");

const W = 64;
const H = 96;
const COUNT = 8;
const FPS = 8;
const REVISION = "robot_fixed_rig_v007";
const STEM = "robot_walk_down_fixed_rig_v007";
const SOURCE_NAME = "source/robot_idle_down_canonical_original.png";
const CANONICAL_SHA256 = "c65f68455554edb03aea0a7b7b3cea6e1a779fa9d5aa49cba9b4aa5c4f6fbfff";
const sha256 = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const slash = (value) => value.replaceAll("\\", "/");

function options() {
  const args = {};
  for (const token of process.argv.slice(2)) {
    const separator = token.indexOf("=");
    if (!token.startsWith("--") || separator < 3) throw new Error(`未知参数：${token}`);
    const key = token.slice(2, separator);
    if (!["root", "sharp-module"].includes(key)) throw new Error(`未知参数：${key}`);
    args[key] = token.slice(separator + 1);
  }
  args.root = path.resolve(args.root || path.join(process.cwd(), "art-source/ember/robot-fixed-rig-v007"));
  return args;
}

async function readJson(file) {
  return JSON.parse((await fs.readFile(file, "utf8")).replace(/^\uFEFF/, ""));
}

async function rgba(sharp, bytes) {
  const result = await sharp(bytes).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  if (result.info.width !== W || result.info.height !== H || result.info.channels !== 4) {
    throw new Error(`原生图必须是 ${W}×${H} RGBA，实际 ${result.info.width}×${result.info.height}×${result.info.channels}`);
  }
  return result.data;
}

function measure(raw) {
  let minX = W, minY = H, maxX = -1, maxY = -1, opaque = 0, intermediate = 0;
  const palette = new Set();
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const at = (y * W + x) * 4;
    const alpha = raw[at + 3];
    if (alpha !== 0 && alpha !== 255) intermediate++;
    if (alpha === 0) continue;
    opaque++;
    minX = Math.min(minX, x); minY = Math.min(minY, y);
    maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
    palette.add(raw.subarray(at, at + 3).toString("hex"));
  }
  return { bbox_xywh: opaque ? [minX, minY, maxX - minX + 1, maxY - minY + 1] : null,
    visible_bottom_boundary_y: opaque ? maxY + 1 : null, opaque_pixels: opaque,
    binary_alpha: intermediate === 0, intermediate_alpha_pixels: intermediate,
    visible_rgb_colors: [...palette].sort(), visible_rgb_color_count: palette.size,
    note: "bbox仅描述实际图像范围，不作为root、支撑脚、重新齐底或身份一致性的依据。" };
}

// 显式最近邻整格放大，避免库默认插值、bbox裁切或自动重定位。
function nearest(raw, factor) {
  if (factor === 1) return Buffer.from(raw);
  const out = Buffer.alloc(W * H * factor * factor * 4);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const from = (y * W + x) * 4;
    for (let yy = 0; yy < factor; yy++) for (let xx = 0; xx < factor; xx++) {
      raw.copy(out, (((y * factor + yy) * W * factor) + x * factor + xx) * 4, from, from + 4);
    }
  }
  return out;
}

function checker(raw) {
  const out = Buffer.from(raw);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const at = (y * W + x) * 4;
    if (raw[at + 3] === 255) continue;
    if (raw[at + 3] !== 0) throw new Error("正式PNG有连续Alpha；不能用checker压平掩盖问题。");
    const value = (Math.floor(x / 8) + Math.floor(y / 8)) % 2 ? 35 : 47;
    out[at] = value; out[at + 1] = value + 3; out[at + 2] = value + 5; out[at + 3] = 255;
  }
  return out;
}

function compare(expected, actual) {
  if (expected.length !== actual.length) throw new Error("解码RGBA长度与完整画布不匹配。");
  let rgbaChanged = 0, alphaChanged = 0, visibleRgbChanged = 0;
  for (let at = 0; at < expected.length; at += 4) {
    const alpha = expected[at + 3] !== actual[at + 3];
    const rgb = expected[at] !== actual[at] || expected[at + 1] !== actual[at + 1] || expected[at + 2] !== actual[at + 2];
    if (alpha || rgb) rgbaChanged++;
    if (alpha) alphaChanged++;
    if (rgb && (expected[at + 3] || actual[at + 3])) visibleRgbChanged++;
  }
  return { rgba_changed_pixels: rgbaChanged, alpha_changed_pixels: alphaChanged, visible_rgb_changed_pixels: visibleRgbChanged };
}

// WebP允许合并相邻完全相同帧；按实际停留区间验证，不把页数变化误判成坏帧。
async function checkAnimated(sharp, file, frames, width, height, expectedDelays) {
  const metadata = await sharp(file, { animated: true }).metadata();
  const result = await sharp(file, { animated: true }).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const delays = metadata.delay || [];
  const duration = (values) => values.reduce((sum, value) => sum + value, 0);
  if (metadata.width !== width || metadata.pageHeight !== height || duration(delays) !== duration(expectedDelays)) {
    throw new Error(`动画尺寸/时轴不匹配：${path.basename(file)}`);
  }
  const frameBytes = width * height * 4;
  if (result.data.length !== frameBytes * delays.length) throw new Error("动画解码页与时长记录不匹配。");
  const comparisons = [];
  let sourceStart = 0, decodedStart = 0, decodedIndex = 0;
  for (let index = 0; index < frames.length; index++) {
    const sourceEnd = sourceStart + expectedDelays[index];
    while (decodedIndex < delays.length && decodedStart + delays[decodedIndex] <= sourceStart) {
      decodedStart += delays[decodedIndex++];
    }
    let testStart = decodedStart, testIndex = decodedIndex;
    while (testStart < sourceEnd) {
      if (testIndex >= delays.length) throw new Error("动画提前结束。");
      const actual = result.data.subarray(testIndex * frameBytes, (testIndex + 1) * frameBytes);
      const metrics = compare(frames[index], actual);
      if (metrics.rgba_changed_pixels !== 0) throw new Error(`动画解码改变颜色/Alpha：${path.basename(file)} / 源帧${index}`);
      comparisons.push({ source_frame: index, decoded_page: testIndex, ...metrics });
      testStart += delays[testIndex++];
    }
    sourceStart = sourceEnd;
  }
  return { decoded_pages: delays.length, delays_ms: delays, total_duration_ms: duration(delays), comparisons,
    exact_rgba: true, exact_alpha: true, exact_visible_rgb: true };
}

function contactSheet(frames, width, height) {
  const out = Buffer.alloc(width * 4 * height * 2 * 4);
  for (let index = 0; index < frames.length; index++) {
    const column = index % 4, row = Math.floor(index / 4);
    for (let y = 0; y < height; y++) {
      const from = y * width * 4;
      frames[index].copy(out, ((row * height + y) * width * 4 + column * width) * 4, from, from + width * 4);
    }
  }
  return out;
}

function stablePartObservation(canonical, raw, pose, name, diagnostic) {
  const part = pose?.stable_parts?.[name] || (name === "chest" ? pose?.stable_parts?.chest_shell : null);
  if (!part || !Array.isArray(part.visible_source_pixels)) {
    return { status: "UNKNOWN", reason: "缺少renderer实际owner提供的可见源像素映射；不从头胸bbox或区域相似性推断稳定。" };
  }
  let mismatch = 0;
  const uniqueSourcePixels = new Set();
  const uniqueDestinationPixels = new Set();
  let duplicateDestinations = 0;
  const checked = [];
  for (const item of part.visible_source_pixels) {
    if (!Array.isArray(item) || item.length < 4) throw new Error(`可见源像素映射格式错误：${name}`);
    const [x, y, sx, sy] = item;
    if (![x, y, sx, sy].every(Number.isInteger) || x < 0 || x >= W || y < 0 || y >= H || sx < 0 || sx >= W || sy < 0 || sy >= H) {
      throw new Error(`可见源像素映射越界：${name}`);
    }
    const from = (sy * W + sx) * 4, to = (y * W + x) * 4;
    uniqueSourcePixels.add(`${sx},${sy}`);
    const destinationKey = `${x},${y}`;
    if (uniqueDestinationPixels.has(destinationKey)) duplicateDestinations++;
    uniqueDestinationPixels.add(destinationKey);
    const equal = canonical.subarray(from, from + 4).equals(raw.subarray(to, to + 4));
    if (!equal) mismatch++;
    checked.push([x, y, sx, sy, equal]);
    // 这是单独的诊断色图；绝不写回原帧。隐藏像素没有映射，不会被当作成功。
    if (!equal || (x + y) % 2 === 0) {
      const color = equal ? [67, 167, 157, 255] : [215, 84, 92, 255];
      for (let c = 0; c < 4; c++) diagnostic[to + c] = color[c];
    }
  }
  const occluded = Number.isInteger(part.occluded_source_pixel_count) ? part.occluded_source_pixel_count : null;
  return { status: checked.length === 0 ? "UNKNOWN" : (duplicateDestinations > 0 ? "INVALID_DUPLICATE_DESTINATION_MAPPING" : (mismatch === 0 ? "VISIBLE_PIXELS_MATCH_SOURCE" : "VISIBLE_PIXEL_MISMATCH")),
    visible_checked_pixels: checked.length, visible_source_rgba_mismatch: mismatch,
    visible_unique_source_pixels: uniqueSourcePixels.size, visible_unique_destination_pixels: uniqueDestinationPixels.size,
    duplicate_destination_mapping_count: duplicateDestinations,
    occluded_source_pixel_count: occluded, occluded_stability: occluded === 0 ? "NOT_APPLICABLE" : "UNKNOWN",
    source_pixel_count: part.source_pixel_count ?? null, transform_note: part.transform_note ?? null,
    mapping_sha256: sha256(Buffer.from(JSON.stringify(part.visible_source_pixels))),
    scope: "只验证该姿态实际可见像素相对登记的母稿源位置，允许登记关节变换/骨盆bob；遮挡部分未知，不证明完整动作。" };
}

async function main() {
  const args = options();
  const sharp = require(args["sharp-module"] || "sharp");
  const previews = path.join(args.root, "previews");
  const qa = path.join(args.root, "qa");
  await fs.mkdir(previews, { recursive: true });
  await fs.mkdir(qa, { recursive: true });
  const reportPath = path.join(qa, "export_validation_v007.json");
  const encoderHash = sha256(await fs.readFile(__filename));
  const outputs = [];
  const inputs = [];
  const frames = [];
  const checkerFrames = [];
  const diagnosticFrames = [];
  const observations = [];
  const sourcePath = path.join(args.root, SOURCE_NAME);
  const sourceBytes = await fs.readFile(sourcePath);
  const canonical = await rgba(sharp, sourceBytes);
  const sourceHash = sha256(sourceBytes);
  if (sourceHash !== CANONICAL_SHA256) throw new Error("v007固定原生母稿SHA与冻结的原idle_down不一致；不对重绘母稿继续导出。");
  const sourceMetadata = [];
  for (const relative of ["source/rig_down_v007.json", "source/part_masks_v007.json"]) {
    try {
      const bytes = await fs.readFile(path.join(args.root, relative));
      sourceMetadata.push({ file: relative, sha256: sha256(bytes) });
    } catch (error) { if (error.code !== "ENOENT") throw error; }
  }
  let knownStableMappings = 0;
  const exactDelays = Array(COUNT).fill(125);
  // GIF只能记录10ms单位，120/130交替保留整秒；本意仍为每帧125ms的8FPS。
  const gifDelays = Array.from({ length: COUNT }, (_, i) => 10 * (Math.round((i + 1) * 100 / FPS) - Math.round(i * 100 / FPS)));

  async function recordOutput(file, type, extra = {}) {
    const bytes = await fs.readFile(file);
    const entry = { file: slash(path.relative(args.root, file)), type, bytes: bytes.length, sha256: sha256(bytes), ...extra };
    outputs.push(entry); return entry;
  }
  async function png(file, raw, width, height, extra = {}) {
    await sharp(raw, { raw: { width, height, channels: 4 } }).png().toFile(file);
    const actual = await sharp(file).ensureAlpha().raw().toBuffer();
    const metrics = compare(raw, actual);
    if (metrics.rgba_changed_pixels) throw new Error(`PNG输出改变完整格像素：${path.basename(file)}`);
    return recordOutput(file, "PNG", { width, height, ...metrics, ...extra });
  }

  try {
    for (let index = 0; index < COUNT; index++) {
      const suffix = String(index).padStart(2, "0");
      const relative = `frames/robot_walk_down_f${suffix}_v007.png`;
      const poseRelative = `poses/walk_down_f${suffix}_v007.json`;
      const bytes = await fs.readFile(path.join(args.root, relative));
      const raw = await rgba(sharp, bytes);
      const measurement = measure(raw);
      if (!measurement.binary_alpha) throw new Error(`正式PNG连续Alpha：${relative}`);
      const posePath = path.join(args.root, poseRelative);
      let pose = null, poseHash = null;
      try { const poseBytes = await fs.readFile(posePath); poseHash = sha256(poseBytes); pose = JSON.parse(poseBytes.toString("utf8").replace(/^\uFEFF/, "")); }
      catch (error) { if (error.code !== "ENOENT") throw error; }
      const rigMetadata = sourceMetadata.find((entry) => entry.file === "source/rig_down_v007.json");
      if (pose?.source_rig_sha256 && rigMetadata && pose.source_rig_sha256 !== rigMetadata.sha256) {
        throw new Error(`pose使用的rig与当前源不一致：${poseRelative}`);
      }
      const diagnostic = checker(raw);
      const stable = {};
      for (const name of ["head", "chest"]) {
        stable[name] = stablePartObservation(canonical, raw, pose, name, diagnostic);
        if (stable[name].visible_checked_pixels > 0) knownStableMappings++;
      }
      inputs.push({ index, file: relative, sha256: sha256(bytes), rgba_sha256: sha256(raw), pose_file: pose ? poseRelative : null, pose_sha256: poseHash });
      observations.push({ index, file: relative, ...measurement,
        declared_root_anchor: pose?.root_anchor ?? null, declared_phase: pose?.phase ?? null,
        declared_support_leg: pose?.support_leg ?? null, declared_contacts: pose?.contacts ?? null,
        contact_evidence: pose?.contacts ? "POSE_DECLARATION_ONLY_NOT_INFERRED_FROM_BBOX" : "UNKNOWN",
        declared_pelvis_bob: pose?.pelvis_bob ?? null, keypoints_projected: pose?.keypoints_projected ?? null,
        bone_measures: pose?.bone_measures ?? null, stable_parts: stable });
      frames.push(raw); checkerFrames.push(checker(raw)); diagnosticFrames.push(diagnostic);
      const nativeDir = path.join(previews, "png_sequence_1x");
      const fourDir = path.join(previews, "png_sequence_4x");
      await fs.mkdir(nativeDir, { recursive: true }); await fs.mkdir(fourDir, { recursive: true });
      const nativeOutput = path.join(nativeDir, path.basename(relative));
      await fs.writeFile(nativeOutput, bytes);
      await recordOutput(nativeOutput, "PNG_SOURCE_BYTES_COPY", { width: W, height: H, factor: 1, byte_identical_to_source: true });
      await png(path.join(fourDir, path.basename(relative).replace(".png", "_4x.png")), nearest(raw, 4), W * 4, H * 4, { factor: 4 });
    }

    for (const factor of [1, 4]) {
      const width = W * factor, height = H * factor;
      const scaledFrames = frames.map((raw) => nearest(raw, factor));
      const scaledChecker = checkerFrames.map((raw) => nearest(raw, factor));
      const rawOptions = { raw: { width, height: height * COUNT, channels: 4, pageHeight: height } };
      const webpFile = path.join(previews, `${STEM}_transparent_${factor}x.webp`);
      await sharp(Buffer.concat(scaledFrames), rawOptions).webp({ lossless: true, effort: 6, loop: 0, delay: exactDelays }).toFile(webpFile);
      const webpChecks = await checkAnimated(sharp, webpFile, scaledFrames, width, height, exactDelays);
      await recordOutput(webpFile, "ANIMATED_LOSSLESS_WEBP", { factor, width, height, ...webpChecks });
      const gifFile = path.join(previews, `${STEM}_checker_${factor}x.gif`);
      await sharp(Buffer.concat(scaledChecker), rawOptions).gif({ colours: 256, effort: 7, dither: 0, loop: 0, delay: gifDelays,
        keepDuplicateFrames: true, interFrameMaxError: 0, interPaletteMaxError: 0 }).toFile(gifFile);
      const gifChecks = await checkAnimated(sharp, gifFile, scaledChecker, width, height, gifDelays);
      await recordOutput(gifFile, "ANIMATED_CHECKER_GIF", { factor, width, height, ...gifChecks,
        duration_note: "GIF以10ms存储帧时长，120/130ms交替；PNG/无损WebP每帧精确125ms。" });
      for (const [label, cells] of [["transparent", scaledFrames], ["checker", scaledChecker]]) {
        await png(path.join(previews, `${STEM}_contact_${label}_${factor}x.png`), contactSheet(cells, width, height), width * 4, height * 2,
          { factor, columns: 4, rows: 2, cell_size: [width, height], trimmed: false, repositioned: false });
      }
      if (knownStableMappings > 0) {
        const cells = diagnosticFrames.map((raw) => nearest(raw, factor));
        await png(path.join(previews, `${STEM}_stable_visible_diagnostic_${factor}x.png`), contactSheet(cells, width, height), width * 4, height * 2,
          { factor, diagnostic_only: true, legend: "青绿=已核对的可见源像素；红=不符；未着色的遮挡/未登记部分不宣称稳定。" });
      }
    }

    // 固定格图集元数据，无trim/rotation；这只是导出描述，不自动创建生产SpriteFrames。
    const atlasMetadata = { revision: REVISION, candidate_status: "CANDIDATE", animation_art_status: "NOT_REVIEWED_BY_EXPORTER",
      canvas: [W, H], fps: FPS, duration_ms: 1000, root_anchor: [32, 80], layout: [4, 2],
      frames: inputs.map((entry) => ({ index: entry.index, filename: entry.file, frame: { x: (entry.index % 4) * W, y: Math.floor(entry.index / 4) * H, w: W, h: H },
        sourceSize: { w: W, h: H }, spriteSourceSize: { x: 0, y: 0, w: W, h: H }, rotated: false, trimmed: false, duration: 125, sha256: entry.sha256 })) };
    const metadataPath = path.join(previews, `${STEM}_atlas_metadata.json`);
    await fs.writeFile(metadataPath, JSON.stringify(atlasMetadata, null, 2) + "\n");
    await recordOutput(metadataPath, "FIXED_CELL_METADATA");
    // 审阅页只显示固定整格PNG，暂停/逐帧查看；参考图也复制原字节，不制作新姿态。
    const masterPreviewPath = path.join(previews, "canonical_original_bytes_copy.png");
    await fs.writeFile(masterPreviewPath, sourceBytes);
    await recordOutput(masterPreviewPath, "PNG_SOURCE_BYTES_COPY", { width: W, height: H, factor: 1, byte_identical_to_canonical_source: true });
    const reviewData = JSON.stringify(observations).replaceAll("<", "\\u003c");
    const html = `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>v007 固定母稿步态候选</title><style>
body{margin:32px;background:#11181e;color:#e4e9e6;font:15px/1.65 system-ui,sans-serif}main{max-width:1050px;margin:auto}h1{font-size:24px;margin:0}p{color:#b5c3c5}button,input{font:inherit}button{background:#344b58;color:#edf1e8;border:1px solid #647e86;border-radius:4px;padding:5px 14px;cursor:pointer}.controls{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:20px 0}.views{display:flex;gap:36px;flex-wrap:wrap;align-items:flex-start}figure{margin:0}canvas{display:block;image-rendering:pixelated;background-color:#222a32;background-image:linear-gradient(45deg,#2f363d 25%,transparent 25%),linear-gradient(-45deg,#2f363d 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#2f363d 75%),linear-gradient(-45deg,transparent 75%,#2f363d 75%);background-size:16px 16px;background-position:0 0,0 8px,8px -8px,-8px 0}#native{width:64px;height:96px}#large,#master{width:256px;height:384px;background-size:64px 64px;background-position:0 0,0 32px,32px -32px,-32px 0}figcaption{margin:8px 0;color:#afc3c8}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#1a252e;border:1px solid #3e5662;padding:16px}a{color:#9ad0c7}
</style><main><h1>固定原生母稿 · 正向行走 v007</h1><p>CANDIDATE：8 帧，8 FPS，64×96 完整原生画布。未裁边、齐底或重居中；ENCODING_PASS 仅表示格式保真，动作与关节需独立 TA 审查。</p>
<div class="controls"><button id="play">暂停</button><label>帧 <input id="frame" type="range" min="0" max="7" value="0" step="1"></label><span id="label">F00</span><label><input id="guide" type="checkbox">显示登记 root/地面参考线</label></div>
<div class="views"><figure><canvas id="native" width="64" height="96"></canvas><figcaption>原生 1× · 完整格</figcaption></figure><figure><canvas id="large" width="256" height="384"></canvas><figcaption>整数 Nearest 4× · 完整格</figcaption></figure><figure><canvas id="master" width="256" height="384"></canvas><figcaption>同一原母稿 · 原字节</figcaption></figure></div>
<p>参考线来自声明的 root=(32,80)，不按 bbox 调图。支撑脚/contact 取 pose 声明；头胸只检查实际可见的源像素，遮挡部分仍未知。</p><pre id="details"></pre>
<p><a href="${STEM}_contact_checker_4x.png">8 帧 4× 联系图</a> · <a href="${STEM}_transparent_1x.webp">透明无损 WebP</a> · <a href="${STEM}_checker_4x.gif">4× GIF</a> · <a href="../qa/export_validation_v007.json">编码核验</a></p></main>
<script>const observations=${reviewData};let images=[],frame=0,playing=true,epoch=performance.now();const slider=document.getElementById('frame'),button=document.getElementById('play'),guide=document.getElementById('guide');
function draw(){if(!images.length)return;for(const [name,factor] of [['native',1],['large',4]]){const canvas=document.getElementById(name),ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(images[frame],0,0,64*factor,96*factor);if(guide.checked){ctx.fillStyle='#de916a';ctx.fillRect(0,80*factor,64*factor,factor);ctx.fillStyle='#b7e7d4';ctx.fillRect(31*factor,79*factor,2*factor,2*factor);}}slider.value=frame;document.getElementById('label').textContent='F'+String(frame).padStart(2,'0');const m=observations[frame];document.getElementById('details').textContent=JSON.stringify({frame,phase:m.declared_phase,support_leg:m.declared_support_leg,root:m.declared_root_anchor,contacts:m.declared_contacts,actual_bbox:m.bbox_xywh,visible_bottom_boundary:m.visible_bottom_boundary_y,head_visible_check:m.stable_parts.head,chest_visible_check:m.stable_parts.chest},null,2);}
button.onclick=()=>{playing=!playing;button.textContent=playing?'暂停':'播放';epoch=performance.now()-frame*125;};slider.oninput=()=>{playing=false;button.textContent='播放';frame=Number(slider.value);draw();};guide.onchange=draw;
Promise.all(Array.from({length:8},(_,i)=>new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('缺少固定格PNG F'+i));image.src='png_sequence_1x/robot_walk_down_f'+String(i).padStart(2,'0')+'_v007.png';}))).then(loaded=>{images=loaded;draw();const original=new Image();original.onload=()=>{const ctx=document.getElementById('master').getContext('2d');ctx.imageSmoothingEnabled=false;ctx.drawImage(original,0,0,256,384);};original.src='canonical_original_bytes_copy.png';}).catch(error=>document.getElementById('details').textContent=error.message);
function tick(now){if(playing&&images.length){const index=Math.floor((now-epoch)/125)%8;if(index!==frame){frame=index;draw();}}requestAnimationFrame(tick);}requestAnimationFrame(tick);</script></html>`;
    const reviewPath = path.join(previews, "review_fixed_rig_v007.html");
    await fs.writeFile(reviewPath, html, "utf8");
    await recordOutput(reviewPath, "FIXED_CELL_INTERACTIVE_REVIEW", { candidate_status: "CANDIDATE", fps: FPS, frame_count: COUNT });
    await fs.writeFile(path.join(previews, ".gdignore"), "Browser animation previews and diagnostic PNGs; not production textures.\n");

    // 最后读回原文件SHA，证明本脚本未改母稿、帧或姿态。
    if (sha256(await fs.readFile(sourcePath)) !== sourceHash) throw new Error("原生母稿被改动。");
    for (const entry of inputs) {
      if (sha256(await fs.readFile(path.join(args.root, entry.file))) !== entry.sha256) throw new Error(`源帧被改动：${entry.file}`);
      if (entry.pose_file && sha256(await fs.readFile(path.join(args.root, entry.pose_file))) !== entry.pose_sha256) throw new Error(`pose被改动：${entry.pose_file}`);
    }
    for (const entry of sourceMetadata) {
      if (sha256(await fs.readFile(path.join(args.root, entry.file))) !== entry.sha256) throw new Error(`源标注被改动：${entry.file}`);
    }
    const measurements = { revision: REVISION, status: "OBSERVED_ONLY", candidate_status: "CANDIDATE",
      encoder_sha256: encoderHash, source_file: SOURCE_NAME, source_sha256: sourceHash, source_metadata: sourceMetadata,
      canvas: [W, H], fps: FPS, fixed_root_declaration: [32, 80], frames: observations,
      scope: "逐帧原始bbox/颜色/二值Alpha；root和支撑脚仅来自pose声明；可见母稿像素实查，遮挡/缺映射为UNKNOWN。不能代替关节、身份和步态TA验收。" };
    const measurementsPath = path.join(qa, "export_pose_measurements_v007.json");
    await fs.writeFile(measurementsPath, JSON.stringify(measurements, null, 2) + "\n");
    const report = { revision: REVISION, status: "ENCODING_PASS", candidate_status: "CANDIDATE", animation_art_status: "PENDING_INDEPENDENT_TA",
      encoder_sha256: encoderHash, source_file: SOURCE_NAME, source_sha256: sourceHash, source_rgba_sha256: sha256(canonical),
      canvas: [W, H], full_cell: true, trim: false, recenter: false, per_frame_ground_alignment: false,
      alpha_repair: "NONE", pose_drawing_or_translation: "NONE", fps: FPS, frame_count: COUNT,
      duration_ms: 1000, webp_delays_ms: exactDelays, gif_delays_ms: gifDelays,
      inputs, source_metadata: sourceMetadata, outputs, measurements_file: slash(path.relative(args.root, measurementsPath)), measurements_sha256: sha256(await fs.readFile(measurementsPath)),
      source_png_and_pose_sha_unchanged: true, stable_parts_mappings_observed: knownStableMappings,
      scope: "仅PNG复制/完整格nearest放大/无损WebP/GIF时轴与RGBA色Alpha实查。ENCODING_PASS不表示动作、骨架或关节通过。" };
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2) + "\n");
    console.log(`ROBOT_FIXED_RIG_V007 ENCODING_PASS frames=${COUNT} full_cell=${W}x${H} outputs=${outputs.length}`);
  } catch (error) {
    await fs.writeFile(reportPath, JSON.stringify({ revision: REVISION, status: "ENCODING_FAIL", candidate_status: "CANDIDATE",
      animation_art_status: "NOT_ACCEPTED", encoder_sha256: encoderHash, error: error.message, inputs, outputs }, null, 2) + "\n");
    throw error;
  }
}

main().catch((error) => { console.error(error.stack || error.message); process.exitCode = 1; });
