"""Freeze the five remaining drone masters with explicit fixed-part profile assembly."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "static_preflight_s004_drone"
ZIP = ROOT.parent / "deliveries/enemy_drone_seven_directions_v013_s004_2026-10-06.zip"
assert not ZIP.exists() and not (PACKAGE / "manifest.json").exists(), "Submission already frozen"
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
catalog = json.loads((PACKAGE / "catalog.json").read_text())
checks = []
for item in catalog["entries"]:
    path = PACKAGE / (item["key"] + ".png")
    image = Image.open(path).convert("RGBA")
    assert image.size == (128, 128) and set(image.getchannel("A").getdata()) <= {0, 255}
    assert sha(path) == item["sha256"]
    if "copied_from" in item:
        assert path.read_bytes() == (ROOT / item["copied_from"].removeprefix("res://")).read_bytes()
    checks.append({"key": item["key"], "sha256": sha(path), "size": [128, 128],
                   "bounds": image.getchannel("A").getbbox(), "binary_alpha": True,
                   "preserved_copy_verified": "copied_from" in item})
sources = [
    "source/turnarounds/enemy_scout_drone_profiles_v005.png",
    "source/turnarounds/enemy_scout_drone_profiles_v006.png",
    "source/turnarounds/enemy_scout_drone_back_diagonals_v006.png",
    "source/turnarounds/enemy_scout_drone_back_diagonals_v007.png",
    "source/turnarounds/enemy_scout_drone_back_v005.png",
    "source/turnarounds/enemy_scout_drone_diagonals_c003r1.png",
    "source/approved_down/enemy_scout_drone_8x.png",
    "source/registered/drone_profile_preassembly_v001/left.png",
    "source/registered/drone_profile_preassembly_v001/right.png",
    "source/registered/drone_profile_preassembly_v001/catalog.json",
    "prompts/enemy_scout_drone_profiles_v005.txt", "prompts/enemy_scout_drone_profiles_v006.txt",
    "prompts/enemy_scout_drone_back_diagonals_v006.txt", "prompts/enemy_scout_drone_back_diagonals_v007.txt",
    "prompts/enemy_scout_drone_back_v005.txt", "drone_profile_preassembly_registration.json",
    "static_registration_drone_s004.json", "export_static_snapshot.gd",
    "entity_cutout.gdshader", "masked_part.gdshader"]
for name in sources:
    destination = PACKAGE / "provenance" / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, destination)
(PACKAGE / "native_static_qa.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
(PACKAGE / "source_provenance.json").write_text(json.dumps({name: sha(ROOT / name) for name in sources}, indent=2), encoding="utf-8")
(PACKAGE / "README.md").write_text("""# 侦察机七个新方向 s004 静态复审

状态：PENDING_TA_STATIC_REVIEW。只申请剩余五向与七向连续性复审，无新动画完成声明。

九格顺序：原 down / c002 同向身份诊断 / c003 SW；W / NW / N；NE / E / c003 SE。
原 down、c002 同向、c003 两斜前 PNG 逐字节保留；剩余 W/NW/N/NE/E 本次新增。

NW/NE 背部保持已校准的双轴结构，后面使用小暗色服务槽，前探头在远侧遮挡，未在背面复制第二探头。N 使用与正向同尺度的反向身份稿。两背斜来自同一887格源图，共用26/244×724/887比例；N的1254源画布仅按原1024参考的统一密度换算。

W/E 特别说明：生成侧向源的近圆舱仍有约3px横偏、4px多余纵距，因此使用Godot固定源部件组装校准。先共同比例导出两个原生源格，再把完整近圆舱按同一行区间归属拆出，仅刚体平移：W(-3,-4)，E(+3,-4)，远圆舱与机壳保持原纹理和尺寸；最后一次整体注册W(2,2)、E(-1,2)。没有横向拉伸整机、分别缩放风扇或手工重绘RGB。原始源格、行区间、位移、着色器与导出器快照均在provenance，轴线图只作诊断。请重点审近舱旧位置有没有残片、露底或错误遮挡，以及侧向机壳/支架结构是否成立。

轴心差约 W 0.093×14.895、E 0.018×14.951、NW31.412×11.728、NE31.128×11.756、N44.097×0.409 px。数字仅说明固定结构，不代替身份和投影审图。profiles_roi_white_16x.png 是共同ROI[48,45,34,45]的Nearest放大，无补画。

每张图128×128、二值Alpha、地面根(64,104)，固定悬浮轴线；不得将侧向总宽变窄视为缩小同一圆舱。副本范围、原图提示词、注册与逐文件SHA有记录。此包为静态审查证据，不声明独立动画工程；新增动作将另行送审。
""", encoding="utf-8")
files = sorted(p for p in PACKAGE.rglob("*") if p.is_file() and p.suffix != ".import")
manifest = {"status": "PENDING_TA_STATIC_REVIEW", "files": {
    p.relative_to(PACKAGE).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in files}}
(PACKAGE / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in files + [PACKAGE / "manifest.json"]:
        archive.write(path, path.relative_to(PACKAGE).as_posix())
with zipfile.ZipFile(ZIP) as archive:
    for name, item in manifest["files"].items():
        assert hashlib.sha256(archive.read(name)).hexdigest() == item["sha256"]
receipt = {"status": "PENDING_TA_STATIC_REVIEW", "zip": str(ZIP), "sha256": sha(ZIP),
           "payload_count": len(files), "bytes": ZIP.stat().st_size, "clean_pngs": 9}
(ROOT / "qa/drone_s004_submission_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps(receipt))
