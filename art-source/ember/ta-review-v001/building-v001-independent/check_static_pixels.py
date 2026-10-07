"""Read existing GPU evidence; write numeric diagnostics only, never edit art."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
PREVIEWS = ROOT / "assets/ember/building_assets_v001/previews"
INDEX = json.loads((PREVIEWS / "actions/action_index_v001.json").read_text(encoding="utf-8"))

# Fixed screenshot coordinates, selected from the actual 2x GPU captures.
# Roof devices that legitimately move are outside these static sample regions.
REGIONS = {
    "tower_roof_and_upper_facade": [80, 196, 370, 660],
    "workshop_roof_left": [460, 365, 750, 640],
    "warehouse_roof": [976, 300, 1522, 650],
    "tower_left_door_frame": [168, 696, 184, 798],
    "workshop_left_door_frame": [616, 696, 632, 798],
    "warehouse_right_cargo_rail": [1400, 696, 1422, 778],
}

def rgba(name):
    return np.asarray(Image.open(PREVIEWS / name).convert("RGBA"))

baseline = rgba(INDEX["frames"][0]["filename"])
checks = []
# First six captures share building visibility and actor placement, and cover
# all four doors opening, then cargo closing. This is deliberately scoped.
for frame in INDEX["frames"][1:6]:
    current = rgba(frame["filename"])
    for name, (x0, y0, x1, y1) in REGIONS.items():
        diff = np.any(baseline[y0:y1, x0:x1] != current[y0:y1, x0:x1], axis=2)
        checks.append({"frame": frame["filename"], "region": name,
                       "rect_xyxy": REGIONS[name], "changed_pixels": int(diff.sum())})

# A frozen power-loss state should remain visually identical below the label.
frozen_a = rgba("actions/11_power_loss_half.png")
frozen_b = rgba("actions/12_power_loss_still.png")
freeze_changes = int(np.any(frozen_a[100:] != frozen_b[100:], axis=2).sum())

hashes = []
for frame in INDEX["frames"]:
    digest = hashlib.sha256((PREVIEWS / frame["filename"]).read_bytes()).hexdigest()
    hashes.append({"frame": frame["filename"], "sha256": digest, "match": digest == frame["sha256"]})

report = {
    "scope": "18 captured-frame hashes; 30 static-region comparisons over first 6 frames; blackout pair below header",
    "static_regions": checks,
    "static_region_failures": sum(c["changed_pixels"] != 0 for c in checks),
    "blackout_changed_pixels_below_y100": freeze_changes,
    "hash_checks": hashes,
    "hash_failures": sum(not h["match"] for h in hashes),
    "limitation": "Numeric samples support direct visual review; not a normal-speed live animation PASS.",
}
out = Path(__file__).with_name("static-pixel-checks.json")
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: report[k] for k in ("scope", "static_region_failures", "blackout_changed_pixels_below_y100", "hash_failures")}, ensure_ascii=False))
