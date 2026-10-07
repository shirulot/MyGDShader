// 只读比较固定源与投影，不把骨长/连通检查当作美术结论。
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const current = path.resolve(__dirname, '..');
const previous = path.resolve(current, '../robot-fixed-rig-v008');
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const frames = [];
for (let index = 0; index < 8; index++) {
  const stem = String(index).padStart(2, '0');
  const oldFile = path.join(previous, `poses/walk_down_f${stem}_v008.json`);
  const newFile = path.join(current, `poses/walk_down_f${stem}_v009.json`);
  const oldPose = read(oldFile), newPose = read(newFile);
  const legs = {};
  for (const side of ['left', 'right']) {
    const oldShin = oldPose.bone_measures.find(b => b.bone === `shin_${side}`);
    const newShin = newPose.bone_measures.find(b => b.bone === `shin_${side}`);
    legs[side] = {
      viewer_side: side === 'left' ? 'right' : 'left',
      rest_length: newShin.rest_length,
      previous_projected_length: oldShin.projected_length,
      current_projected_length: newShin.projected_length,
      previous_projected_ratio: oldShin.projected_length / oldShin.rest_length,
      current_projected_ratio: newShin.projected_length / newShin.rest_length,
      bone_length_3d_error: newShin.length_error,
      foot: newPose.contacts[side]
    };
  }
  frames.push({ index, previous_pose_sha256: hash(oldFile), current_pose_sha256: hash(newFile),
    body_lower_before: oldPose.body_lower_from_original, body_lower_after: newPose.body_lower_from_original,
    legs, stable_parts_unknown: Object.fromEntries(Object.entries(newPose.stable_parts).map(([id, value]) => [id, value.unknown_rgba_samples])) });
}
const sourceParts = fs.readdirSync(path.join(current, 'source/parts')).filter(name => name.endsWith('.png')).map(name => ({
  file: name, current_sha256: hash(path.join(current, 'source/parts', name)),
  previous_sha256: hash(path.join(previous, 'source/parts', name))
}));
const report = { status: 'MEASURED_NOT_ART_ACCEPTANCE',
  scope: '8 down-walk frames; viewer left/right differs from robot anatomical left/right',
  source_parts_unchanged: sourceParts.every(p => p.current_sha256 === p.previous_sha256),
  source_parts: sourceParts,
  original_mother_sha256: hash(path.join(current, 'source/robot_idle_down_canonical_original.png')),
  canonical_bind_unchanged: hash(path.join(current, 'source/robot_idle_down_fixed_rig_canonical_v009.png')) === hash(path.join(previous, 'source/robot_idle_down_fixed_rig_canonical_v008.png')),
  frames,
  minimum_projected_ratio_before: Math.min(...frames.flatMap(f => Object.values(f.legs).map(l => l.previous_projected_ratio))),
  minimum_projected_ratio_after: Math.min(...frames.flatMap(f => Object.values(f.legs).map(l => l.current_projected_ratio))),
  interpretation: 'Foot controllers, restrained body bob and lift reduce shin foreshortening. No hard minimum-ratio clamp. Visual acceptance requires native and normal-speed review.',
  known_limits: ['Small-angle planar 2.5D boot projection, not a full volumetric shoe', 'Foot ground markers are rig-space evidence; gameplay contact/root-speed integration not covered']
};
fs.writeFileSync(path.join(__dirname, 'foot_motion_comparison_v009.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({source_parts_unchanged: report.source_parts_unchanged, canonical_bind_unchanged: report.canonical_bind_unchanged,
  minimum_before: report.minimum_projected_ratio_before, minimum_after: report.minimum_projected_ratio_after,
  unknown: frames.map(f => ({frame: f.index, ...f.stable_parts_unknown}))}));
