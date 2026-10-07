// 固定完整动作候选包。任何修订必须换 rc 编号，不能覆盖已送审文件。
const fs = require('node:fs/promises'), path = require('node:path'), crypto = require('node:crypto');
const root = __dirname, revision = process.argv[2] || 'phase-c2-rc01';
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const read = async file => JSON.parse(await fs.readFile(path.join(root, file), 'utf8'));
async function filesIn(folder) {
  const out = [];
  for (const entry of await fs.readdir(folder, {withFileTypes: true})) {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) out.push(...await filesIn(file)); else out.push(file);
  }
  return out;
}
(async () => {
  if (!/^phase-c2-rc\d{2}$/.test(revision)) throw Error('Invalid full-action revision');
  const target = path.join(root, 'review', revision);
  try { await fs.access(target); throw Error('Frozen revision already exists'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  const meta = await read('full-action-metadata.json');
  if (meta.revision !== 'v011-' + revision || meta.clips.length !== 24 || meta.clips.flatMap(c => c.frames).length !== 112) throw Error('Incomplete metadata');
  if (sha(await fs.readFile(path.join(root, meta.atlas))) !== meta.atlas_sha256) throw Error('Atlas mismatch');
  for (const file of ['qa/export_validation_full_actions.json', 'qa/godot_full_actions_v011.json']) {
    const report = await read(file);
    if (report.technical_checks !== 'PASS' || report.atlas_sha256 !== meta.atlas_sha256 || report.errors.length) throw Error('Stale or failed report: ' + file);
  }
  const visual = await read('qa/visual-review-' + revision.slice(6) + '.json');
  if (visual.atlas_sha256 !== meta.atlas_sha256 || visual.producer_review !== 'READY_FOR_INDEPENDENT_REVIEW') throw Error('Visual review missing');
  // 送审前重新核对已通过帧，而不是依赖旧报告中的 PASS 文本。
  const accepted = [...(await read('source/walk-acceptance-v011.json')).clips, ...(await read('source/action-acceptance-v011.json')).clips].flatMap(c => c.frames);
  const mothers = (await read('source/reference-phase-b2-rc01-metadata.json')).clips.filter(c => c.action === 'pose').flatMap(c => c.frames);
  if (accepted.length !== 70 || mothers.length !== 8) throw Error('Wrong accepted baseline');
  for (const frame of [...accepted, ...mothers]) if (sha(await fs.readFile(path.join(root, frame.file))) !== frame.sha256) throw Error('Accepted pixels changed: ' + frame.file);
  const manifest = await read('run-manifest.json');
  const newSources = manifest.generation.filter(g => g.scope?.startsWith('C2 '));
  if (newSources.length !== 14) throw Error('Missing C2 generation sources');
  for (const entry of newSources) {
    for (const [file, expected] of [[entry.source, entry.sha256], [entry.actual_input, entry.input_sha256], [entry.prompt, entry.prompt_sha256]]) {
      if (sha(await fs.readFile(path.join(root, file))) !== expected) throw Error('Generation provenance changed: ' + file);
    }
  }
  manifest.status = 'PHASE_C2_RC01_READY_FOR_TA'; manifest.frozen_review = 'review/' + revision;
  await fs.writeFile(path.join(root, 'run-manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  const selected = ['README-full-actions.md', 'WORKLOG.md', 'eight_way_action_contract_v011.json', 'run-manifest.json', 'full-action-metadata.json', meta.atlas, 'action-batch-review.html', 'source', 'prompts', 'frames', 'previews', 'qa', 'gpu-full-playback', 'godot-full-review'];
  // 带上固定源生成/合成的本地依赖；旧冻结包和引擎缓存不进入新包。
  selected.push(...(await fs.readdir(root)).filter(file => file.endsWith('.cjs')));
  const excluded = new Set(['.godot', 'cold-action-validation', 'cold-full-validation', 'cold-godot']);
  await fs.mkdir(target, {recursive: true});
  for (const item of selected) await fs.cp(path.join(root, item), path.join(target, item === 'README-full-actions.md' ? 'README.md' : item), {
    recursive: true, filter: source => !source.split(path.sep).some(part => excluded.has(part)) && !source.endsWith('.log')
  });
  await fs.writeFile(path.join(target, 'FROZEN.md'), `# ${revision}\n\n固定候选：完整24段112帧，其中42新帧及S中性姿态待TA。入口action-batch-review.html及godot-full-review/project.godot。原包只读，在新副本中编辑；引擎验证输出使用包外目录。\n`);
  const files = [];
  for (const file of (await filesIn(target)).sort()) {
    const bytes = await fs.readFile(file);
    files.push({file: path.relative(target, file).split(path.sep).join('/'), bytes: bytes.length, sha256: sha(bytes)});
  }
  await fs.writeFile(path.join(target, 'sha256-manifest.json'), JSON.stringify({revision, status: 'CANDIDATE_PENDING_TA', files}, null, 2) + '\n');
  console.log(JSON.stringify({frozen: target, payload_files: files.length, manifest_sha256: sha(await fs.readFile(path.join(target, 'sha256-manifest.json')))}));
})().catch(error => { console.error(error); process.exitCode = 1; });
