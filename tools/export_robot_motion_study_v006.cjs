/*
 * v006 动作试样的格式导出器，不是像素修图器。
 * 唯一生产像素操作：按母图固定 4×2 网格等分取出完整单格并无损保存 PNG。
 * 不裁角色 bbox、不删除透明碎片、不补接头、不自动对齐、不改旧游戏素材。
 * WebP 从这八张原始格子的 RGBA 编码；GIF 的棋盘背景仅供预览。
 * 64×96 文件是全组相同变换的缩小诊断，明确不能称为原生角色资源。
 * 用法：node tools/export_robot_motion_study_v006.cjs
 *       --master=<母图PNG> --output=<试样目录> --sharp-module=<Sharp模块目录>
 */
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');

const FRAME_COUNT = 8;
const COLS = 4;
const ROWS = 2;
const FPS = 8;
const sha256 = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');
const absolute = (file) => path.resolve(file);

function parseOptions() {
  const args = {};
  for (const argument of process.argv.slice(2)) {
    const equal = argument.indexOf('=');
    if (!argument.startsWith('--') || equal < 3) throw new Error(`参数需写成 --key=value：${argument}`);
    const key = argument.slice(2, equal);
    if (!['master', 'output', 'sharp-module', 'review-only'].includes(key)) throw new Error(`未知参数：${key}`);
    args[key] = argument.slice(equal + 1);
  }
  if (!args.master || !args.output) throw new Error('必须提供 --master 与 --output');
  args.master = absolute(args.master);
  args.output = absolute(args.output);
  return args;
}

// Buffer 逐行复制保证固定格取像素；没有按角色内容决定剪裁或锚点。
function cropRaw(master, sourceWidth, left, top, width, height) {
  const result = Buffer.alloc(width * height * 4);
  for (let y = 0; y < height; y += 1) {
    const start = ((top + y) * sourceWidth + left) * 4;
    master.copy(result, y * width * 4, start, start + width * 4);
  }
  return result;
}

function measureAlpha(raw, width, height) {
  const histogram = Array(256).fill(0);
  let minX = width, minY = height, maxX = -1, maxY = -1, opaqueBottom = -1;
  let weightedX = 0, weightedY = 0, weight = 0, borderSamples = 0;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const alpha = raw[(y * width + x) * 4 + 3];
      histogram[alpha] += 1;
      if (alpha === 255) opaqueBottom = Math.max(opaqueBottom, y);
      if (alpha === 0) continue;
      minX = Math.min(minX, x); minY = Math.min(minY, y);
      maxX = Math.max(maxX, x); maxY = Math.max(maxY, y);
      weightedX += x * alpha; weightedY += y * alpha; weight += alpha;
      if (x === 0 || y === 0 || x === width - 1 || y === height - 1) borderSamples += 1;
    }
  }
  const empty = maxX < 0;
  return {
    bbox_xywh: empty ? null : [minX, minY, maxX - minX + 1, maxY - minY + 1],
    bbox_xyxy_exclusive: empty ? null : [minX, minY, maxX + 1, maxY + 1],
    alpha_bottom_boundary: empty ? null : maxY + 1,
    fully_opaque_bottom_boundary: opaqueBottom < 0 ? null : opaqueBottom + 1,
    alpha_weighted_centroid: empty ? null : [weightedX / weight, weightedY / weight],
    fully_transparent_pixels: histogram[0], fully_opaque_pixels: histogram[255],
    partial_alpha_pixels: histogram.slice(1, 255).reduce((a, b) => a + b, 0),
    visible_alpha_border_pixels: borderSamples,
    alpha_histogram: histogram.map((count, alpha) => ({ alpha, count })).filter((entry) => entry.count > 0)
  };
}

