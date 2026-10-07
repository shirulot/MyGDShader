"""三列共用128画布/8倍Nearest。中列工作态另记哈希，不伪称固定预检输入。"""
from pathlib import Path
from PIL import Image
import hashlib
import json
from io import BytesIO

ROOT = Path("E:/dev/shader/godot-shader/godot-shader-simple")
SOURCE = ROOT / "art-source/ember/enemy-eight-directions-v013"
OUT = Path(__file__).resolve().parent
BOUND = OUT / "bound"
def sha(raw): return hashlib.sha256(raw).hexdigest()
records = []
for unit in ["enemy_patrol", "enemy_scout_drone"]:
    working = SOURCE / "qa" / (unit + "_generated_front.png")
    paths = [BOUND / "baseline-source-approved-down" / (unit + ".png"),
             working,
             BOUND / "output" / unit / "neutral_down_right.png"]
    raws = [p.read_bytes() for p in paths]
    sheet = Image.new("RGBA", (384, 128), (210, 214, 220, 255))
    cols = []
    for index, (path, raw) in enumerate(zip(paths, raws)):
        img = Image.open(BytesIO(raw)).convert("RGBA")
        assert img.size == (128, 128)
        # 保留每张128×128中的原位置，不裁bbox、不移底、不额外校准比例。
        canvas = Image.alpha_composite(Image.new("RGBA", (128,128), (210,214,220,255)), img)
        sheet.paste(canvas, (index*128, 0))
        cols.append({"index": index, "meaning": ["fixed approved_down", "WORKING generated_front diagnostic only", "fixed neutral_down_right"][index],
            "source_path": str(path), "sha256": sha(raw), "canvas": [128,128], "translation_in_cell": [0,0],
            "belongs_to_bound_catalog_or_baseline_snapshot": index != 1})
    dest = OUT / "diagnostic-crops" / (unit + "_approved-generated-front-down-right_light_8x.png")
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.resize((3072,1024), Image.Resampling.NEAREST).save(dest)
    records.append({"unit": unit, "path": str(dest), "sha256": sha(dest.read_bytes()),
        "columns_left_to_right": cols, "scale": 8, "background_rgb": [210,214,220],
        "canvas_registration_preserved": True, "working_input_unchanged_during_capture": working.read_bytes() == raws[1]})
(OUT / "calibration-working-diagnostics.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps([{"path": r["path"], "sha256": r["sha256"], "working_front_sha256": r["columns_left_to_right"][1]["sha256"]} for r in records], ensure_ascii=False, indent=2))
