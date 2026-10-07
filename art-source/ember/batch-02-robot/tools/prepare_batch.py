"""准备 C01 第二批的帧序和逐资产提示词；不生成或编辑图片。"""
import json
from pathlib import Path


BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]
DIRECTIONS = ["down", "left", "right", "up"]
PALETTE = ["#101820", "#182631", "#2B3E4B", "#4D6470", "#829BA3", "#BECBC4",
           "#7B4D35", "#B77C4B", "#E2B77A", "#51C5C2", "#E5A44B", "#E65B4A",
           "#566B78", "#203A4B", "#406B78", "#ECE9D8"]
VIEW = {
    "down": "Facing SOUTH toward the bottom of the screen. Its anatomical LEFT wrist tool stays on SCREEN RIGHT.",
    "up": "Facing NORTH away from the viewer. Show the SAME helmet from behind, with simple back armor and a small dark service seam; front visor and chest window are hidden. Its anatomical LEFT wrist tool stays on SCREEN LEFT. No backpack or new equipment.",
    "left": "Facing WEST toward screen left, top-down three-quarter orthographic left profile. Its anatomical LEFT arm is on the NEAR, lower-screen side; keep the brass wrist repair-tool visible on that same arm. Visor seen only at the front-left edge.",
    "right": "Facing EAST toward screen right, top-down three-quarter orthographic right profile. Its anatomical LEFT arm is on the FAR, upper-screen side, partly occluded; keep a small visible brass wrist-tool cue there. The near arm is the plain right arm. This is NOT a mirror of the left-facing sprite. Visor seen only at the front-right edge.",
}
PHASES = [
    "LEFT foot forward contact, RIGHT foot behind; right arm forward, left tool arm behind. Both feet contact the floor.",
    "Passing pose: LEFT foot supports, RIGHT foot lifted to pass forward; arms pass near the torso. Torso rises at most one logical pixel.",
    "RIGHT foot forward contact, LEFT foot behind; left tool arm forward, right arm behind. Both feet contact the floor.",
    "Opposite passing pose: RIGHT foot supports, LEFT foot lifted to pass forward; arms pass near the torso. Torso rises at most one logical pixel. This frame must smoothly loop back to frame 0.",
]
COMMON = """Use case: stylized-concept / C01 animation asset for Ember Energy Station / 余烬采能站.
Edit the attached ORIGINAL PROJECT robot into exactly ONE new animation frame. The reference is the identity lock: keep the same compact gentle repair robot, rounded pale ceramic helmet and armor, recessed deep blue-gray visor/joints, thick separated boots, a small unlit neutral chest status window, and a brass repair-tool coupling on its ANATOMICAL LEFT WRIST. Preserve the same head/body ratio, armor seams, limb count and manufacturing language. No weapon, hand swap, extra accessories or redesigned character.
Camera stays top-down three-quarter ORTHOGRAPHIC about 35 degrees, looking down on the head and shoulders. World light stays gently from upper-left, regardless of turn. No cast/contact shadow, perspective vanishing point, isometric diamond view or full side-on camera.
One constant native pixel grid: intended final canvas 64 columns by 96 rows; body no wider than 40 and no taller than 64 logical pixels, approximately 59 pixels tall like the reference. Subject centered on the foot ground boundary (32,80), generous transparent padding, no clipping. If small native output is unavailable, display a clean exact integer enlargement of that design grid. Do not fill the large canvas with thousands of tiny pixel details.
Broad coherent flat pixel clusters, crisp 1-logical-pixel outline, 3-4 shades per material, sparse detail. Use ONLY this registered palette: """ + " ".join(PALETTE) + """. Base uses neutral ceramic/steel/brass; do not paint cyan, orange or red runtime state colors. No dithering, gradients, soft glow, antialiasing or random texture.
Background must be genuine transparent ALPHA, empty pixels fully transparent. No floor, painted checkerboard, white box, text, labels, contact shadows, decorative frame, UI, rain, smoke, fire, shield, aura or baked energy effect. Show exactly one complete robot in one pose.
"""


def main():
    (BATCH / "prompts").mkdir(parents=True, exist_ok=True)
    (BATCH / "generated").mkdir(exist_ok=True)
    frames, animations, sheet_frames = [], [], []
    for row, direction in enumerate(DIRECTIONS):
        ids = []
        for column in range(5):
            state = "idle" if column == 0 else "walk"
            index = 0 if state == "idle" else column - 1
            asset_id = f"robot_{state}_{direction}" + ("" if state == "idle" else f"_f{index:02d}")
            name = asset_id + "_v001.png"
            original = direction == "down" and state == "idle"
            frames.append({"id": asset_id, "direction": direction, "state": state, "frame_index": index,
                           "file": "res://assets/ember/characters/robot/" + name,
                           "coord": [column, row], "anchor": [32, 80],
                           "sha256": "c65f68455554edb03aea0a7b7b3cea6e1a779fa9d5aa49cba9b4aa5c4f6fbfff" if original else None,
                           "status": "EXISTING_ACCEPTED_FRAME_READ_ONLY" if original else "PLANNED_NOT_PRODUCED"})
            sheet_frames.append({"frame_id": asset_id, "coord": [column, row]})
            if column > 0:
                ids.append(asset_id)
            if not original:
                pose = "Relaxed IDLE, both feet planted, compact arms." if state == "idle" else "WALK cycle frame " + str(index) + ": " + PHASES[index]
                prompt = COMMON + "\nOrientation: " + VIEW[direction] + "\nPose: " + pose + "\nSubtle practical walking only, not running or exaggerated marching. Keep repair tool fixed to its left wrist.\n"
                if state == "walk" and direction != "down":
                    # 新方向行走使用两个参考：原生身份基准及该方向的实际待机母稿。
                    prompt += "\nREFERENCE ROLES: Image 1 is the accepted native DOWN frame: identity, proportions, palette and pixel density. Image 2 is the new direction IDLE candidate: turn/orientation and same-left-wrist tool placement. Keep the new direction while following the native baseline scale. Ignore any soft alpha halo in the candidate.\n"
                prompt_path = BATCH / "prompts" / (asset_id + "_v001.txt")
                if not prompt_path.exists():
                    prompt_path.write_text(prompt, encoding="utf-8")
        animations += [
            {"id": "idle_" + direction, "direction": direction, "state": "idle", "frame_ids": ["robot_idle_" + direction], "fps": 1.0, "loop": True, "preview": "single still frame"},
            {"id": "walk_" + direction, "direction": direction, "state": "walk", "frame_ids": ids, "fps": 8.0, "loop": True},
        ]
    plan = {"schema_version": 1, "date": "2026-10-04", "status": "PLANNED_NOT_PRODUCTION_ACCEPTANCE",
            "scope": "C01 only: preserve existing downward idle and produce the other 19 frames; no optional collect animation.",
            "canvas": [64, 96], "anchor": [32, 80], "bbox_limit": [40, 64], "directions": DIRECTIONS,
            "palette": PALETTE, "frames": frames, "animations": animations,
            "sheet": {"texture": "res://assets/ember/characters/robot/robot_animations_v001.png",
                      "size": [320, 384], "columns": 5, "rows": 4, "frames": sheet_frames}}
    path = BATCH / "planned-catalog-v001.json"
    # 保留已经确定的帧序，避免重跑准备工具覆盖后来追加的审查记录。
    if not path.exists():
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"planned_frames": 20, "new_prompt_files": 19, "catalog": str(path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
