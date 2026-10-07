"""Freeze one drone movement candidate; existing reviewed packages are immutable."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent / "enemy-eight-directions-v013-pilot-drone-v001"
ZIP = ROOT.parent / "deliveries/enemy_eight_directions_v013_pilot_drone_v001_2026-10-06.zip"
WEB = ROOT.parent / "enemy-sequences-v001/previews/eight-direction-v013-drone-v001"
UNIT = "enemy_scout_drone"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(relative):
    destination = PACKAGE / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / relative, destination)


assert not PACKAGE.exists() and not ZIP.exists() and not WEB.exists(), "Frozen version already exists"
catalog = json.loads((ROOT / "output/pilot_catalog_v013.json").read_text())
assert len(catalog["clips"]) == 1 and catalog["clips"][0]["unit"] == UNIT
for name in ["pilot_pixel_audit.json", "pilot_gpu_roundtrip.json", "pilot_runtime.json"]:
    report = json.loads((ROOT / "qa" / name).read_text())
    assert report["status"] == "PASS" and report["catalog_sha256"] == sha(ROOT / "output/pilot_catalog_v013.json")
PACKAGE.mkdir()
for name in ["project.godot", "preview.gd", "preview.tscn", "pilot_rig.gd", "pilot_rigs.json",
             "entity_cutout.gdshader", "masked_part.gdshader", "pilot_tread.gdshader",
             "pilot_fan.gdshader", "pilot_fan_body.gdshader", "export_pilots.gd",
             "verify_pilots.gd", "verify_pilot_assets.py", "capture_pilots.gd", "previews/index.html",
             "inspect_drone_pilot.gd", "output/pilot_catalog_v013.json", f"output/{UNIT}_pilot_v013.tres",
             f"source/registered/{UNIT}_down_right_s004.png", "source/parts/rotor_well_master.png"]:
    copy(name)
for directory in [ROOT / "output" / UNIT, ROOT / "reference" / UNIT]:
    for path in directory.rglob("*.png"):
        copy(path.relative_to(ROOT))
for pattern in ["enemy_scout_drone_move_*.png", "enemy_scout_drone_rig_bind_*.png", "drone_se_eight_rotors_8x.png",
                "pilot_pixel_audit.json", "pilot_gpu_roundtrip.json", "pilot_runtime.json", "pilot_runtime.png",
                "picker_enemy_scout_drone.png"]:
    for path in (ROOT / "qa").glob(pattern):
        copy(path.relative_to(ROOT))
shutil.copy2(ROOT.parent / "enemy-drone-actions-v011/source/rotor_well_prompt.txt",
             PACKAGE / "source/parts/rotor_well_prompt.txt")
static = {"scope": "Approved s004/c003 SE silhouette and approved v011 rotor source; new animation pending TA",
          "review_report": "art-source/ember/ta-review-v001/enemy-drone-v013-s004/review-s004.md",
          "reviewed_zip": "enemy_drone_seven_directions_v013_s004_2026-10-06.zip",
          "reviewed_zip_sha256": "3a6dc8a5ab9c16dc5e71d083568768ff3cabefae2675d5385e552149acb79342",
          "direction_source_sha256": sha(ROOT / f"source/registered/{UNIT}_down_right_s004.png"),
          "rotor_source_sha256": sha(ROOT / "source/parts/rotor_well_master.png"),
          "rotor_approved_zip_sha256": "13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e"}
(PACKAGE / "STATIC_SOURCE_RECEIPT.json").write_text(json.dumps(static, indent=2), encoding="utf-8")
(PACKAGE / "README.md").write_text("""# 侦察机右下移动小样 v001

仅申请 move_down_right 一条八帧动作验收，状态 PENDING_TA_REVIEW。其完整七向静态 s004 已通过；原 v012 down 保持。128×128 / root(64,104) / Nearest / 8帧 / 8FPS / loop。

机壳、支架、风筒、短探头均来自通过的 s004/c003 SE 原图。只在两处椭圆风口内装入已通过 v011 的固定转子和井底，不使用 v011-r1 探头实验稿。绑定178像素变化全部在两处风口内；外部RGBA零差。两轴分别(48.5,69.5)/(79.5,58.5)，风口半径(6.5,4.5)。转子先在自身平面转动，再投影为椭圆；近侧与远侧反向，八帧覆盖四叶转子的90度周期。机体只有固定1px升降，不变形或改变轴距。

Godot 打开 project.godot 运行，或查看本包 previews/index.html 对应的固定网页。方向选择保持已制作动作的帧相位；六个未制作方向仅显示已过静态并标明状态。提供8FPS/1FPS、原生/4倍、深浅底及共同ROI八帧图。原生PNG、atlas、嵌入SpriteFrames一致；16次黑白底 live rig/PNG 对照零差；4个真实播放器完整循环及8方向切换自检通过。技术结果不代替TA视觉审查。

pilot_rigs.json 内保留公共管线其它单位定义，但 enabled_pilot_units 仅侦察机。本包只申请一条动作；运行和导出使用冻结的JSON，不依赖元数据生成脚本或外部路径。
""", encoding="utf-8")
files = sorted(path for path in PACKAGE.rglob("*") if path.is_file())
manifest = {"status": "PENDING_TA_REVIEW", "clips": 1, "frames": 8, "files": {
    path.relative_to(PACKAGE).as_posix(): {"sha256": sha(path), "bytes": path.stat().st_size} for path in files}}
(PACKAGE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in files + [PACKAGE / "manifest.json"]:
        archive.write(path, path.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as archive:
    for name, data in manifest["files"].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == data["sha256"]
WEB.mkdir()
shutil.copy2(PACKAGE / "previews/index.html", WEB / "index.html")
shutil.copy2(PACKAGE / "output/pilot_catalog_v013.json", WEB / "pilot_catalog_v013.json")
for name in ["output", "reference"]:
    for path in (PACKAGE / name).rglob("*.png"):
        destination = WEB / path.relative_to(PACKAGE)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
receipt = {"package": str(PACKAGE), "zip": str(ZIP), "zip_sha256": sha(ZIP),
           "bytes": ZIP.stat().st_size, "payload_count": len(files),
           "catalog_sha256": sha(PACKAGE / "output/pilot_catalog_v013.json"),
           "web_url": "http://127.0.0.1:6106/eight-direction-v013-drone-v001/index.html",
           "web_files": {p.relative_to(WEB).as_posix(): sha(p) for p in WEB.rglob("*") if p.is_file()},
           "status": "PENDING_TA_REVIEW"}
(ROOT / "qa/drone_v001_submission_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps({key: value for key, value in receipt.items() if key != "web_files"}))
