"""PNG/Atlas/SpriteFrames独立字节绑定；不把阶段A pose称为双帧idle。"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
from zipfile import ZipFile
from PIL import Image
OUT = Path(__file__).resolve().parent
PACKAGE = OUT/"package"
ROOT = Path("E:/dev/shader/godot-shader/godot-shader-simple")
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read_image(path): return Image.open(path).convert("RGBA")
def read_json(path): return json.loads(path.read_text(encoding="utf-8-sig"))
report = read_json(OUT/"integrity-data.json")
metadata = read_json(PACKAGE/"phase-a-metadata.json")
assert metadata["canvas"] == [64,96] and metadata["root_anchor"] == [32,80] and metadata["texture_scale"] == 1
assert len(metadata["clips"]) == 10
atlas_raw = (PACKAGE/metadata["atlas"]).read_bytes()
assert sha(atlas_raw) == metadata["atlas_sha256"]
atlas = read_image(PACKAGE/metadata["atlas"])
assert atlas.size == (512,288)
assert atlas_raw == (PACKAGE/"godot-review/assets/robot_phase_a_atlas_v011.png").read_bytes()
assert (PACKAGE/"phase-a-metadata.json").read_bytes() == (PACKAGE/"godot-review/phase-a-metadata.json").read_bytes()
tres = (PACKAGE/"godot-review/robot_phase_a_v011.tres").read_text(encoding="utf-8-sig")
regions = {int(key):[int(v.strip()) for v in values.split(",")] for key,values in re.findall(r'\[sub_resource type="AtlasTexture" id="Atlas_(\d+)"\]\s+atlas = ExtResource\("1_atlas"\)\s+region = Rect2\(([^)]+)\)',tres)}
assert len(regions) == 24
resource_clips = {}
for line in tres.splitlines():
    if '"frames":' not in line: continue
    name = re.search(r'"name": &"([^"]+)"',line).group(1)
    resource_clips[name] = {"indices":[int(v) for v in re.findall(r'SubResource\("Atlas_(\d+)"\)',line)],
        "fps":float(re.search(r'"speed": ([\d.]+)',line).group(1)), "loop":'"loop": true' in line,
        "durations":[float(v) for v in re.findall(r'"duration": ([\d.]+)',line)]}
assert set(resource_clips) == {c["name"] for c in metadata["clips"]}
report["clips"] = []
report["review_pngs"] = []
old_v010 = ROOT/"art-source/ember/robot-joint-repair-v010"
old_qa = read_json(old_v010/"qa/export_validation_v010.json")
prior_snapshot = ROOT/"art-source/ember/ta-review-v001/robot-v010-independent/action-audit/snapshot/export_validation_v010.json"
assert (old_v010/"qa/export_validation_v010.json").read_bytes() == prior_snapshot.read_bytes()
old_zip = ROOT/"art-source/ember/deliveries/robot_joint_repair_v010_walk_down_candidate_2026-10-06.zip"
report["v010_zip_sha256_observed"] = sha(old_zip.read_bytes())
report["v010_prior_independent_snapshot_export_sha256"] = sha(prior_snapshot.read_bytes())
for clip in metadata["clips"]:
    resource = resource_clips[clip["name"]]
    walk = clip["action"] == "walk"
    assert len(clip["frames"]) == (8 if walk else 1)
    assert clip["fps"] == resource["fps"] == (8 if walk else 1)
    assert clip["loop"] == resource["loop"] == walk
    assert resource["durations"] == [1.0]*len(clip["frames"])
    assert len(resource["indices"]) == len(clip["frames"])
    for frame,index in zip(clip["frames"],resource["indices"]):
        path = PACKAGE/frame["file"]
        raw = path.read_bytes()
        img = read_image(path)
        assert sha(raw) == frame["sha256"] and img.size == (64,96)
        assert regions[index] == frame["region"]
        x,y,w,h = frame["region"]
        assert atlas.crop((x,y,x+w,y+h)).tobytes() == img.tobytes()
        alpha = Counter(img.getchannel("A").get_flattened_data())
        assert set(alpha) <= {0,255}
        item = {"clip":clip["name"],"frame":frame["frame"],"file":frame["file"],"sha256":sha(raw),
            "size":[64,96],"region":frame["region"],"atlas_full_rgba_equal":True,"binary_alpha":True}
        if clip["name"] == "walk_down":
            old = old_qa["frames"][frame["frame"]]
            assert sha(raw) == old["sha256"] and raw == (old_v010/old["file"]).read_bytes()
            with ZipFile(old_zip) as baseline_zip:
                candidates = [n for n in baseline_zip.namelist() if n == old["file"] or n.endswith("/"+old["file"])]
                assert len(candidates) == 1
                assert raw == baseline_zip.read(candidates[0])
                item["v010_zip_source_member"] = candidates[0]
            item["v010_source_and_prior_export_hash_byte_equal"] = True
            item["v010_zip_frame_byte_equal"] = True
        report["review_pngs"].append(item)
    report["clips"].append({"name":clip["name"],"fps":resource["fps"],"loop":resource["loop"],
        "frames":len(clip["frames"]),"spriteframes_regions_and_durations_match":True})
assert len(report["review_pngs"]) == 24
pose_down = next(c for c in metadata["clips"] if c["name"]=="pose_down")["frames"][0]
pose_sw = next(c for c in metadata["clips"] if c["name"]=="pose_down_left")["frames"][0]
assert read_image(PACKAGE/pose_down["file"]).tobytes() == read_image(old_v010/old_qa["frames"][2]["file"]).tobytes()
assert read_image(PACKAGE/pose_sw["file"]).tobytes() == read_image(PACKAGE/"source/candidate-masters/robot_idle_down_left_v011.png").tobytes()
report["pose_source_binding"] = {"pose_down_v010_f02_full_rgba_equal":True,"pose_down_left_fixed_rig_master_full_rgba_equal":True}
report["atlas_sha256"] = sha(atlas_raw)
report["atlas_size"] = list(atlas.size)
gpu = read_json(PACKAGE/"qa/godot_phase_a_v011.json")
assert gpu["atlas_sha256"] == sha(atlas_raw) and len(gpu["cases"]) == 48
report["bound_author_evidence"] = {"gpu_report_sha256":sha((PACKAGE/"qa/godot_phase_a_v011.json").read_bytes()),
    "gpu_cases":48,"playback_record_keys":list(gpu),
    "export_report_sha256":sha((PACKAGE/"qa/export_validation_phase_a.json").read_bytes()),
    "meaning":"manifest-bound author 48 GPU/natural loops only; not independently re-run"}
assert all((PACKAGE/c["file"]).is_file() for c in gpu["cases"])
report["bound_author_evidence"]["natural_playback"] = gpu["natural_playback"]
report["status"] = "ZIP_FRAME_RESOURCE_BINDING_PASS"
(OUT/"integrity-data.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"review_pngs":24,"clips":report["clips"],"gpu_report_keys":list(gpu),"status":"FRAME_ATLAS_RESOURCE_BINDING_PASS"},ensure_ascii=False,indent=2))