function difference(expected, actual) {
  if (expected.length !== actual.length) return { rgba_equal: false, size_mismatch: true };
  let alphaChanged = 0, visibleRgbChanged = 0, transparentRgbChanged = 0, rgbaChanged = 0, maxVisibleRgbError = 0;
  for (let offset = 0; offset < expected.length; offset += 4) {
    const alphaDiff = expected[offset + 3] !== actual[offset + 3];
    const rgbError = Math.max(...[0, 1, 2].map((c) => Math.abs(expected[offset + c] - actual[offset + c])));
    if (alphaDiff) alphaChanged += 1;
    if (rgbError > 0 && (expected[offset + 3] > 0 || actual[offset + 3] > 0)) visibleRgbChanged += 1;
    else if (rgbError > 0) transparentRgbChanged += 1;
    if (alphaDiff || rgbError > 0) rgbaChanged += 1;
    if (expected[offset + 3] > 0 || actual[offset + 3] > 0) maxVisibleRgbError = Math.max(maxVisibleRgbError, rgbError);
  }
  return { rgba_equal: rgbaChanged === 0, rgba_changed_pixels: rgbaChanged, alpha_changed_pixels: alphaChanged,
    visible_rgb_changed_pixels: visibleRgbChanged, transparent_rgb_changed_pixels: transparentRgbChanged,
    max_visible_rgb_channel_error: maxVisibleRgbError };
}

function checkerRaw(width, height) {
  const raw = Buffer.alloc(width * height * 4);
  const cell = Math.max(8, Math.round(Math.min(width, height) / 24));
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    const value = (Math.floor(x / cell) + Math.floor(y / cell)) % 2 ? 45 : 60;
    const offset = (y * width + x) * 4;
    raw[offset] = value; raw[offset + 1] = value + 7; raw[offset + 2] = value + 10; raw[offset + 3] = 255;
  }
  return raw;
}

const rawSettings = (width, height) => ({ raw: { width, height, channels: 4 } });
const animationSettings = (width, height, count) => ({ raw: { width, height: height * count, channels: 4, pageHeight: height } });
const gcd = (a, b) => b ? gcd(b, a % b) : a;
const span = (values) => values.length ? Math.max(...values) - Math.min(...values) : null;

async function decode(sharp, input, animated = false) {
  return sharp(input, { animated }).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
}

// 动画编码可合并完全相同的相邻帧，按重叠时间区间检查，不能只按页编号比对。
async function verifyTimeline(sharp, file, sourceFrames, delays, width, height) {
  const metadata = await sharp(file, { animated: true }).metadata();
  const decoded = await decode(sharp, file, true);
  const decodedDelays = metadata.delay || [];
  const bytesPerFrame = width * height * 4;
  const pages = decoded.data.length / bytesPerFrame;
  const duration = delays.reduce((a, b) => a + b, 0);
  const decodedDuration = decodedDelays.reduce((a, b) => a + b, 0);
  if (!Number.isInteger(pages) || pages !== decodedDelays.length || duration !== decodedDuration) {
    return { rgba_equal: false, timing_equal: false, decoded_pages: pages, decoded_delays_ms: decodedDelays,
      source_duration_ms: duration, decoded_duration_ms: decodedDuration, checks: [] };
  }
  let sourceStart = 0, decodedStart = 0, decodedIndex = 0;
  const checks = [];
  for (let sourceIndex = 0; sourceIndex < sourceFrames.length; sourceIndex += 1) {
    const sourceEnd = sourceStart + delays[sourceIndex];
    while (decodedIndex < pages && decodedStart + decodedDelays[decodedIndex] <= sourceStart) {
      decodedStart += decodedDelays[decodedIndex++];
    }
    let comparisonStart = decodedStart, comparisonIndex = decodedIndex;
    while (comparisonStart < sourceEnd && comparisonIndex < pages) {
      const actual = decoded.data.subarray(comparisonIndex * bytesPerFrame, (comparisonIndex + 1) * bytesPerFrame);
      checks.push({ source_frame: sourceIndex, decoded_page: comparisonIndex,
        overlap_ms: [Math.max(sourceStart, comparisonStart), Math.min(sourceEnd, comparisonStart + decodedDelays[comparisonIndex])],
        ...difference(sourceFrames[sourceIndex], actual) });
      comparisonStart += decodedDelays[comparisonIndex++];
    }
    sourceStart = sourceEnd;
  }
  return { rgba_equal: checks.length > 0 && checks.every((entry) => entry.rgba_equal), timing_equal: true,
    source_duration_ms: duration, decoded_duration_ms: decodedDuration, decoded_pages: pages,
    decoded_delays_ms: decodedDelays, decoded_rgba_sha256: sha256(decoded.data), checks };
}

