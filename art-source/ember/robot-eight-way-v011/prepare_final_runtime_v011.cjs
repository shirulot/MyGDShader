// 独立TA通过后才制作精简交付包。此脚本只搬运已审像素及调整资源路径，不重绘。
const fs = require('node:fs/promises'), path = require('node:path'), crypto = require('node:crypto');
const root = __dirname;
let frozen;
const candidate = process.argv.includes('--candidate');
const target = path.join(root, candidate ? 'delivery/robot-v011-candidate-v2' : 'delivery/robot-v011');
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const read = async file => JSON.parse(await fs.readFile(file, 'utf8'));
async function put(file, data) { await fs.mkdir(path.dirname(path.join(target, file)), {recursive: true}); await fs.writeFile(path.join(target, file), data); }
async function copy(from, to = from) { await put(to, await fs.readFile(path.join(frozen, from))); }
(async () => {
  // 可先校验候选包的资源路径；候选明确标注待审，不能绕过最终放行门槛。
  const gate = candidate ? {source_revision:'phase-c2-rc02',status:'PENDING_TA',accepted_frames:70,ta_receipt:'qa/ta-receipt-phase-c2-rc01.md'} : await read(path.join(root, 'qa/final-release-gate.json'));
  if (!/^phase-c2-rc\d{2}$/.test(gate.source_revision)) throw Error('Invalid accepted source revision');
  frozen = path.join(root, 'review', gate.source_revision);
  const meta = await read(path.join(frozen, 'full-action-metadata.json'));
  const receipt = await fs.readFile(path.join(root, gate.ta_receipt));
  if (!candidate && (gate.status !== 'READY_FOR_FINAL_RELEASE' || gate.accepted_frames !== 112 || gate.atlas_sha256 !== meta.atlas_sha256 || sha(receipt) !== gate.ta_receipt_sha256)) throw Error('Independent acceptance gate missing or stale');
  if (candidate) { gate.atlas_sha256=meta.atlas_sha256; gate.ta_receipt_sha256=sha(receipt); }
  try { await fs.access(target); throw Error('Final runtime already exists'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  // 完整源包与精简包采用同一张图集、112张PNG，逐项比较获审哈希。
  const atlas = await fs.readFile(path.join(frozen, meta.atlas));
  if (sha(atlas) !== meta.atlas_sha256) throw Error('Frozen atlas changed');
  for (const frame of meta.clips.flatMap(clip => clip.frames)) {
    const bytes = await fs.readFile(path.join(frozen, frame.file));
    if (sha(bytes) !== frame.sha256) throw Error('Frozen frame changed: ' + frame.file);
  }
  const assetFolder = 'assets/ember/robot_v011';
  await put(assetFolder + '/' + meta.atlas, atlas);
  // 保持原始透明边像素；Godot默认边缘修正会改变全RGBA对照中的透明RGB。
  const importer = (await fs.readFile(path.join(frozen, 'godot-full-review/assets/' + meta.atlas + '.import'), 'utf8')).replaceAll('res://assets/' + meta.atlas, 'res://' + assetFolder + '/' + meta.atlas);
  await put(assetFolder + '/' + meta.atlas + '.import', importer);
  for (const frame of meta.clips.flatMap(clip => clip.frames)) await copy(frame.file);
  for (const item of await read(path.join(frozen, 'qa/full_action_animated_exports.json'))) await copy(item.file);
  // 浏览器动图不是Godot纹理源；仅导入assets中的生产atlas，帧PNG仍供原图对照读取。
  for (const folder of ['previews','frames','evidence']) await put(folder+'/.gdignore','');
  const tres = (await fs.readFile(path.join(frozen, 'godot-full-review/robot_eight_way_v011.tres'), 'utf8')).replaceAll('res://assets/' + meta.atlas, 'res://' + assetFolder + '/' + meta.atlas);
  await put(assetFolder + '/robot_eight_way_v011.tres', tres);
  const previewScript = (await fs.readFile(path.join(frozen, 'godot-full-review/preview_full_actions.gd'), 'utf8')).replaceAll('res://robot_eight_way_v011.tres', 'res://' + assetFolder + '/robot_eight_way_v011.tres');
  const scene = (await fs.readFile(path.join(frozen, 'godot-full-review/preview_full_actions.tscn'), 'utf8')).replaceAll('res://preview_full_actions.gd', 'res://preview/preview_full_actions.gd');
  const project = (await fs.readFile(path.join(frozen, 'godot-full-review/project.godot'), 'utf8')).replaceAll('res://preview_full_actions.tscn', 'res://preview/preview_full_actions.tscn');
  await put('preview/preview_full_actions.gd', previewScript);
  await put('preview/preview_full_actions.tscn', scene);
  await put('project.godot', project);
  const originalMetaHash = sha(await fs.readFile(path.join(frozen, 'full-action-metadata.json')));
  meta.release = candidate ? 'robot-v011-candidate' : 'robot-v011-final';
  meta.status = candidate ? 'CANDIDATE_NEW_42_PENDING_TA' : 'ALL_24_CLIPS_112_FRAMES_TA_ACCEPTED';
  meta.atlas = assetFolder + '/' + meta.atlas;
  const receiptFile = candidate ? 'evidence/previous-ta-c2-rc01.md' : 'evidence/ta-c2-final.md';
  meta.art_acceptance = {receipt:receiptFile,receipt_sha256:gate.ta_receipt_sha256,approved_total_frames:candidate?70:112,original_candidate_metadata_sha256:originalMetaHash,candidate_pending:candidate};
  if (!candidate) for (const clip of meta.clips) clip.art_status = 'PASS';
  await put('full-action-metadata.json', JSON.stringify(meta, null, 2) + '\n');
  await put(receiptFile, receipt);
  await put('JOINT-RULES.md', await fs.readFile(path.join(root, 'JOINT-RULES.md')));
  await put('evidence/final-release-gate.json', JSON.stringify(gate, null, 2) + '\n');
  for (const file of ['qa/ta-receipt-phase-b2-rc01.md', 'qa/ta-receipt-phase-c1-rc01.md', 'qa/export_validation_full_actions.json', 'qa/godot_full_actions_v011.json']) await copy(file, 'evidence/' + path.basename(file));
  await put('evidence/cold-source-validation.json', await fs.readFile(path.join(root, 'qa/cold_delivery_validation_' + gate.source_revision.slice(6).replaceAll('-', '_') + '.json')));
  await put('evidence/source-delivery.json', await fs.readFile(path.join(root, 'qa/delivery_' + gate.source_revision + '.json')));
  let html = await fs.readFile(path.join(frozen, 'action-batch-review.html'), 'utf8');
  if (!candidate) html = html.replace('八向行走与南西小样已通过；本次新增的七向待机、采集正在独立审查。', '八向待机、行走和采集已通过逐批独立审查。')
    .replace("clip.art_status==='PASS_RETAINED'?'保留已通过原帧':'新增动作待独立审查'", "clip.art_status==='PASS'?'已通过独立审查':'待审'")
  html = html.replace('godot-full-review/project.godot', 'project.godot');
  await put('preview.html', html);
  await put('verify_import.gd', await fs.readFile(path.join(root, 'qa/verify_final_runtime_import.gd')));
  if (!candidate) await put('verify_entry.gd', await fs.readFile(path.join(root, 'qa/verify_runtime_entry_v011.gd')));
  await put('README.md', `# 机器人 v011 · 八向完整动作\n\n24段、112帧，已通过逐批独立技术美术验收。64×96原生画布，root (32,80)，11色透明像素图。\n\n## 预览\n\n打开本目录project.godot运行。Q/E切方向，1待机、2行走、3采集，空格暂停。网页preview.html须通过本地HTTP服务打开，提供原生/4倍、逐帧、深浅底和慢速。previews/full中另有WebP/GIF。\n\n## 接入现有Godot工程\n\n1. 将assets/ember/robot_v011整个目录复制到目标工程的同名路径。\n2. 为AnimatedSprite2D指定robot_eight_way_v011.tres；将Texture Filter设为Nearest，centered=false，offset=(-32,-80)。节点位置就是脚底原点。\n3. 播放动作名为idle_down、walk_down、collect_down等。八方向为down/down_left/left/up_left/up/up_right/right/down_right。\n4. idle 2帧@2FPS循环，walk 8帧@8FPS循环，collect 4帧@6FPS单次；用animation_finished将采集切回同方向idle并设frame=0。示例代码见preview/preview_full_actions.gd。\n\n所有方向工具均在解剖左腕，禁止用flip_h替代另一侧。主游戏尚未自动接入，本包只提供素材和独立预览。\n\n## 交付依据\n\n完整源包为robot_eight_way_v011_phase_c2_rc01_2026-10-07.zip，哈希见evidence/source-delivery.json；包含母版、固定源片、imagegen输入和提示词、变换、局部掩膜及完整审查证据。本精简包复用完全相同的112帧与atlas，未重新生成。evidence/ta-c2-rc01.md为最终增量回执，其内部相对证据链接属于原TA报告目录。\n\n原源包通过实际Godot224个GPU画面、16条自然两圈、136次切换及8条采集回待机，冷解压复测一致。精简包只调整资源路径、预览文案和通过状态；verify_import.gd检查实际Godot导入、112区域及资源参数。PNG和SpriteFrames是可用素材，不含采集目标判定、发光或战斗逻辑。\n`);
  // 模板中的示例版本名绑定到实际获批的固定源包，避免说明书指向旧候选。
  let finalReadme = await fs.readFile(path.join(target, 'README.md'), 'utf8');
  finalReadme = finalReadme.replaceAll('phase_c2_rc01', gate.source_revision.replaceAll('-', '_')).replaceAll('evidence/ta-c2-rc01.md', receiptFile);
  if (candidate) finalReadme=finalReadme.replace('已通过逐批独立技术美术验收。','候选已制作；已通过70帧，新增42帧等待C2 rc02正式复审。').replace('为最终增量回执','为前序退回回执，当前局部修复仍待新回执');
  if (!candidate) finalReadme += '\n## 正式运行包验证\n\nverify_entry.gd直接运行本包主场景，检查循环、同相位切向、采集期间锁向及单次完成回待机，并读取实际GPU的原生/4倍像素。evidence/runtime-migration.md和runtime-migration-validation.json给出源包到本包的逐文件保持证明；112帧、图集和192个动图均未重绘。实际执行结果见evidence/runtime-entry-validation.json与runtime-editor-import.json。最终ZIP的独立迁移复审回执保存在包外，避免审查后改变已冻结交付。\n';
  await put('README.md', finalReadme);
  console.log(JSON.stringify({prepared: target, clips: 24, frames: 112, atlas_sha256: meta.atlas_sha256}));
})().catch(error => { console.error(error); process.exitCode = 1; });
