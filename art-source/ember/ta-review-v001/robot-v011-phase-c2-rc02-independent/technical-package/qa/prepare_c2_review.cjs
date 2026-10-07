// 记录制作方实际观察及明确的待审范围；技术 PASS 不自动扩张为美术 PASS。
const fs = require('node:fs/promises'), path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = async file => JSON.parse(await fs.readFile(path.join(root, file), 'utf8'));
const write = async (file, value) => fs.writeFile(path.join(root, file), JSON.stringify(value, null, 2) + '\n');
(async () => {
  const meta = await read('full-action-metadata.json');
  const browser = (await fs.readdir(path.join(root, 'qa/browser'))).filter(file => file.startsWith('phase_c2_rc01_')).map(file => 'qa/browser/' + file);
  await write('qa/visual-review-c2-rc01.json', {
    revision: 'phase-c2-rc01', atlas_sha256: meta.atlas_sha256,
    producer_review: 'READY_FOR_INDEPENDENT_REVIEW', independent_art_acceptance: 'PENDING_TA',
    scope: 'Seven remaining directions idle2/collect4, 42 new frames; includes the new S neutral supported stance.',
    viewed_contact_sheets: ['front_back', 'sides', 'diagonals'].flatMap(group => ['light', 'dark'].map(bg => `qa/c2_${group}_${bg}_4x.png`)),
    observations: [
      'New S neutral uses the approved F02 identity pixels and lowers its right lower leg/boot by one raster pixel; five knee-core pixels use a registered local imagegen edit. The original identity and walk remain unchanged.',
      'Every direction uses fixed source armor, tool and boots. Idle upper-body servo motion is one pixel; pelvis and leg transforms stay fixed.',
      'Collect uses one-pixel torso drop in S/N and two pixels in other directions. Feet stay planted; fixed-length legs bend at their registered joints.',
      'F01/F02 share body/leg/far-arm seam pixels wherever their transforms are identical. F03 is exactly the same direction idle F00.',
      'Dark and light contact boards show attached knee/ankle cores and no floating foot or generation halo. Collection crouches remain compact; independent review must judge readability, joint overlap and the S neutral stance.',
      'The E idle edit initially introduced two detached dark additions. The compositor now rejects new pixels that do not touch the original opaque silhouette; no line was drawn to connect the artifact.',
      'Source geometry, asymmetric left-wrist tool and screen upper-left lighting are preserved. No mirroring or per-frame bbox alignment was used.'
    ],
    browser_checks: [
      'Seven new collect directions inspected at held F01 or F02, quarter speed and dark background, with native and 4x views together.',
      'SE collect replayed at normal speed on light background with return enabled; the displayed action returned to idle.',
      'Browser screenshots are discrete observations, not a recording of continuous playback. Natural loops and completion events were exercised by the actual GPU verifier.'
    ],
    browser_evidence: browser, engine_playback_evidence: 'qa/godot_full_actions_v011.json',
    preserved_approved_scope: '64 walk frames, 6 SW action frames and 8 identity masters byte-for-byte',
    unreviewed_scope: 'Independent TA acceptance of 42 new frames and S neutral; main project integration is outside this standalone delivery.'
  });
  const contract = await read('eight_way_action_contract_v011.json');
  contract.current_unfinished = ['Independent TA review of seven remaining idle2/collect4 directions and S neutral stance', 'Final frozen full-action delivery and cold-load verification'];
  contract.integration_scope = 'Independent preview and SpriteFrames delivery; main game integration is separate.';
  contract.collect.direction_projection = {down: '1px torso drop', up: '1px torso drop', other_directions: '2px torso drop'};
  await write('eight_way_action_contract_v011.json', contract);
  const manifest = await read('run-manifest.json');
  manifest.status = 'PHASE_C2_RC01_READY_FOR_TA';
  manifest.phase_c.remaining_directions = {new_clips: 14, new_frames: 42, art_acceptance: 'PENDING_TA', preview: 'action-batch-review.html', independent_engine_project: 'godot-full-review/project.godot'};
  manifest.full_action_delivery = {metadata: 'full-action-metadata.json', atlas_sha256: meta.atlas_sha256, clips: 24, frames: 112, approved_frames: 70, new_frames_pending_art_review: 42, technical_checks: 'PASS', main_project_integrated: false};
  await write('run-manifest.json', manifest);
  console.log(JSON.stringify({visual_review: 'READY_FOR_INDEPENDENT_REVIEW', browser_evidence: browser.length, atlas_sha256: meta.atlas_sha256}));
})().catch(error => { console.error(error); process.exitCode = 1; });
