/*
 * v008 固定原生母稿步态的格式导出与只读测量。
 * 不裁 bbox、不齐底、不重居中、不修 Alpha、不改姿态；1× PNG 复制原字节，
 * 4× 仅复制每个完整画布像素为 4×4 块。编码 PASS 不代表动作或关节 TA 通过。
 * 固定root与世界接地/屏幕接触位置分开登记，不假定支撑脚屏幕y恒为80。
 * node tools/export_robot_fixed_rig_v008.cjs --root=<v008源目录>
 *      --sharp-module=<sharp模块目录>
 */
const fs = require("node:fs/promises");
const path = require("node:path");
const crypto = require("node:crypto");

const W = 64;
const H = 96;
const COUNT = 8;
const FPS = 8;
const REVISION = "robot_fixed_rig_v008";
const STEM = "robot_walk_down_fixed_rig_v008";
const SOURCE_NAME = "source/robot_idle_down_canonical_original.png";
const CANONICAL_SHA256 = "c65f68455554edb03aea0a7b7b3cea6e1a779fa9d5aa49cba9b4aa5c4f6fbfff";
const REQUIRED_IDENTITY_PARTS = ["head", "chest", "left_wrist_tool"];
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
  args.root = path.resolve(args.root || path.join(process.cwd(), "art-source/ember/robot-fixed-rig-v008"));
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

function grayChecker(raw) {
  const output = checker(raw);
  for (let at = 0; at < raw.length; at += 4) {
    if (raw[at + 3] !== 255) continue;
    const value = Math.round((raw[at] * 299 + raw[at + 1] * 587 + raw[at + 2] * 114) / 1000);
    output[at] = value; output[at + 1] = value; output[at + 2] = value;
  }
  return output;
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

function stablePartObservation(canonical, raw, pose, name, diagnostic, ownerEvidence) {
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
  // owner 图中存在但没有确定源 UV 的像素，保持 Unknown 并另用琥珀色显示。
  // unseen 是投影/遮挡未见的源像素，不能擅自全部解释为遮挡或稳定。
  const unknownOwnerPixels = [];
  let actualOwnerPixels = null;
  if (ownerEvidence) {
    actualOwnerPixels = 0;
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
      const at = (y * W + x) * 4;
      if (ownerEvidence.raw[at] !== ownerEvidence.id || ownerEvidence.raw[at + 3] !== 255) continue;
      actualOwnerPixels++;
      if (!uniqueDestinationPixels.has(`${x},${y}`)) {
        unknownOwnerPixels.push([x, y]);
        const amber = [226, 166, 67, 255];
        for (let c = 0; c < 4; c++) diagnostic[at + c] = amber[c];
      }
    }
    if (actualOwnerPixels !== part.visible_gpu_owner_pixels || unknownOwnerPixels.length !== part.unknown_rgba_samples) {
      throw new Error(`owner图与pose的实际可见/未知采样数量不一致：${name}`);
    }
  }
  const unseen = Number.isInteger(part.unseen_source_pixel_count) ? part.unseen_source_pixel_count : null;
  const unknown = Number.isInteger(part.unknown_rgba_samples) ? part.unknown_rgba_samples : null;
  const coverage = unseen === null || unknown === null || !ownerEvidence ? "UNKNOWN_EVIDENCE"
    : (unseen > 0 || unknown > 0 ? "PARTIAL_UNKNOWN" : "ALL_SOURCE_PIXELS_OBSERVED");
  return { status: checked.length === 0 ? "UNKNOWN" : (duplicateDestinations > 0 ? "INVALID_DUPLICATE_DESTINATION_MAPPING" : (mismatch === 0 ? "VISIBLE_PIXELS_MATCH_SOURCE" : "VISIBLE_PIXEL_MISMATCH")),
    visible_checked_pixels: checked.length, visible_source_rgba_mismatch: mismatch,
    visible_unique_source_pixels: uniqueSourcePixels.size, visible_unique_destination_pixels: uniqueDestinationPixels.size,
    duplicate_destination_mapping_count: duplicateDestinations,
    coverage_status: coverage, unseen_source_pixel_count: unseen,
    unseen_source_classification: part.unseen_source_classification ?? "UNKNOWN",
    unseen_stability: unseen === 0 ? "NOT_APPLICABLE" : "UNKNOWN",
    declared_unknown_rgba_samples: unknown, actual_unknown_owner_pixels: unknownOwnerPixels,
    actual_visible_gpu_owner_pixels: actualOwnerPixels,
    unknown_rgba_stability: unknown === 0 ? "NOT_APPLICABLE" : "UNKNOWN",
    source_pixel_count: part.source_pixel_count ?? null, transform_note: part.transform_note ?? null,
    mapping_sha256: sha256(Buffer.from(JSON.stringify(part.visible_source_pixels))),
    scope: "只验证该姿态有确定源UV的实际可见像素，允许登记关节变换/骨盆bob；未见源像素和采样边界不确定像素仍Unknown，不证明完整角色或动作。" };
}

