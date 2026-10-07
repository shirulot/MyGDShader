"""Freeze the patrol pilot and publish only this fixed review payload on port 6106."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT.parent / "enemy-eight-directions-v013-pilot-patrol-v001"
ZIP = ROOT.parent / "deliveries/enemy_eight_directions_v013_pilot_patrol_v001_2026-10-06.zip"
WEB = ROOT.parent / "enemy-sequences-v001/previews/eight-direction-v013-patrol-v001"
UNIT = "enemy_patrol"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(relative):
    destination = PACKAGE / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / relative, destination)


assert not PACKAGE.exists() and not ZIP.exists() and not WEB.exists(), "Frozen version already exists"
catalog = json.loads((ROOT / "output/pilot_catalog_v013.json").read_text())
assert len(catalog["clips"]) == 1 and catalog["clips"][0]["unit"] == UNIT
for report in ["pilot_pixel_audit.json", "pilot_gpu_roundtrip.json", "pilot_runtime.json"]:
    data = json.loads((ROOT / "qa" / report).read_text())
    assert data["status"] == "PASS" and data["catalog_sha256"] == sha(ROOT / "output/pilot_catalog_v013.json")
PACKAGE.mkdir()
for name in ["project.godot", "preview.gd", "preview.tscn", "pilot_rig.gd", "pilot_rigs.json",
             "entity_cutout.gdshader", "masked_part.gdshader", "pilot_tread.gdshader",
             "pilot_fan.gdshader", "pilot_fan_body.gdshader", "export_pilots.gd",
             "verify_pilots.gd", "verify_pilot_assets.py", "capture_pilots.gd", "previews/index.html",
             "output/pilot_catalog_v013.json", f"output/{UNIT}_pilot_v013.tres",
             f"source/registered/{UNIT}_down_right_s002.png"]:
    copy(name)
for directory in [ROOT / "output" / UNIT, ROOT / "reference" / UNIT]:
    for path in directory.rglob("*.png"):
        copy(path.relative_to(ROOT))
for pattern in ["enemy_patrol_move_*.png", "enemy_patrol_rig_bind_*.png", "patrol_se_eight_legs_8x.png",
                "pilot_pixel_audit.json", "pilot_gpu_roundtrip.json", "pilot_runtime.json", "pilot_runtime.png",
                "picker_enemy_patrol.png"]:
    for path in (ROOT / "qa").glob(pattern):
        copy(path.relative_to(ROOT))
static = {"scope": "Patrol s002 approved direction source; this new animation is pending separate TA review",
          "review_report": "art-source/ember/ta-review-v001/enemy-patrol-v013-s002/review-static.md",
          "reviewed_zip": "enemy_patrol_seven_directions_v013_s002_2026-10-06.zip",
          "reviewed_zip_sha256": "28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1",
          "direction_source_sha256": sha(ROOT / f"source/registered/{UNIT}_down_right_s002.png")}
(PACKAGE / "STATIC_SOURCE_RECEIPT.json").write_text(json.dumps(static, indent=2), encoding="utf-8")
(PACKAGE / "README.md").write_text("""# 巡逻兵右下移动小样 v001

本固定包仅申请巡逻兵 move_down_right 一条八帧动作验收。其七向静态母版已通过 s002；本动作状态仍为 PENDING_TA_REVIEW。原 v012 down 保留。

128×128 / root(64,104) / Nearest / 8 frames / 8 FPS / loop。原生方向源与 s002/c002 SE 字节一致；中性绑定全 RGBA 零差。膝甲与完整靴为刚体平移，短暗色连接轴使用关节端点映射；相位取自已通过 v008 down。遮罩分区已排除邻近夹爪，并把完整靴缘归回正确脚。所有帧使用同一源图与注册，无逐帧生成或 bbox 归一化。

Godot 打开 project.godot 可直接运行。选择各方向会保留已存在移动的 frame/frame_progress；其余六个新方向只显示已过静态母版且明确写未制作。正常/1FPS、原生/4×与深浅底供审阅；八帧腿部共同ROI附 qa/patrol_se_eight_legs_8x.png。

qa 中作者自检绑定当前 catalog：PNG/atlas/嵌入 SpriteFrames 一致；黑白两底共16次 live rig/PNG GPU 对照零差；四播放器覆盖八帧及循环；八方向切换检查。上述技术结果不替代 TA 视觉通过。

pilot_rigs.json 保留公共管线的其他单位定义，但 enabled_pilot_units 只有 patrol；本包不包含或申请其它单位的新动画。生成元数据脚本依赖历史 v008，因此未作为独立入口打包；本包实际运行和导出只读取已冻结的 pilot_rigs.json。
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
web_binding = {path.relative_to(WEB).as_posix(): sha(path) for path in WEB.rglob("*") if path.is_file()}
receipt = {"package": str(PACKAGE), "zip": str(ZIP), "zip_sha256": sha(ZIP),
           "bytes": ZIP.stat().st_size, "payload_count": len(files),
           "catalog_sha256": sha(PACKAGE / "output/pilot_catalog_v013.json"),
           "web_url": "http://127.0.0.1:6106/eight-direction-v013-patrol-v001/index.html",
           "web_files": web_binding, "status": "PENDING_TA_REVIEW"}
(ROOT / "qa/patrol_v001_submission_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps({key: value for key, value in receipt.items() if key != "web_files"}))
