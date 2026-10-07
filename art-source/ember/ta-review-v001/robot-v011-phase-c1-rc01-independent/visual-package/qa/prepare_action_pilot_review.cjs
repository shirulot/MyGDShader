// 登记八向行走已通过的固定字节，并生成动作小样的来源记录和方格审计适配图。
// 这里只做记录、哈希和透明边距，不重绘或覆盖任何已通过的图像。
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const sharp = require('C:/Users/shiru/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const root = path.resolve(__dirname, '..');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = file => fs.readFile(path.join(root, file));
const json = async file => JSON.parse(await read(file));
const write = (file, value) => fs.writeFile(path.join(root, file), JSON.stringify(value, null, 2) + '\n');

async function main() {
  const receipt = 'qa/ta-receipt-phase-b2-rc01.md';
  const receiptBytes = await read(receipt);
  if (!receiptBytes.toString('utf8').includes('PASS，W/E两条新walk共16帧')) throw Error('Unexpected B2 receipt');
  const accepted = await json('source/reference-phase-b2-rc01-metadata.json');
  const walks = accepted.clips.filter(clip => clip.action === 'walk');
  const acceptedImages = accepted.clips.flatMap(clip => clip.frames);
  if (walks.length !== 8 || walks.some(clip => clip.frames.length !== 8)) throw Error('Incomplete accepted walks');
  for (const frame of acceptedImages) {
    if (sha(await read(frame.file)) !== frame.sha256) throw Error('Accepted image changed: ' + frame.file);
  }
  await write('source/walk-acceptance-v011.json', {
    status: 'EIGHT_WALK_DIRECTIONS_ACCEPTED',
    receipts: ['qa/ta-receipt-phase-a-rc02.md', 'qa/ta-receipt-phase-b1-rc02.md', receipt],
    current_receipt_sha256: sha(receiptBytes), directions: walks.map(clip => clip.direction), clips: walks,
    accepted_frame_count: 64, excludes: ['final idle', 'collect', 'main game integration']
  });
  const manifest = await json('run-manifest.json');
  const review = {revision: 'phase-b2-rc01', decision: 'PASS', scope: 'W/E 16 walk frames; all eight walks now accepted, 64 frames', review: receipt,
    review_sha256: sha(receiptBytes), zip_sha256: '538d7bb49eb2e4480046eee50306a232b7a3f130219564e1618dbfbfff19164c'};
  manifest.review_history = manifest.review_history.filter(item => item.revision !== review.revision).concat(review);
  manifest.phases.find(p => p.id === 'B').status = 'EIGHT_WALK_DIRECTIONS_PASS';
  manifest.phase_b.motion_art_acceptance = 'PASS_FIXED_B2_RC01';
  manifest.status = 'PHASE_C1_RC01_IN_REVIEW_PREPARATION';
  manifest.new_directions_art_acceptance = 'WALK_PASS_IDLE_COLLECT_PENDING';
  manifest.current_review_metadata = 'action-pilot-metadata.json';
  manifest.current_candidate_revision = 'phase-c1-rc01';
  manifest.current_revision_fix = {revision: 'phase-c1-rc01', scope: 'SW idle 2 + collect 4 new frames', previous_batch: 'phase-b2-rc01',
    unchanged_files: acceptedImages.length, source_rig: 'build_action_pilot_v011.cjs', compositor: 'composite_action_pilot_v011.cjs', art_acceptance: 'PENDING_TA'};
  const generations = [
    {scope: 'C1 SW idle waist seam', source: 'source/idle_down_left_joint_edit_raw_v011.png', prompt: 'prompts/idle_down_left_joint_edit_v011.txt',
      actual_input: 'source/action_edit_inputs_c1_rc01/idle_down_left.png', usage: 'LOCAL_WAIST_PATCH_FRAME_1_ONLY',
      original_output: 'exec-d964124c-ae79-4551-8e80-abc89d07033a.png'},
    {scope: 'C1 SW collect rejected pose drift', source: 'source/collect_down_left_joint_edit_rejected_v011.png', prompt: 'prompts/collect_down_left_joint_edit_v011.txt',
      actual_input: 'source/action_edit_inputs_c1_rc01/collect_down_left.png', status: 'REJECTED_NOT_USED',
      reason: 'Changed crouch and arm pose; halo background; never composited into final frames', original_output: 'exec-558f09a8-cbbb-4bc6-9f51-06bf0ca664dd.png'},
    {scope: 'C1 SW collect joint seams', source: 'source/collect_down_left_joint_edit_raw_v011.png', prompt: 'prompts/collect_down_left_joint_edit_v011_retry.txt',
      actual_input: 'source/action_edit_inputs_c1_rc01/collect_down_left.png', usage: 'LOCAL_JOINT_PATCH_ON_FIXED_RIG',
      original_output: 'exec-9c1f4d50-27d7-4ea2-b4ed-67420a69a88b.png',
      note: 'Raw generation is an intermediate with background artifacts; protected masks, binary alpha and dark-core restriction exclude those artifacts from final sprites.'}
  ];
  for (const entry of generations) {
    entry.method = 'imagegen_edit'; entry.cell = [64, 96]; entry.direction = 'down_left';
    entry.sha256 = sha(await read(entry.source)); entry.input_sha256 = sha(await read(entry.actual_input));
    entry.prompt_sha256 = sha(await read(entry.prompt));
    manifest.generation = manifest.generation.filter(item => item.scope !== entry.scope).concat(entry);
  }
  manifest.phase_c = {pilot: 'down_left', new_frames: 6, art_acceptance: 'PENDING_TA', approved_walk_frames_preserved: 64,
    body_pelvis_overlap_source_rows: [54, 55], idle0_is_original_identity: true, collect3_is_idle0: true,
    preview: 'action-review.html', independent_engine_project: 'godot-action-review/project.godot'};
  await write('run-manifest.json', manifest);
  const contract = await json('eight_way_action_contract_v011.json');
  contract.current_unfinished = ['SW idle2/collect4 independent art review', 'seven remaining idle2/collect4 directions, including a neutral supported S base', 'final all-direction preview and delivery', 'main project integration'];
  await write('eight_way_action_contract_v011.json', contract);
  const meta = await json('action-pilot-metadata.json');
  for (const clip of meta.clips.filter(clip => ['idle', 'collect'].includes(clip.action))) {
    const width = 96 * clip.frames.length, raw = Buffer.alloc(width * 96 * 4);
    for (const [index, frame] of clip.frames.entries()) {
      const pixels = await sharp(await read(frame.file)).ensureAlpha().raw().toBuffer();
      for (let y = 0; y < 96; y++) pixels.copy(raw, (y * width + index * 96 + 16) * 4, y * 64 * 4, (y + 1) * 64 * 4);
    }
    await sharp(raw, {raw: {width, height: 96, channels: 4}}).png().toFile(path.join(root, `qa/${clip.action}_motion_diagnostic_padded96.png`));
  }
  await write('qa/action_pilot_provenance.json', {status: 'PASS', atlas_sha256: meta.atlas_sha256,
    unchanged_accepted_images: acceptedImages.length, unchanged_accepted_walk_frames: 64, generations,
    method: 'Original imagegen mother parts, fixed transforms, local imagegen joint patches',
    processing: 'Common sheet quantization only; no per-frame fitting, scaling or recentering',
    art_acceptance: 'PENDING_TA'});
  console.log(JSON.stringify({accepted_walks: 64, unchanged_images: acceptedImages.length, new_frames: 6, generation_records: 3}));
}
main().catch(error => {console.error(error); process.exitCode = 1;});
