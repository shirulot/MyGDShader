/*
 * 将 Godot 已渲染的 PNG 序列编码成动画预览。
 * 不裁切、不缩放、不重绘角色。WebP 使用无损编码，解码后逐字节核对；
 * GIF 另查登记角色色是否变化，避免动画预览中黄铜工具闪色。
 * 用法：node tools/encode_robot_preview_v003.cjs --frames=<目录>
 *       --output=<输出目录> --fps=12 --sharp-module=<sharp模块目录>
 */
const fs = require("node:fs/promises");
const path = require("node:path");
const crypto = require("node:crypto");

function options() {
  const result = {};
  for (const value of process.argv.slice(2)) {
    const split = value.indexOf("=");
    if (value.startsWith("--") && split > 2) {
      result[value.slice(2, split)] = value.slice(split + 1);
    }
  }
  if (!result.frames || !result.output) throw new Error("需要 --frames 和 --output");
  result.fps = Number(result.fps || 12);
  if (!Number.isFinite(result.fps) || result.fps <= 0 || result.fps > 60) {
    throw new Error("fps 必须在 0..60 之间");
  }
  return result;
}

const sha256 = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");

async function main() {
  const args = options();
  const sharp = require(args["sharp-module"] || "sharp");
  const names = (await fs.readdir(args.frames)).filter((name) => /\.png$/i.test(name)).sort();
  if (names.length < 2) throw new Error("需要至少两张有序 Godot PNG");
  const sourceRecords = [];
  const sourceBuffers = [];
  let width = 0;
  let height = 0;
  for (const name of names) {
    const bytes = await fs.readFile(path.join(args.frames, name));
    const decoded = await sharp(bytes).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
    if (!width) ({ width, height } = decoded.info);
    if (decoded.info.width !== width || decoded.info.height !== height || decoded.info.channels !== 4) {
      throw new Error(`帧规格不一致：${name}`);
    }
    sourceBuffers.push(decoded.data);
    sourceRecords.push({ file: name, sha256: sha256(bytes) });
  }
  const raw = Buffer.concat(sourceBuffers);
  sourceBuffers.length = 0;
  const settings = { raw: { width, height: height * names.length, channels: 4, pageHeight: height } };
  const exactDelays = names.map((_, i) => Math.round((i + 1) * 1000 / args.fps) - Math.round(i * 1000 / args.fps));
  const gifDelays = names.map((_, i) => 10 * (Math.round((i + 1) * 100 / args.fps) - Math.round(i * 100 / args.fps)));
  await fs.mkdir(args.output, { recursive: true });
  const webpPath = path.join(args.output, "robot_actions_loop_v003.webp");
  const gifPath = path.join(args.output, "robot_actions_loop_v003.gif");
  await sharp(raw, settings).webp({ lossless: true, effort: 6, loop: 0, delay: exactDelays }).toFile(webpPath);
  const webpDecoded = await sharp(webpPath, { animated: true }).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const webpMeta = await sharp(webpPath, { animated: true }).metadata();
  const bytesPerFrame = width * height * 4;
  // WebP 编码器可能把相邻相同帧合并成更长的停留时间。
  // 按时间区间检查所有重叠帧，可同时证明合并后颜色和播放时长都没有变化。
  const decodedDelays = webpMeta.delay || [];
  if (decodedDelays.reduce((a, b) => a + b, 0) !== exactDelays.reduce((a, b) => a + b, 0)) {
    throw new Error("无损 WebP 与原 PNG 时轴长度不一致");
  }
  let sourceStart = 0;
  let decodedStart = 0;
  let decodedIndex = 0;
  for (let sourceIndex = 0; sourceIndex < names.length; sourceIndex += 1) {
    const sourceEnd = sourceStart + exactDelays[sourceIndex];
    while (decodedStart + decodedDelays[decodedIndex] <= sourceStart) {
      decodedStart += decodedDelays[decodedIndex++];
    }
    let comparisonIndex = decodedIndex;
    let comparisonStart = decodedStart;
    while (comparisonStart < sourceEnd) {
      const expected = raw.subarray(sourceIndex * bytesPerFrame, (sourceIndex + 1) * bytesPerFrame);
      const actual = webpDecoded.data.subarray(comparisonIndex * bytesPerFrame, (comparisonIndex + 1) * bytesPerFrame);
      if (!expected.equals(actual)) throw new Error(`无损 WebP 第 ${sourceIndex} 个时间区间的 RGBA 不一致`);
      comparisonStart += decodedDelays[comparisonIndex++];
    }
    sourceStart = sourceEnd;
  }
  await sharp(raw, settings).gif({ colours: 256, effort: 7, dither: 0, loop: 0, delay: gifDelays,
    keepDuplicateFrames: true, interFrameMaxError: 0, interPaletteMaxError: 0 }).toFile(gifPath);
  const gifDecoded = await sharp(gifPath, { animated: true }).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const palette = new Set(["101820", "182631", "2b3e4b", "4d6470", "829ba3", "becbc4", "7b4d35", "b77c4b", "e2b77a", "566b78", "ece9d8"]
    .map((hex) => parseInt(hex, 16)));
  let nativePaletteSamples = 0;
  let nativePaletteMismatch = 0;
  if (gifDecoded.data.length !== raw.length) throw new Error("GIF 解码帧数不一致");
  for (let i = 0; i < raw.length; i += 4) {
    const rgb = (raw[i] << 16) | (raw[i + 1] << 8) | raw[i + 2];
    if (raw[i + 3] !== 255 || !palette.has(rgb)) continue;
    nativePaletteSamples += 1;
    if (raw[i] !== gifDecoded.data[i] || raw[i + 1] !== gifDecoded.data[i + 1]
      || raw[i + 2] !== gifDecoded.data[i + 2] || gifDecoded.data[i + 3] !== 255) nativePaletteMismatch += 1;
  }
  const report = { status: nativePaletteMismatch === 0 ? "PASS" : "WEBP_PASS_GIF_PALETTE_MISMATCH",
    scope: "Format encoding only; source PNG pixels unchanged", width, height, frames: names.length,
    fps: args.fps, encoder_sha256: sha256(await fs.readFile(__filename)),
    source_frames: sourceRecords, webp_exact_rgba: true,
    webp_decoded_pages: webpMeta.pages, webp_decoded_delays_ms: decodedDelays, native_palette_samples: nativePaletteSamples,
    gif_native_palette_mismatch: nativePaletteMismatch, webp_delays_ms: exactDelays, gif_delays_ms: gifDelays,
    outputs: { webp: { file: path.basename(webpPath), sha256: sha256(await fs.readFile(webpPath)) },
      gif: { file: path.basename(gifPath), sha256: sha256(await fs.readFile(gifPath)) } } };
  await fs.writeFile(path.join(args.output, "preview_encoding_v003.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(`ROBOT_PREVIEW ${report.status} frames=${names.length} gif_palette_mismatch=${nativePaletteMismatch}`);
}

main().catch((error) => { console.error(error.message); process.exitCode = 1; });
