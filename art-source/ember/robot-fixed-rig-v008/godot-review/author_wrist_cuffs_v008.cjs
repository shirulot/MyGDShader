/* 明确一次登记双腕实体袖套；这是新增固定结构作者源，不是按结果Alpha补点。
 * 不修改23个原始PNG、不改变骨长/姿态/原部件比例。重复运行不重复增加cap。 */
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const base = path.resolve(__dirname, "..");
const rigFile = path.join(base, "source/rig_down_v008.json");
const changeFile = path.join(base, "source/wrist_cuff_authoring_change_v008.json");
const hash = file => crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const rig = JSON.parse(fs.readFileSync(rigFile, "utf8"));
if (rig.cap_definitions.some(cap => cap.id === "wrist_socket_left")) {
  process.stdout.write(JSON.stringify({status: "ALREADY_AUTHORED", current_rig_sha256: hash(rigFile)}));
  process.exit(0);
}
const oldSHA = hash(rigFile), oldCount = rig.cap_definitions.length;
const sources = Object.fromEntries(rig.parts.map(part => [part.path,
  hash(path.join(base, part.path.split("/source/")[1] ? "source/" + part.path.split("/source/")[1] : part.path))]));
for (const side of ["left", "right"]) rig.cap_definitions.push({
  id: "wrist_socket_" + side, parent_bone: "forearm_" + side, pivot_keypoint: "wrist_" + side,
  rest_pivot: rig.keypoints["wrist_" + side], width_native: 3, height_native: 4,
  local_polygon: [[-1.5,-2],[1.5,-2],[1.5,2],[-1.5,2]],
  medium_color: "#4D6470", edge_color: "#2B3E4B", edge_width_native: 1,
  draw_order: "BELOW_ORIGINAL_FOREARM_ARMOR_AND_GLOVE", status: "CANDIDATE_ONCE_AUTHORED_FIXED_WRIST_CUFF",
  attachment_end: "distal_forearm_to_wrist", section_note: "3px material section; 2px up/2px down fixed sleeve, single-sided shade",
  authoring_policy: "Once defined in source, transformed by the same physical bone affine as attached armor. Never inspect output Alpha to decide pixels, position, or length."
});
fs.writeFileSync(rigFile, JSON.stringify(rig, null, 2) + "\n");
const newSHA = hash(rigFile);
fs.writeFileSync(changeFile, JSON.stringify({status: "CANDIDATE_AUTHORED_STRUCTURAL_CHANGE",
  source_rig_sha256_before: oldSHA, source_rig_sha256_after: newSHA, cap_count_before: oldCount, cap_count_after: rig.cap_definitions.length,
  added_caps: ["wrist_socket_left", "wrist_socket_right"], original_source_png_sha256: sources,
  source_pngs_changed: false, bones_and_poses_changed: false, art_acceptance: "NOT_CLAIMED",
  note: "Two fixed authored wrist cuffs for both sides; no per-frame Alpha gap filling. Candidate root/game speed integration remains outside scope."
}, null, 2) + "\n");
process.stdout.write(JSON.stringify({source_rig_sha256_before: oldSHA, source_rig_sha256_after: newSHA, cap_count: rig.cap_definitions.length}));
