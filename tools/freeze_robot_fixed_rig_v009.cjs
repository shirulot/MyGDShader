// 登记已审阅的小样与保护性校验。只写 v009 的报告，不替换正式角色资源。
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = process.cwd();
const base = path.join(root, 'art-source/ember/robot-fixed-rig-v009');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const write = (relative, value) => fs.writeFileSync(path.join(base, relative), JSON.stringify(value, null, 2) + '\n');
const baseline = read(path.join(root, 'art-source/ember/robot-fixed-rig-v007/source/production_baseline_sha256_v007.json'));
const protectedFiles = baseline.files.map(entry => ({file: entry.file, expected: entry.sha256, actual: hash(entry.file)}));
const oldManifest = read(path.join(root, 'art-source/ember/robot-fixed-rig-v008/run-manifest.json'));
const oldFrames = oldManifest.frozen_frames.map(entry => ({file: entry.file, expected: entry.sha256,
  actual: hash(path.join(root, entry.file.replace(/^res:\/\//, '')))}));
const oldZip = 'art-source/ember/deliveries/robot_fixed_rig_v008_walk_down_candidate_2026-10-06.zip';
const oldZipCheck = {file: oldZip, expected: 'ac74a58d6ac1751556751046571d5d983a9dcc4f9f85a146b4494706b055ff1b', actual: hash(path.join(root, oldZip))};
const allProtected = [...protectedFiles, ...oldFrames, oldZipCheck].every(entry => entry.expected === entry.actual);
write('qa/production_protection_v009.json', {status: allProtected ? 'PASS' : 'FAIL', formal_files: protectedFiles,
  previous_frozen_frames: oldFrames, previous_zip: oldZipCheck});
if (!allProtected) throw new Error('Protected production or frozen v008 content differs from baseline.');
const render = read(path.join(base, 'fixed_rig_render_v009.json'));
const playback = read(path.join(base, 'fixed_rig_playback_v009.json'));
const encoding = read(path.join(base, 'qa/export_validation_v009.json'));
const comparison = read(path.join(base, 'qa/foot_motion_comparison_v009.json'));
if (render.technical_checks !== 'PASS' || playback.technical_checks !== 'PASS' || encoding.status !== 'ENCODING_PASS') throw new Error('Required technical evidence did not pass.');
const evidence = ['source/robot_idle_down_canonical_original.png','source/rig_down_v009.json','source/foot_motion_v009.json',
  'robot_walk_down_atlas_v009.png','godot-review/render_fixed_rig_v009.gd',
  'godot-review/assets/robot_walk_down_atlas_v009.png.import','fixed_rig_render_v009.json','fixed_rig_playback_v009.json',
  'qa/export_validation_v009.json','qa/foot_motion_comparison_v009.json','qa/producer_visual_review_v009.md','qa/production_protection_v009.json'];
const manifest = {
  revision: 'robot_fixed_rig_v009', stage: 'FROZEN_CANDIDATE_PENDING_TA',
  scope: {direction: 'down', action: 'walk', frames: 8, fps: 8, canvas: [64,96], root_anchor: [32,80], projection: 'screen=(X,Y+0.65Z)', loop: true},
  change: 'Independent rigid foot pivot/pitch and restrained lift/body bob; fixed source parts and camera',
  fixed_parts_count: comparison.source_parts.length, source_parts_unchanged_from_v008: comparison.source_parts_unchanged,
  canonical_bind_unchanged_from_v008: comparison.canonical_bind_unchanged,
  frozen_frames: render.frames.map(f => ({frame:f.frame_index, phase:f.phase, file:f.file, sha256:f.sha256})),
  technical_render: render.technical_checks, technical_playback: playback.technical_checks,
  natural_playback_loops: playback.playback.actual_loops, encoding: encoding.status,
  producer_visual_review: 'REVIEWED_LOCAL_FOOT_REVISION_CANDIDATE', ta_art_review: 'PENDING', production_accepted: false,
  production_assets_modified: false, preserved_v008_zip: oldZipCheck,
  minimum_shin_projection_before: comparison.minimum_projected_ratio_before,
  minimum_shin_projection_after: comparison.minimum_projected_ratio_after,
  limitations: comparison.known_limits,
  evidence: evidence.map(file => ({file, sha256:hash(path.join(base, file))})),
  delivery_zip: 'art-source/ember/deliveries/robot_fixed_rig_v009_foot_revision_candidate_2026-10-06.zip',
  cold_unpack_evidence: 'External sidecar in deliveries binds the ZIP SHA; .import is mandatory package content'
};
write('run-manifest.json', manifest);
console.log(JSON.stringify({status: manifest.stage, formal_files_protected: protectedFiles.length, previous_frames_protected: oldFrames.length, evidence: manifest.evidence}));