async function saveContact(sharp, frames, width, height, file, diagnostic = false) {
  // 标签和边距全部位于格外；格内仍是完整固定格的棋盘合成预览。
  const padding = 12, labelHeight = 28, header = 44;
  const outWidth = COLS * (width + padding) + padding;
  const outHeight = ROWS * (height + labelHeight + padding) + header + padding;
  const overlays = [];
  const background = checkerRaw(width, height);
  let text = `<text x="12" y="28" fill="#e1e7df" font-size="19">${diagnostic ? 'SCALED DIAGNOSTIC / fixed full cells / not native assets' : 'Generated walk motion study / fixed 4x2 cells / 8 FPS'}</text>`;
  for (let index = 0; index < FRAME_COUNT; index += 1) {
    const left = padding + (index % COLS) * (width + padding);
    const top = header + Math.floor(index / COLS) * (height + labelHeight + padding);
    const preview = await sharp(background, rawSettings(width, height))
      .composite([{ input: frames[index], raw: { width, height, channels: 4 }, left: 0, top: 0 }]).png().toBuffer();
    overlays.push({ input: preview, left, top });
    text += `<text x="${left}" y="${top + height + 20}" fill="#d8e2df" font-size="16">F${String(index).padStart(2, '0')}</text>`;
  }
  overlays.push({ input: Buffer.from(`<svg width="${outWidth}" height="${outHeight}" xmlns="http://www.w3.org/2000/svg"><g font-family="Segoe UI,Arial,sans-serif">${text}</g></svg>`), left: 0, top: 0 });
  await sharp({ create: { width: outWidth, height: outHeight, channels: 4, background: '#182630' } }).composite(overlays).png().toFile(file);
  return { width: outWidth, height: outHeight, display_scope: diagnostic ? 'scaled diagnostic with identical group transform' : 'unscaled full fixed-cell checker preview' };
}

async function encodeAnimation(sharp, frames, width, height, prefix, directory) {
  const exactDelays = frames.map((_, index) => Math.round((index + 1) * 1000 / FPS) - Math.round(index * 1000 / FPS));
  const gifDelays = frames.map((_, index) => 10 * (Math.round((index + 1) * 100 / FPS) - Math.round(index * 100 / FPS)));
  const webpFile = path.join(directory, `${prefix}.webp`);
  await sharp(Buffer.concat(frames), animationSettings(width, height, frames.length))
    .webp({ lossless: true, exact: true, effort: 6, loop: 0, delay: exactDelays }).toFile(webpFile);
  const webpVerification = await verifyTimeline(sharp, webpFile, frames, exactDelays, width, height);
  // GIF 明确合成棋盘并量化，仅用于观看，不再称为透明/原色无损交付。
  const checker = checkerRaw(width, height);
  const checkerFrames = [];
  for (const frame of frames) {
    checkerFrames.push(await sharp(checker, rawSettings(width, height))
      .composite([{ input: frame, raw: { width, height, channels: 4 }, left: 0, top: 0 }]).raw().toBuffer());
  }
  const gifFile = path.join(directory, `${prefix}_checker.gif`);
  await sharp(Buffer.concat(checkerFrames), animationSettings(width, height, checkerFrames.length))
    .gif({ colours: 256, effort: 7, dither: 0, loop: 0, delay: gifDelays, keepDuplicateFrames: true,
      interFrameMaxError: 0, interPaletteMaxError: 0 }).toFile(gifFile);
  const gifVerification = await verifyTimeline(sharp, gifFile, checkerFrames, gifDelays, width, height);
  return { webp: { file: webpFile, sha256: sha256(await fs.readFile(webpFile)), lossless: true, exact_option: true,
    delays_ms: exactDelays, verification: webpVerification },
    gif: { file: gifFile, sha256: sha256(await fs.readFile(gifFile)), checker_background: true, quantized_preview_only: true,
      rgba_lossless_claim: false, colours: 256, delays_ms: gifDelays, verification_against_checker_rgba: gifVerification } };
}

