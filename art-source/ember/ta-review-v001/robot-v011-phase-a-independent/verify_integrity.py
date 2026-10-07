"""独立阶段A绑定与必要像素重算。只写本审查目录，不运行生产脚本。"""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from collections import Counter
from io import BytesIO
import hashlib
import json
import math
import re
from PIL import Image

ROOT = Path("E:/dev/shader/godot-shader/godot-shader-simple")
OUT = Path(__file__).resolve().parent
PACKAGE = OUT / "package"
FROZEN = ROOT / "art-source/ember/robot-eight-way-v011/review/phase-a-rc01"
ZIP = ROOT / "art-source/ember/deliveries/robot_eight_way_v011_phase_a_rc01_2026-10-06.zip"
EXPECTED = "ee0b416f194363d4e37e751c03446c944c217af3a2f567a03eff4a00ad91e7e6"
def sha(raw): return hashlib.sha256(raw).hexdigest()
def read_image(path): return Image.open(path).convert("RGBA")
def read_json(path): return json.loads(path.read_text(encoding="utf-8-sig"))
assert ZIP.stat().st_size == 4559554 and sha(ZIP.read_bytes()) == EXPECTED
report = {"zip_sha256": EXPECTED, "zip_bytes": ZIP.stat().st_size, "manifest": []}
with ZipFile(ZIP) as z:
    assert z.testzip() is None
    items = [r for r in z.infolist() if not r.is_dir()]
    assert len(items) == len({r.filename for r in items})
    assert len(z.infolist()) == 182 and len(items) == 181
    report["entries"] = 182
    report["regular_files"] = 181
    report["directories"] = [r.filename for r in z.infolist() if r.is_dir()]
    for item in items:
        name = item.filename
        assert not PurePosixPath(name).is_absolute() and ".." not in PurePosixPath(name).parts and ":" not in name and "\\" not in name
        target = (PACKAGE/name).resolve()
        assert target.is_relative_to(PACKAGE.resolve())
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(z.read(item))
    manifest = read_json(PACKAGE/"sha256-manifest.json")
    assert len(manifest["files"]) == len({r["file"] for r in manifest["files"]}) == 180
    for item in manifest["files"]:
        data = z.read(item["file"])
        assert len(data) == item["bytes"] and sha(data) == item["sha256"]
        source = FROZEN/item["file"]
        same = source.read_bytes() == data
        assert same
        report["manifest"].append({**item,"zip_and_frozen_source_match":same})
    report["non_manifest_members"] = sorted(set(z.namelist()) - {r["file"] for r in manifest["files"]})
    assert report["non_manifest_members"] == ["frames/idle/","sha256-manifest.json"]
    report["crc_all_pass"] = True
(OUT/"integrity-data.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({"non_manifest":report["non_manifest_members"],
    "godot_files":[r["file"] for r in report["manifest"] if r["file"].startswith("godot-review/")],
    "pilot_files":[r["file"] for r in report["manifest"] if "fixed-rig-pilot" in r["file"]]},ensure_ascii=False,indent=2))