function contactPixelObservations(raw, pose) {
  const observed = {};
  for (const side of ["left", "right"]) {
    const contact = pose?.contacts?.[side];
    const point = contact?.registered_contact_pixel;
    const valid = Array.isArray(point) && point.length >= 2 && point.slice(0, 2).every(Number.isInteger)
      && point[0] >= 0 && point[0] < W && point[1] >= 0 && point[1] < H;
    const alpha = valid ? raw[(point[1] * W + point[0]) * 4 + 3] : null;
    const declaredAlpha = contact?.actual_gpu_contact_pixel_alpha;
    const gpuAlphaSampled = Number.isInteger(declaredAlpha) && declaredAlpha >= 0 && declaredAlpha <= 255;
    observed[side] = { status: valid ? "PIXEL_OBSERVED" : "UNKNOWN", registered_contact_pixel: point ?? null,
      actual_png_alpha_at_registered_contact_pixel: alpha,
      declared_gpu_contact_pixel_alpha: declaredAlpha ?? null,
      declared_gpu_alpha_sampled: gpuAlphaSampled,
      png_alpha_matches_declared_gpu_alpha: valid && gpuAlphaSampled ? alpha === declaredAlpha : null,
      declared_stance: contact?.stance ?? null, declared_sole_world: contact?.sole_world ?? null,
      declared_sole_projected: contact?.sole_projected ?? null,
      scope: "只在pose登记的实际接触像素读取原PNG Alpha；世界接地与投影位置取声明，不从bbox或屏幕y80推断。" };
  }
  return observed;
}