function reviewHtml(width, height, diagnostic) {
  // 浏览器只读八张固定格PNG；原图用天然尺寸，诊断画布用全组同一变换。
  const transform = diagnostic.status === 'SCALED_DIAGNOSTIC_ONLY'
    ? { width: diagnostic.resized_full_cell[0], height: diagnostic.resized_full_cell[1],
      left: diagnostic.shared_padding_left_top[0], top: diagnostic.shared_padding_left_top[1] } : null;
  return `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>机器人 v006 动作试样审阅</title>
<style>
:root{color-scheme:dark;font-family:system-ui,"Microsoft YaHei",sans-serif;background:#111b22;color:#e6e9e4}*{box-sizing:border-box}
body{margin:0;padding:24px;max-width:1200px}h1{font-size:24px;margin:0 0 10px}p{line-height:1.6;margin:8px 0 18px;color:#bac6c8}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:20px}button{border:1px solid #566773;border-radius:7px;padding:9px 16px;background:#293c48;color:#eef1eb;font:inherit;cursor:pointer}button[aria-pressed="true"]{background:#476b77}
label{display:flex;gap:12px;align-items:center}input{width:240px}output{min-width:90px;font-variant-numeric:tabular-nums}
.panels{display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap}.panel{border:1px solid #3e505b;border-radius:10px;overflow:hidden}.panel h2{font-size:17px;margin:0;padding:14px 16px;background:#22323d}.stage{padding:16px;background:#16232c;overflow:auto}.stage.light{background:#f0f0e7}.stage img{display:block;width:${width}px;height:${height}px;max-width:none;image-rendering:pixelated}.stage canvas{display:block;width:256px;height:384px;image-rendering:pixelated}
.caption{max-width:500px;padding:12px 16px;font-size:13px;line-height:1.6;background:#192831;color:#b8c9ca}a{color:#a5d9e1}.status{font-size:14px;color:#d7ba83;margin-top:18px}
</style></head><body>
<h1>机器人 v006 动作试样审阅</h1>
<p>TRIAL：仅观察生成动作。固定 4×2 整格切分，无逐帧对齐、位移、补画或 Alpha 清理。循环 8 FPS，动作尚未获正式素材验收。</p>
<div class="controls"><button id="play" type="button" aria-pressed="true">暂停</button>
<label>帧 <input id="frame" type="range" min="0" max="7" step="1" value="0" aria-label="帧索引"><output id="index">F00 / 07</output></label>
<button id="dark" type="button" aria-pressed="true">深色背景</button><button id="light" type="button" aria-pressed="false">浅色背景</button></div>
<div class="panels"><section class="panel"><h2>原始完整格 · ${width}×${height}</h2><div class="stage"><img id="original" alt="原始完整帧"></div>
<div class="caption">天然尺寸显示，直接加载 frames/ 的透明 PNG。保存了母图固定格完整 RGBA；不裁角色边界。</div></section>
<section class="panel"><h2>64×96 缩小诊断 · 4×显示</h2><div class="stage"><canvas id="diagnostic" width="64" height="96" aria-label="完整格统一缩小诊断"></canvas></div>
<div class="caption">这是缩小检查图，非 native 64×96 素材。全部帧共享同一完整格比例和补边，关闭平滑；没有根据每帧角色位置重新对齐。</div></section></div>
<p class="status" id="status">正在载入八张原始 PNG…</p>
<p><a href="export_motion_study_v006.json">导出核验与实测 JSON</a> · <a href="README.md">使用说明</a></p>
<script>
const TRANSFORM=${JSON.stringify(transform)};
const slider=document.getElementById('frame'),indexLabel=document.getElementById('index'),playButton=document.getElementById('play');
const original=document.getElementById('original'),canvas=document.getElementById('diagnostic'),context=canvas.getContext('2d');
let images=[],playing=true,frame=0;
function render(){
  if(!images.length)return;
  original.src=images[frame].src;
  context.clearRect(0,0,64,96);context.imageSmoothingEnabled=false;
  if(TRANSFORM)context.drawImage(images[frame],0,0,${width},${height},TRANSFORM.left,TRANSFORM.top,TRANSFORM.width,TRANSFORM.height);
  slider.value=String(frame);indexLabel.textContent='F'+String(frame).padStart(2,'0')+' / 07';
}
// 每次计时回调只前进一格；宿主节流时也不会赶帧后反复落在F00。
setInterval(()=>{if(playing&&images.length){frame=(frame+1)%8;render();}},125);
playButton.addEventListener('click',()=>{playing=!playing;playButton.textContent=playing?'暂停':'继续';playButton.setAttribute('aria-pressed',String(playing));});
slider.addEventListener('input',()=>{frame=Number(slider.value);render();});
function setBackground(light){document.querySelectorAll('.stage').forEach(stage=>stage.classList.toggle('light',light));document.getElementById('light').setAttribute('aria-pressed',String(light));document.getElementById('dark').setAttribute('aria-pressed',String(!light));}
document.getElementById('dark').addEventListener('click',()=>setBackground(false));document.getElementById('light').addEventListener('click',()=>setBackground(true));
Promise.all(Array.from({length:8},(_,i)=>new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('PNG加载失败: F'+i));image.src='frames/robot_walk_down_f'+String(i).padStart(2,'0')+'_study_v006.png';}))).then(loaded=>{
  images=loaded;render();document.getElementById('status').textContent='已加载 8 帧 · 原始整格循环 8 FPS · 64×96 仅统一缩小诊断';
}).catch(error=>{document.getElementById('status').textContent=error.message;});
</script></body></html>\n`;
}

