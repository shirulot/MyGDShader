"""Recheck recovered visual evidence without editing the fixed delivery."""
from pathlib import Path
import hashlib
import json
from PIL import Image

review = Path(__file__).resolve().parent
package = review / "visual-package"
binding = json.loads((review / "visual-binding.json").read_text(encoding="utf-8"))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
checked = []
for name, expected in binding["diagnostic_sha256"].items():
    assert sha(review / name) == expected, name
    checked.append(name)
for name, record in binding["frames"].items():
    assert sha(package / name) == record["sha256"], name

# Coordinates remain on the original 64 x 96 canvas, not the diagnostic crop.
elbow = {}
for frame in (1, 2):
    filename = f"robot_collect_down_right_f{frame:02d}_v011.png"
    raw_path = package / "source/action-rig-batch/collect/down_right" / filename
    final_path = package / "frames/collect/down_right" / filename
    raw = Image.open(raw_path).convert("RGBA")
    final = Image.open(final_path).convert("RGBA")
    elbow[f"F{frame:02d}"] = {
        "raw_sha256": sha(raw_path),
        "final_sha256": sha(final_path),
        "pixels": [{"xy": [14, y], "raw": list(raw.getpixel((14, y))),
                    "final": list(final.getpixel((14, y)))} for y in range(51, 57)],
    }
    assert final.getpixel((14, 51)) == (16, 24, 32, 255)
    for y in (52, 53, 54):
        assert final.getpixel((14, y)) == (236, 233, 216, 255)
        assert final.getpixel((14, y)) != raw.getpixel((14, y))

report = {"diagnostics_rechecked": len(checked), "bound_frames_rechecked": len(binding["frames"]),
          "evidence_unchanged": True, "se_elbow": elbow,
          "interpretation": "Opaque bright pixels replace an existing dark outer contour; not an alpha-disconnected limb."}
(review / "visual-recheck.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