async function main() {
  const args = options();
  const sharp = require(args["sharp-module"] || "sharp");
  const previews = path.join(args.root, "previews");
  const qa = path.join(args.root, "qa");
  await fs.mkdir(previews, { recursive: true });
  await fs.mkdir(qa, { recursive: true });
  const reportPath = path.join(qa, "export_validation_v008.json");
  const encoderHash = sha256(await fs.readFile(__filename));
  const outputs = [];
  const inputs = [];
  const frames = [];
  const checkerFrames = [];
  const diagnosticFrames = [];
  const observations = [];
  const missingIdentityEvidence = [];
  const sourcePath = path.join(args.root, SOURCE_NAME);
  const sourceBytes = await fs.readFile(sourcePath);
  const canonical = await rgba(sharp, sourceBytes);
  const sourceHash = sha256(sourceBytes);
  if (sourceHash !== CANONICAL_SHA256) throw new Error("v008固定原生母稿SHA与冻结的原idle_down不一致；不对重绘母稿继续导出。");
  const sourceMetadata = [];
  for (const relative of ["source/rig_down_v008.json", "source/part_masks_v008.json", "source/robot_idle_down_fixed_rig_canonical_v008.png"]) {
    try {
      const bytes = await fs.readFile(path.join(args.root, relative));
      sourceMetadata.push({ file: relative, sha256: sha256(bytes) });
    } catch (error) { if (error.code !== "ENOENT") throw error; }
  }
  const rig = await readJson(path.join(args.root, "source/rig_down_v008.json"));
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
      const relative = `frames/robot_walk_down_f${suffix}_v008.png`;
      const poseRelative = `poses/walk_down_f${suffix}_v008.json`;
      const bytes = await fs.readFile(path.join(args.root, relative));
      const raw = await rgba(sharp, bytes);
      const measurement = measure(raw);
      if (!measurement.binary_alpha) throw new Error(`正式PNG连续Alpha：${relative}`);
      const posePath = path.join(args.root, poseRelative);
      let pose = null, poseHash = null;
      try { const poseBytes = await fs.readFile(posePath); poseHash = sha256(poseBytes); pose = JSON.parse(poseBytes.toString("utf8").replace(/^\uFEFF/, "")); }
      catch (error) { if (error.code !== "ENOENT") throw error; }
      const rigMetadata = sourceMetadata.find((entry) => entry.file === "source/rig_down_v008.json");
      if (pose?.source_rig_sha256 && rigMetadata && pose.source_rig_sha256 !== rigMetadata.sha256) {
        throw new Error(`pose使用的rig与当前源不一致：${poseRelative}`);
      }
      // renderer 的 owner pass 为 rig.parts 顺序 + 1 的红通道整数 ID。
      // 读取真实 owner PNG，只给诊断图标注边界未知，不改正式 PNG 的像素。
      const ownerRelative = `owner_maps/walk_down_f${suffix}_owner_v008.png`;
      const ownerBytes = await fs.readFile(path.join(args.root, ownerRelative));
      const ownerHash = sha256(ownerBytes);
      if (pose?.owner_map_sha256 !== ownerHash) throw new Error(`pose与实际owner图SHA不匹配：${ownerRelative}`);
      const ownerRaw = await rgba(sharp, ownerBytes);
      const diagnostic = grayChecker(raw);
      const stable = {};
      const observedParts = REQUIRED_IDENTITY_PARTS.concat(["hand_left", "hand_right"].filter((name) => pose?.stable_parts?.[name]));
      for (const name of observedParts) {
        const partId = name === "chest" ? "chest_shell" : name;
        const ownerIndex = rig.parts.findIndex((part) => part.id === partId);
        if (ownerIndex < 0) throw new Error(`rig中没有身份诊断部件：${partId}`);
        stable[name] = stablePartObservation(canonical, raw, pose, name, diagnostic, { raw: ownerRaw, id: ownerIndex + 1 });
        if (stable[name].visible_checked_pixels > 0) knownStableMappings++;
        if (REQUIRED_IDENTITY_PARTS.includes(name) && (stable[name].status !== "VISIBLE_PIXELS_MATCH_SOURCE" || stable[name].coverage_status !== "ALL_SOURCE_PIXELS_OBSERVED")) {
          missingIdentityEvidence.push({ frame: index, part: name, visible_status: stable[name].status,
            coverage_status: stable[name].coverage_status, unseen_source_pixel_count: stable[name].unseen_source_pixel_count,
            unknown_rgba_samples: stable[name].declared_unknown_rgba_samples,
            reason: stable[name].reason || "可见的确定源UV像素已检查；未见源像素/采样边界仍Unknown，不能标完整身份稳定PASS。" });
        }
      }
      inputs.push({ index, file: relative, sha256: sha256(bytes), rgba_sha256: sha256(raw), pose_file: pose ? poseRelative : null, pose_sha256: poseHash,
        owner_map_file: ownerRelative, owner_map_sha256: ownerHash });
      observations.push({ index, file: relative, ...measurement,
        declared_root_anchor: pose?.root_anchor ?? null, declared_phase: pose?.phase ?? null,
        declared_support_leg: pose?.support_leg ?? null, declared_contacts: pose?.contacts ?? null,
        contact_evidence: pose?.contacts ? "WORLD_AND_PROJECTED_CONTACTS_DECLARED_IN_POSE_SCREEN_Y_NOT_ASSUMED_80" : "UNKNOWN",
        contact_pixel_observations: contactPixelObservations(raw, pose),
        declared_camera_projection: pose?.camera_projection ?? null, declared_keypoints3d: pose?.keypoints3d ?? null,
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
      const twoLoops = scaledChecker.concat(scaledChecker);
      const twoLoopDelays = gifDelays.concat(gifDelays);
      const twoLoopFile = path.join(previews, `${STEM}_two_normal_loops_${factor}x.gif`);
      await sharp(Buffer.concat(twoLoops), { raw: { width, height: height * twoLoops.length, channels: 4, pageHeight: height } })
        .gif({ colours: 256, effort: 7, dither: 0, loop: 0, delay: twoLoopDelays,
          keepDuplicateFrames: true, interFrameMaxError: 0, interPaletteMaxError: 0 }).toFile(twoLoopFile);
      await recordOutput(twoLoopFile, "TWO_NORMAL_FPS_LOOPS_CHECKER_GIF", { factor, width, height, nominal_fps: FPS, encoded_source_loops: 2,
        ...await checkAnimated(sharp, twoLoopFile, twoLoops, width, height, twoLoopDelays) });
      const slowFile = path.join(previews, `${STEM}_slow_frame_review_${factor}x.gif`);
      const slowDelays = Array(COUNT).fill(1000);
      await sharp(Buffer.concat(scaledChecker), rawOptions).gif({ colours: 256, effort: 7, dither: 0, loop: 0, delay: slowDelays,
        keepDuplicateFrames: true, interFrameMaxError: 0, interPaletteMaxError: 0 }).toFile(slowFile);
      await recordOutput(slowFile, "SLOW_FRAME_REVIEW_ONLY_GIF", { factor, width, height, diagnostic_fps: 1, formal_animation_fps: FPS,
        ...await checkAnimated(sharp, slowFile, scaledChecker, width, height, slowDelays),
        scope: "每帧1000ms慢检查图；不改变正式8FPS，不插帧，不作为正常速度动作通过的依据。" });
      for (const [label, cells] of [["transparent", scaledFrames], ["checker", scaledChecker]]) {
        await png(path.join(previews, `${STEM}_contact_${label}_${factor}x.png`), contactSheet(cells, width, height), width * 4, height * 2,
          { factor, columns: 4, rows: 2, cell_size: [width, height], trimmed: false, repositioned: false });
      }
      if (knownStableMappings > 0) {
        const cells = diagnosticFrames.map((raw) => nearest(raw, factor));
        await png(path.join(previews, `${STEM}_stable_visible_diagnostic_${factor}x.png`), contactSheet(cells, width, height), width * 4, height * 2,
          { factor, diagnostic_only: true, legend: "灰化角色为参照；青绿=已核对的head/chest/tool及手部确定源UV像素；琥珀=实际owner可见但源UV采样不确定；红=已登记映射不符。未见源像素不宣称稳定。" });
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
<title>v008 固定母稿步态候选</title><style>
body{margin:32px;background:#11181e;color:#e4e9e6;font:15px/1.65 system-ui,sans-serif}main{max-width:1050px;margin:auto}h1{font-size:24px;margin:0}p{color:#b5c3c5}button,input{font:inherit}button{background:#344b58;color:#edf1e8;border:1px solid #647e86;border-radius:4px;padding:5px 14px;cursor:pointer}.controls{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:20px 0}.views{display:flex;gap:36px;flex-wrap:wrap;align-items:flex-start}figure{margin:0}canvas{display:block;image-rendering:pixelated;background-color:#222a32;background-image:linear-gradient(45deg,#2f363d 25%,transparent 25%),linear-gradient(-45deg,#2f363d 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#2f363d 75%),linear-gradient(-45deg,transparent 75%,#2f363d 75%);background-size:16px 16px;background-position:0 0,0 8px,8px -8px,-8px 0}#native{width:64px;height:96px}#large,#master{width:256px;height:384px;background-size:64px 64px;background-position:0 0,0 32px,32px -32px,-32px 0}figcaption{margin:8px 0;color:#afc3c8}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#1a252e;border:1px solid #3e5662;padding:16px}a{color:#9ad0c7}
</style><main><h1>固定原生母稿 · 正向行走 v008</h1><p>CANDIDATE：8 帧，8 FPS，64×96 完整原生画布。未裁边、齐底或重居中；ENCODING_PASS 仅表示格式保真，动作与关节需独立 TA 审查。</p>
<div class="controls"><button id="play">暂停</button><button id="previous">上一帧</button><button id="next">下一帧</button><label>速度 <select id="speed"><option value="8">正常8FPS</option><option value="1">慢逐帧1FPS</option></select></label><label>帧 <input id="frame" type="range" min="0" max="7" value="0" step="1"></label><span id="label">F00</span><span id="cycles">完整循环0</span><label><input id="guide" type="checkbox">显示 root/声明接触点</label></div>
<div class="views"><figure><canvas id="native" width="64" height="96"></canvas><figcaption>原生 1× · 完整格</figcaption></figure><figure><canvas id="large" width="256" height="384"></canvas><figcaption>整数 Nearest 4× · 完整格</figcaption></figure><figure><canvas id="master" width="256" height="384"></canvas><figcaption>同一原母稿 · 原字节</figcaption></figure></div>
<p>固定 root 与支撑脚世界/屏幕接触点分开显示。接触点取 pose 的斜俯投影声明，支撑脚屏幕 y 可以变化；不按 bbox 调图。头胸和工具只检查实际可见的源像素，遮挡部分仍未知。请先以正常8FPS看至少两次完整循环，再慢逐帧查看F07→F00。</p><pre id="details"></pre>
<p><a href="${STEM}_contact_checker_4x.png">8 帧 4× 联系图</a> · <a href="${STEM}_transparent_1x.webp">透明无损 WebP</a> · <a href="${STEM}_two_normal_loops_4x.gif">正常速度两次循环</a> · <a href="${STEM}_slow_frame_review_4x.gif">慢逐帧诊断</a> · <a href="../qa/export_validation_v008.json">编码核验</a></p></main>
<script>const observations=${reviewData};let images=[],frame=0,playing=true,epoch=performance.now(),interval=125;const slider=document.getElementById('frame'),button=document.getElementById('play'),guide=document.getElementById('guide');
function draw(){if(!images.length)return;const m=observations[frame];for(const [name,factor] of [['native',1],['large',4]]){const canvas=document.getElementById(name),ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(images[frame],0,0,64*factor,96*factor);if(guide.checked){const root=m.declared_root_anchor;if(Array.isArray(root)){ctx.fillStyle='#b7e7d4';ctx.fillRect((Math.round(root[0])-1)*factor,(Math.round(root[1])-1)*factor,2*factor,2*factor);}for(const side of ['left','right']){const contact=m.declared_contacts&&m.declared_contacts[side],point=contact&&contact.sole_projected;if(!Array.isArray(point))continue;ctx.fillStyle=contact.stance?'#a9d8a8':'#ddb487';ctx.fillRect((Math.round(point[0])-1)*factor,Math.round(point[1])*factor,3*factor,factor);}}}slider.value=frame;document.getElementById('label').textContent='F'+String(frame).padStart(2,'0');document.getElementById('details').textContent=JSON.stringify({frame,phase:m.declared_phase,support_leg:m.declared_support_leg,root:m.declared_root_anchor,projection:m.declared_camera_projection,contacts:m.declared_contacts,contact_pixel_observations:m.contact_pixel_observations,actual_bbox:m.bbox_xywh,visible_bottom_boundary:m.visible_bottom_boundary_y,head_visible_check:m.stable_parts.head,chest_visible_check:m.stable_parts.chest,tool_visible_check:m.stable_parts.left_wrist_tool},null,2);}
button.onclick=()=>{playing=!playing;button.textContent=playing?'暂停':'播放';epoch=performance.now()-frame*interval;};function seek(index){playing=false;button.textContent='播放';frame=(index+8)%8;draw();}slider.oninput=()=>seek(Number(slider.value));document.getElementById('previous').onclick=()=>seek(frame-1);document.getElementById('next').onclick=()=>seek(frame+1);document.getElementById('speed').onchange=event=>{interval=1000/Number(event.target.value);epoch=performance.now()-frame*interval;document.getElementById('cycles').textContent='完整循环0';};guide.onchange=draw;
Promise.all(Array.from({length:8},(_,i)=>new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('缺少固定格PNG F'+i));image.src='png_sequence_1x/robot_walk_down_f'+String(i).padStart(2,'0')+'_v008.png';}))).then(loaded=>{images=loaded;draw();const original=new Image();original.onload=()=>{const ctx=document.getElementById('master').getContext('2d');ctx.imageSmoothingEnabled=false;ctx.drawImage(original,0,0,256,384);};original.src='canonical_original_bytes_copy.png';}).catch(error=>document.getElementById('details').textContent=error.message);
function tick(now){if(playing&&images.length){const step=Math.floor((now-epoch)/interval),index=step%8;document.getElementById('cycles').textContent='完整循环'+Math.floor(step/8);if(index!==frame){frame=index;draw();}}requestAnimationFrame(tick);}requestAnimationFrame(tick);</script></html>`;
    const reviewPath = path.join(previews, "review_fixed_rig_v008.html");
    await fs.writeFile(reviewPath, html, "utf8");
    await recordOutput(reviewPath, "FIXED_CELL_INTERACTIVE_REVIEW", { candidate_status: "CANDIDATE", fps: FPS, frame_count: COUNT });
    await fs.writeFile(path.join(previews, ".gdignore"), "Browser animation previews and diagnostic PNGs; not production textures.\n");

    // 最后读回原文件SHA，证明本脚本未改母稿、帧或姿态。
    if (sha256(await fs.readFile(sourcePath)) !== sourceHash) throw new Error("原生母稿被改动。");
    for (const entry of inputs) {
      if (sha256(await fs.readFile(path.join(args.root, entry.file))) !== entry.sha256) throw new Error(`源帧被改动：${entry.file}`);
      if (entry.pose_file && sha256(await fs.readFile(path.join(args.root, entry.pose_file))) !== entry.pose_sha256) throw new Error(`pose被改动：${entry.pose_file}`);
      if (sha256(await fs.readFile(path.join(args.root, entry.owner_map_file))) !== entry.owner_map_sha256) throw new Error(`owner图被改动：${entry.owner_map_file}`);
    }
    for (const entry of sourceMetadata) {
      if (sha256(await fs.readFile(path.join(args.root, entry.file))) !== entry.sha256) throw new Error(`源标注被改动：${entry.file}`);
    }
    const measurements = { revision: REVISION, status: "OBSERVED_ONLY", candidate_status: "CANDIDATE",
      encoder_sha256: encoderHash, source_file: SOURCE_NAME, source_sha256: sourceHash, source_metadata: sourceMetadata,
      canvas: [W, H], fps: FPS, fixed_root_declaration: [32, 80], frames: observations,
      scope: "逐帧原始bbox/颜色/二值Alpha；固定root、世界接地与屏幕投影分开登记，支撑脚屏幕y不假定为80；读取pose接触像素的实际PNG Alpha；可见母稿像素实查，遮挡/缺映射为UNKNOWN。不能代替关节、身份和步态TA验收。" };
    const measurementsPath = path.join(qa, "export_pose_measurements_v008.json");
    await fs.writeFile(measurementsPath, JSON.stringify(measurements, null, 2) + "\n");
    const report = { revision: REVISION, status: "ENCODING_PASS", candidate_status: "CANDIDATE", animation_art_status: "PENDING_INDEPENDENT_TA",
      encoder_sha256: encoderHash, source_file: SOURCE_NAME, source_sha256: sourceHash, source_rgba_sha256: sha256(canonical),
      canvas: [W, H], full_cell: true, trim: false, recenter: false, per_frame_ground_alignment: false,
      alpha_repair: "NONE", pose_drawing_or_translation: "NONE", fps: FPS, frame_count: COUNT,
      duration_ms: 1000, webp_delays_ms: exactDelays, gif_delays_ms: gifDelays,
      inputs, source_metadata: sourceMetadata, outputs, measurements_file: slash(path.relative(args.root, measurementsPath)), measurements_sha256: sha256(await fs.readFile(measurementsPath)),
      source_png_and_pose_sha_unchanged: true, stable_parts_mappings_observed: knownStableMappings,
      required_identity_parts: REQUIRED_IDENTITY_PARTS, missing_identity_evidence: missingIdentityEvidence,
      scope: "仅PNG复制/完整格nearest放大/无损WebP/GIF时轴与RGBA色Alpha实查。ENCODING_PASS不表示动作、骨架或关节通过。" };
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2) + "\n");
    console.log(`ROBOT_FIXED_RIG_V008 ENCODING_PASS frames=${COUNT} full_cell=${W}x${H} outputs=${outputs.length}`);
  } catch (error) {
    await fs.writeFile(reportPath, JSON.stringify({ revision: REVISION, status: "ENCODING_FAIL", candidate_status: "CANDIDATE",
      animation_art_status: "NOT_ACCEPTED", encoder_sha256: encoderHash, error: error.message, inputs, outputs }, null, 2) + "\n");
    throw error;
  }
}

main().catch((error) => { console.error(error.stack || error.message); process.exitCode = 1; });