async function refreshReviewOnly(sharp, args) {
  // HTML修订单独运行：核验所有已有文件与源字节，绝不重写PNG/GIF/WebP。
  const reportFile = path.join(args.output, 'export_motion_study_v006.json');
  const report = JSON.parse(await fs.readFile(reportFile, 'utf8'));
  const source = await fs.readFile(args.master);
  if (sha256(source) !== report.source.sha256) throw new Error('母图已改变，不能只更新HTML。');
  const decoded = await decode(sharp, source);
  const [width, height] = report.grid.frame_size;
  const rawFrames = [];
  for (const frame of report.frames) {
    if (sha256(await fs.readFile(frame.file)) !== frame.sha256) throw new Error('PNG已改变：' + frame.file);
    const raw = cropRaw(decoded.data, report.source.size[0], frame.source_rect_xywh[0], frame.source_rect_xywh[1], width, height);
    if (!(await decode(sharp, frame.file)).data.equals(raw)) throw new Error('PNG不再与母图固定格RGBA相等。');
    rawFrames.push(raw);
  }
  const files = [report.animation.webp, report.animation.gif, report.contact];
  if (report.scaled_diagnostic.status === 'SCALED_DIAGNOSTIC_ONLY') {
    files.push(report.scaled_diagnostic.animation.webp, report.scaled_diagnostic.animation.gif, report.scaled_diagnostic.contact);
  }
  for (const file of files) if (sha256(await fs.readFile(file.file)) !== file.sha256) throw new Error('预览文件已改变：' + file.file);
  // 重新核验实际WebP时间区间；不会把以前的PASS直接当成此次核验。
  report.animation.webp.verification = await verifyTimeline(sharp, report.animation.webp.file, rawFrames, report.animation.webp.delays_ms, width, height);
  if (!report.animation.webp.verification.rgba_equal || !report.animation.webp.verification.timing_equal) throw new Error('现有WebP时间区间RGBA核验失败。');
  await fs.writeFile(report.review_html.file, reviewHtml(width, height, report.scaled_diagnostic));
  report.review_html.sha256 = sha256(await fs.readFile(report.review_html.file));
  report.review_html.timer = 'sequential setInterval 125ms; no real-time modulo catch-up';
  report.previous_encoding_exporter_sha256 = report.previous_encoding_exporter_sha256 || report.exporter_sha256;
  report.exporter_sha256 = sha256(await fs.readFile(__filename));
  report.html_only_refresh = { all_source_frame_crops_rechecked_rgba: true, webp_timeline_rechecked_rgba: true,
    all_bitmap_files_sha_unchanged: true, no_bitmap_outputs_written: true };
  // 只为使用说明补入口；逐帧审阅正文由root维护，工具不覆写。
  try {
    await fs.access(path.join(args.output, 'visual_review_v006.md'));
    const readmeFile = path.join(args.output, 'README.md');
    const readme = await fs.readFile(readmeFile, 'utf8');
    if (!readme.includes('(visual_review_v006.md)')) {
      await fs.writeFile(readmeFile, readme + '\n逐帧动作局限见[动作审阅记录](visual_review_v006.md)。\n');
    }
  } catch (error) { if (error.code !== 'ENOENT') throw error; }
  await fs.writeFile(reportFile, JSON.stringify(report, null, 2) + '\n');
  console.log('TRIAL_REVIEW_REFRESH frame_pngs=8 bitmaps_unchanged=true webp_rgba=true');
}

