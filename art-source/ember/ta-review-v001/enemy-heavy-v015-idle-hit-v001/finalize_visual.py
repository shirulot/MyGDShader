"""Record observed chart coverage and verify visual recovery endpoints only."""
from pathlib import Path
import hashlib
import json
from PIL import Image

base = Path(__file__).resolve().parent
package = base / "package"
binding_path = base / "visual-binding.json"
binding = json.loads(binding_path.read_text(encoding="utf-8"))
directions = ["down_left", "left", "up_left", "up", "up_right", "right", "down_right"]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
endpoints = {}
for direction in directions:
    output = package / "output/enemy_tracked_heavy"
    hit = [output / ("hit_" + direction) / f"f{index:02}.png" for index in range(4)]
    idle = [output / ("idle_" + direction) / f"f{index:02}.png" for index in range(4)]
    endpoints[direction] = {
        "hit_f03_equals_f00_png_bytes": hit[0].read_bytes() == hit[3].read_bytes(),
        "idle_f02_equals_f00_png_bytes": idle[0].read_bytes() == idle[2].read_bytes(),
        "idle_f00_equals_hit_f00_png_bytes": idle[0].read_bytes() == hit[0].read_bytes(),
    }
assert all(all(checks.values()) for checks in endpoints.values())
binding["visual_endpoint_checks"] = endpoints
binding["observed_visual_scope"] = {
    "new_directions": directions,
    "new_clips": 14,
    "new_frames": 56,
    "viewed": [
        "56 frames on original 128x128 canvases, both light and dark 1x diagnostic montages",
        "14 complete four-frame black-background 4x contact sheets",
        "14 white-background fixed common mount ROI 6x contact sheets",
    ],
    "mount_roi_half_open": [28, 50, 100, 100],
    "dynamic_browser_or_godot_rerun": False,
    "judgment": "FRAME_VISUAL_PASS",
    "confirmed_new_p1_p2": [],
}
binding["bound_author_evidence"] = {
    name: sha(package / "qa" / name)
    for name in ["gpu_roundtrip.json", "runtime.json", "pixel_audit.json"]
}
binding_path.write_text(json.dumps(binding, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"endpoint_checks": 21, "pass": True, "binding_sha256": sha(binding_path)}, ensure_ascii=False))
