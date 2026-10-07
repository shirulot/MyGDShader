// 只将 Godot 实际捕获的 PNG 帧封装为动画；不绘制或修改水面素材。
// 运行：node encode_animation.cjs <sharp 模块目录>
const fs = require("node:fs");
const path = require("node:path");
const sharp = require(process.argv[2] || "sharp");

async function main() {
  const report = JSON.parse(fs.readFileSync(path.join(__dirname, "capture-report.json"), "utf8"));
  if (report.status !== "GPU_CAPTURED" || report.frames.length !== report.captured_frame_count) {
    throw new Error("必须先成功完成实际 GPU 捕获。");
  }
  const buffers = [];
  let channels;
  const [width, height] = report.image_size;
  for (const frame of report.frames) {
    const frameFile = path.join(__dirname, "frames", path.basename(frame.path));
    const decoded = await sharp(frameFile).raw().toBuffer({ resolveWithObject: true });
    if (decoded.info.width !== width || decoded.info.height !== height) {
      throw new Error("捕获帧的尺寸不一致。");
    }
    channels ??= decoded.info.channels;
    if (decoded.info.channels !== channels) throw new Error("捕获帧的通道数不一致。");
    buffers.push(decoded.data);
  }

  // 使用报告中的真实时间差。机器捕获较慢时，动画也保留真实时长。
  // GIF 的时间单位为 10ms，因此只在封装 GIF 时舍入，不改变画面尺寸。
  const intervals = report.frames.slice(1).map((frame, index) =>
    (frame.captured_seconds - report.frames[index].captured_seconds) * 1000
  );
  const typicalInterval = [...intervals].sort((a, b) => a - b)[Math.floor(intervals.length / 2)];
  const delay = [...intervals, typicalInterval].map(ms => Math.max(10, Math.round(ms / 10) * 10));
  const raw = {
    width,
    height: height * buffers.length,
    channels,
    pageHeight: height,
  };
  const animation = sharp(Buffer.concat(buffers), { raw });
  const gifPath = path.join(__dirname, "water_compare_gpu.gif");
  const webpPath = path.join(__dirname, "water_compare_gpu.webp");

  // GIF 便于聊天内播放；WebP 保留无损帧，供更精确地观察较淡的现有 tile。
  await animation.clone().gif({ loop: 0, delay, effort: 7, dither: 0 }).toFile(gifPath);
  await animation.clone().webp({ lossless: true, loop: 0, delay, effort: 4 }).toFile(webpPath);
  const gifMetadata = await sharp(gifPath, { animated: true }).metadata();
  const webpMetadata = await sharp(webpPath, { animated: true }).metadata();
  if (gifMetadata.pages !== buffers.length || webpMetadata.pages !== buffers.length) {
    throw new Error("导出动画帧数与实际捕获帧不一致。");
  }
  const encoding = {
    source: "actual Godot GPU PNG frames",
    artwork_pixel_processing: "none; only animation container encoding",
    image_size: [width, height],
    frames: buffers.length,
    frame_delays_ms: delay,
    playback_duration_seconds: delay.reduce((sum, value) => sum + value, 0) / 1000,
    capture_span_seconds: report.captured_span_seconds,
    gif: {
      path: path.basename(gifPath),
      bytes: fs.statSync(gifPath).size,
      palette_quantization: true,
      pages: gifMetadata.pages,
      page_height: gifMetadata.pageHeight,
    },
    webp: {
      path: path.basename(webpPath),
      bytes: fs.statSync(webpPath).size,
      lossless: true,
      pages: webpMetadata.pages,
      page_height: webpMetadata.pageHeight,
    },
    loop_note: "A short real-time capture repeated for viewing; not a full shader-period seamless loop.",
  };
  fs.writeFileSync(path.join(__dirname, "animation-report.json"), JSON.stringify(encoding, null, 2) + "\n");
  console.log(JSON.stringify(encoding, null, 2));
}

main().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