async function main() {
  const args = parseOptions();
  const sharp = require(args['sharp-module'] || 'sharp');
  if (args['review-only'] === '1') { await refreshReviewOnly(sharp, args); return; }
  const masterBytes = await fs.readFile(args.master);
  const sourceSha = sha256(masterBytes);
  const metadata = await sharp(masterBytes).metadata();
  const decoded = await decode(sharp, masterBytes);
  const { width, height, channels } = decoded.info;
  if (metadata.format !== 'png' || metadata.depth !== 'uchar') throw new Error('母图必须是8位PNG；不能悄悄降位深或换格式。');
  if (channels !== 4 || width % COLS !== 0 || height % ROWS !== 0) throw new Error('母图必须能按4列2行等分为完整RGBA格。');
  const frameWidth = width / COLS, frameHeight = height / ROWS;
  const framesDirectory = path.join(args.output, 'frames');
  const previewDirectory = path.join(args.output, 'previews');
  await fs.mkdir(framesDirectory, { recursive: true });
  await fs.mkdir(previewDirectory, { recursive: true });
  const frames = [], records = [];
  for (let index = 0; index < FRAME_COUNT; index += 1) {
    const left = (index % COLS) * frameWidth, top = Math.floor(index / COLS) * frameHeight;
    const raw = cropRaw(decoded.data, width, left, top, frameWidth, frameHeight);
    const file = path.join(framesDirectory, `robot_walk_down_f${String(index).padStart(2, '0')}_study_v006.png`);
    await sharp(raw, rawSettings(frameWidth, frameHeight)).png({ compressionLevel: 9 }).toFile(file);
    const readback = await decode(sharp, file);
    const exact = raw.equals(readback.data);
    if (!exact) throw new Error(`无损PNG输出的RGBA改变：F${index}`);
    frames.push(raw);
    records.push({ index, file, sha256: sha256(await fs.readFile(file)), rgba_sha256: sha256(raw),
      grid_cell: [index % COLS, Math.floor(index / COLS)], source_rect_xywh: [left, top, frameWidth, frameHeight],
      size: [frameWidth, frameHeight], master_crop_equals_export_rgba: exact, ...measureAlpha(raw, frameWidth, frameHeight) });
  }
  const animations = await encodeAnimation(sharp, frames, frameWidth, frameHeight, 'robot_walk_down_study_v006', previewDirectory);
  const contactFile = path.join(previewDirectory, 'robot_walk_down_contact_v006.png');
  const contact = await saveContact(sharp, frames, frameWidth, frameHeight, contactFile);
  contact.file = contactFile; contact.sha256 = sha256(await fs.readFile(contactFile));
  // 使用宽高的最大公约数选择精确相同比例；所有格共享同一缩放、同一补边。
  const divisor = gcd(frameWidth, frameHeight), reducedWidth = frameWidth / divisor, reducedHeight = frameHeight / divisor;
  const unit = Math.floor(Math.min(64 / reducedWidth, 96 / reducedHeight));
  let diagnostic = { status: 'SKIPPED', reason: '该宽高比不能在64×96整数画布内精确保持比例。' };
  if (unit > 0) {
    const resizeWidth = reducedWidth * unit, resizeHeight = reducedHeight * unit;
    const left = Math.floor((64 - resizeWidth) / 2), top = Math.floor((96 - resizeHeight) / 2);
    const diagnosticFrames = [];
    for (const frame of frames) {
      const resized = await sharp(frame, rawSettings(frameWidth, frameHeight)).resize(resizeWidth, resizeHeight, { kernel: 'nearest' }).raw().toBuffer();
      const padded = Buffer.alloc(64 * 96 * 4);
      for (let y = 0; y < resizeHeight; y += 1) resized.copy(padded, ((top + y) * 64 + left) * 4, y * resizeWidth * 4, (y + 1) * resizeWidth * 4);
      diagnosticFrames.push(padded);
    }
    const diagnosticAnimation = await encodeAnimation(sharp, diagnosticFrames, 64, 96, 'robot_walk_down_scaled_diagnostic_64x96_v006', previewDirectory);
    const diagnosticFile = path.join(previewDirectory, 'robot_walk_down_scaled_diagnostic_contact_v006.png');
    const diagnosticContact = await saveContact(sharp, diagnosticFrames, 64, 96, diagnosticFile, true);
    diagnostic = { status: 'SCALED_DIAGNOSTIC_ONLY', native_asset_claim: false, full_cell_source_size: [frameWidth, frameHeight],
      target_canvas: [64, 96], resized_full_cell: [resizeWidth, resizeHeight], uniform_scale: unit / divisor,
      shared_padding_left_top: [left, top], kernel: 'nearest', per_frame_alignment: false,
      animation: diagnosticAnimation, contact: { file: diagnosticFile, sha256: sha256(await fs.readFile(diagnosticFile)), ...diagnosticContact } };
  }
  const bottoms = records.map((record) => record.alpha_bottom_boundary).filter((value) => value !== null);
  const opaqueBottoms = records.map((record) => record.fully_opaque_bottom_boundary).filter((value) => value !== null);
  const xCenters = records.filter((record) => record.bbox_xywh).map((record) => record.bbox_xywh[0] + record.bbox_xywh[2] / 2);
  const firstBottom = records[0].alpha_bottom_boundary;
  for (const record of records) record.alpha_bottom_delta_vs_f00 = firstBottom === null || record.alpha_bottom_boundary === null ? null : record.alpha_bottom_boundary - firstBottom;
  const sourceUnchanged = sha256(await fs.readFile(args.master)) === sourceSha;
  if (!sourceUnchanged) throw new Error('导出期间母图文件发生变化，请重新导出。');
  const webpExact = animations.webp.verification.rgba_equal && animations.webp.verification.timing_equal;
  const reviewFile = path.join(args.output, 'review.html');
  await fs.writeFile(reviewFile, reviewHtml(frameWidth, frameHeight, diagnostic));
  const report = { schema_version: 1, status: 'TRIAL', encoding_validation_status: webpExact ? 'PASS' : 'WEBP_RGBA_REVIEW_REQUIRED',
    motion_art_acceptance: 'NOT_APPROVED_FOR_PRODUCTION',
    motion_limitations_from_review: ['F03→F04与F07→F00换步仍较生硬', '抬脚经过相位不充分，动作连续性需进一步修改'],
    scope: 'Generated motion study export only; no game asset integration or art approval.',
    exporter_sha256: sha256(await fs.readFile(__filename)), encoder_versions: sharp.versions,
    source: { file: args.master, sha256: sourceSha, rgba_sha256: sha256(decoded.data), size: [width, height],
      format: metadata.format, depth: metadata.depth, source_has_alpha: Boolean(metadata.hasAlpha), unchanged_after_export: sourceUnchanged },
    grid: { columns: COLS, rows: ROWS, order: 'row-major', count: FRAME_COUNT, frame_size: [frameWidth, frameHeight] },
    registration: { fixed_grid_only: true, bbox_trimmed: false, per_frame_translation: false, alpha_repair: false, repaint: false },
    fps: FPS, all_frame_crops_rgba_equal: records.every((record) => record.master_crop_equals_export_rgba), frames: records,
    drift_measurement: { coordinate_space: 'unchanged full grid cell', foot_proxy: 'lowest alpha>0 pixel boundary; not anatomical foot identification',
      alpha_bottom_range_px: span(bottoms), opaque_bottom_range_px: span(opaqueBottoms), bbox_x_center_range_px: span(xCenters),
      source_values_not_corrected: true }, animation: animations, contact, scaled_diagnostic: diagnostic,
    review_html: { file: reviewFile, sha256: sha256(await fs.readFile(reviewFile)), frames: FRAME_COUNT, fps: FPS,
      natural_size_display: [frameWidth, frameHeight], diagnostic_canvas: [64, 96], diagnostic_display_zoom: 4,
      per_frame_alignment: false, read_only_frame_preview: true },
    review_flags: { source_is_opaque: !metadata.hasAlpha || records.every((record) => record.fully_transparent_pixels === 0),
      has_partial_alpha: records.some((record) => record.partial_alpha_pixels > 0),
      visible_pixels_touch_cell_border: records.some((record) => record.visible_alpha_border_pixels > 0),
      alpha_bottom_changes: span(bottoms) !== 0, no_art_acceptance_claim: true } };
  await fs.writeFile(path.join(args.output, 'export_motion_study_v006.json'), JSON.stringify(report, null, 2) + '\n');
  const readme = `# 机器人行走动作试样 v006\n\n状态为TRIAL。这是生成模型动作试样，供观察关节与连续动作，不是原生64×96正式角色资源，也未接入Godot或替换旧素材。编码核验PASS不代表动作美术验收通过。此次审阅记录中，F03→F04与F07→F00换步仍较生硬，抬脚经过相位不充分；这些局限未通过裁切、位移或补画掩盖。\n\n- \`review.html\`：原始完整格8FPS播放，暂停、0–7滑块和深/浅背景切换；旁边是统一缩小到64×96后4倍显示的诊断。通过本地静态服务打开即可审阅。\n- 母图：\`${args.master}\`，实测${width}×${height}。\n- 固定4列×2行，按行读取F00至F07；完整单格${frameWidth}×${frameHeight}。\n- \`frames/\`：八张透明PNG等分原格；逐RGBA字节核验与母图对应区域相等。未裁角色bbox、移动、对齐、清理碎片或补画。\n- \`previews/robot_walk_down_study_v006.webp\`：透明lossless WebP，8FPS，每帧125ms。逐时间RGBA核验结果为\`${webpExact}\`，详见JSON；若失败，不宣称编码保留全RGBA。\n- \`previews/robot_walk_down_study_v006_checker.gif\`：棋盘背景、256色量化观看预览。GIF使用130/120ms交替时长，总周期1秒，不宣称原色无损。\n- \`previews/robot_walk_down_contact_v006.png\`：原尺寸完整格联系图，标签位于格外。\n- 文件名含\`scaled_diagnostic\`的文件：全组采用相同固定格缩放及相同补边，保持宽高比、Nearest；明确属于缩小检查图，不是原生像素素材。\n\nJSON记录母图/每帧/预览SHA、RGBA比对、Alpha分布、bbox及最低可见Alpha边界漂移。最低Alpha像素只是脚底代理值；碎片或其他图案也可能影响该值，工具不据此改图。\n\n复现命令：\n\n\`node tools/export_robot_motion_study_v006.cjs --master=<母图绝对路径> --output=<本目录绝对路径> --sharp-module=<Sharp模块目录>\`\n`;
  await fs.writeFile(path.join(args.output, 'README.md'), readme);
  console.log(`TRIAL encoding=${report.encoding_validation_status} frames=8 cell=${frameWidth}x${frameHeight} crops_rgba=true webp_rgba=${webpExact} alpha_bottom_range=${span(bottoms)}`);
  if (!webpExact) process.exitCode = 2;
}

main().catch((error) => { console.error(error.stack || error.message); process.exitCode = 1; });
