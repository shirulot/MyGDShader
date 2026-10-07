"""创建本批15项的独立提示词；不修改正式资产、全局清单或历史批次。"""
from pathlib import Path
import json

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]
PALETTE = ["101820", "182631", "2B3E4B", "4D6470", "829BA3", "BECBC4", "7B4D35", "B77C4B", "E2B77A", "51C5C2", "E5A44B", "E65B4A", "566B78", "203A4B", "406B78", "ECE9D8"]
SPECS = [
    ("hp", "U01", "完整性 / 生命", "icons", "A compact ceramic mechanical heart emblem, with a small inset medical plus at its center. Two rounded shoulders, a pointed lower tip. Clearly signifies robot health/integrity. This is an object-like pixel icon, not an emoji."),
    ("energy", "U01", "能量", "icons", "A short industrial cylindrical battery cell, thick dark end caps, a pale ceramic casing, and a single broad unlit vertical power window. Tiny brass top contacts. Clearly signifies stored energy; no lightning glow."),
    ("time", "U01", "时间", "icons", "A mechanical stopwatch: round blue-gray steel case, small brass crown on top, a plain pale dial, two dark clock hands of different lengths. No numbers or lettering. Clearly signifies elapsed time."),
    ("interact", "U01", "交互", "icons", "A compact pale robotic glove with one raised index fingertip pressing a small square steel switch at upper right. Thumb and bent remaining fingers form a clear hand silhouette; dark articulated joints. Clearly signifies interaction with equipment."),
    ("log", "U01", "记录", "icons", "A compact bound maintenance logbook: dark steel-blue cover, pale exposed page edges, brass binding clips, one small neutral label plate. No letters or simulated text lines. Clearly signifies collected records."),
    ("pause", "U01", "暂停", "icons", "Two parallel tall ceramic pause bars with dark blue-gray beveled edges and subtle top-left highlights, mounted on a compact steel plate. Clearly readable classic pause silhouette; no text or ornament."),
    ("lighting", "U02", "照明", "tasks", "An unlit industrial light bulb inside a minimal protective steel cage: rounded pale glass dome, two visible cage struts, screw/socket base. Clearly signifies repairing lighting; no rays, halo, glow or active state color."),
    ("drainage", "U02", "排水", "tasks", "A small steel drain basin with two calm dark water marks above a central downward evacuation arrow, and a visible drain outlet below. Strong downward emptying silhouette; clearly drainage, not a faucet."),
    ("water_supply", "U02", "供水", "tasks", "A compact brass-and-steel faucet with a horizontal inlet pipe, a top cross handle, bent downward spout, and one large pale water droplet below the spout. Clearly signifies water supply, distinct from drainage."),
    ("ventilation", "U02", "排热 / 通风", "tasks", "A compact square industrial ventilation fan grille, four clearly separated broad curved blades around a central hub, four corner fasteners, dark recessed opening. Clearly ventilation; no snowflake and no steam."),
    ("cooling", "U02", "冷却", "tasks", "A compact industrial radiator block with three vertical steel cooling fins and a prominent small pale six-branch snowflake badge in front. Clearly cooling, visually distinct from a fan; no frost cloud or colored glow."),
    ("communication", "U02", "通信", "tasks", "A compact industrial antenna mast on a square steel base with a pale tip and two pairs of neutral signal arcs on either side. The arcs are crisp solid pixel shapes, not light effects. Clearly communication."),
    ("teleport", "U03", "传送", "tasks", "A compact ceramic-and-steel portal arch mounted on a shallow elliptical industrial pad, with a small upward transfer arrow in the clear central opening. Clearly teleportation; no robot, glow, magical particles or active effect."),
    ("protection", "U03", "保护", "tasks", "A compact pale ceramic protective shield emblem with steel-blue rim, angled lower corners and a pointed lower tip; a simple closed neutral ring in its center symbolizes stable protection. Clearly protection, distinct from the heart health icon; no magical glow."),
    ("panel_9slice", "U04", "九宫格面板", "panels", "One square reusable industrial UI panel skin: blue-gray steel frame with 8-pixel logical slice margins, tiny chamfered corners and small corner fasteners. Continuous plain beveled edges and a completely calm uniform dark inset center. Design for 96x96 native pixels; four 8x8 corners stay intact, middle stretches cleanly. No content, buttons, icons, text, diagram or slice guides."),
]


def main():
    for directory in ["prompts", "generated", "finished", "review", "annotations"]:
        (BATCH / directory).mkdir(parents=True, exist_ok=True)
    references = ["assets/ember/characters/robot/robot_idle_down_v001.png", "assets/ember/buildings/station/station_base_v001.png"]
    common = "\n".join([
        "Use case: stylized-concept",
        "Asset type: individual production-material reference for Ember Repair Station pixel-game UI",
        "Input images: reference 1 and 2 are style/material references only; create the requested new UI asset rather than copying their full silhouettes.",
        "Style/medium: very clear native-pixel-designed raster icon, hand-finished blocks, a consistent one-logical-pixel dark outline and only three or four material shades.",
        "Materials: blue-gray painted steel, pale ceramic armor, restrained small brass fittings, same manufacturer vocabulary as the supplied repair robot/station.",
        "Lighting: gentle upper-left highlights, no cast shadow, no glow. Neutral base state; do not encode danger, warning or running status with saturated colors.",
        "Color palette: " + ", ".join("#" + color for color in PALETTE) + "; emphasize neutral steel/ceramic colors.",
        "Composition: exactly one centered asset on actual transparent alpha, generous clear empty padding; no scene, no grid, no contact sheet.",
        "Text: none. Avoid: letters, numbers, words, watermarks, emojis, photoreal texture, gradients, antialiasing, noisy dithering, cropped silhouettes.",
    ])
    assets = []
    for asset_id, manifest_id, name, folder, description in SPECS:
        size = [96, 96] if manifest_id == "U04" else [32, 32]
        prompt = common + "\nPrimary request: " + description
        if manifest_id != "U04":
            prompt += "\nLogical target: 32x32 native canvas, the actual subject approximately 24x24 logical pixels with 4 pixels of transparent margin on every side; center (16,16). Render enlarged crisp blocks if the tool needs a large canvas, keeping the 24-pixel silhouette legible. This is a material/shape master; native finishing follows separately."
        else:
            prompt += "\nLogical target: 96x96 native canvas, symmetric 8-pixel slice borders. No perspective: the UI skin is strictly front-facing. Keep edge strips continuous, center quiet and corners unobstructed."
        (BATCH / "prompts" / f"{asset_id}_v001.txt").write_text(prompt + "\n", encoding="utf-8")
        assets.append({"id": asset_id, "manifest_id": manifest_id, "name": name, "folder": folder,
                       "canvas": size, "anchor": [16, 16] if manifest_id != "U04" else [48, 48],
                       "production_file": f"res://assets/ember/ui/{folder}/{asset_id}_v001.png",
                       "slice_margins": [8, 8, 8, 8] if manifest_id == "U04" else None,
                       "references": references, "prompt": f"art-source/ember/batch-04-ui/prompts/{asset_id}_v001.txt"})
    (BATCH / "planned-catalog-v001.json").write_text(json.dumps({"status": "WORK_PLAN_NOT_PRODUCTION", "assets": assets, "palette": PALETTE}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"assets": len(assets), "batch": str(BATCH)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
