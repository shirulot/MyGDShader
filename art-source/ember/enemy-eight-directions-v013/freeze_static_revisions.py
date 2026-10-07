"""Freeze static review submissions; images are read or copied, never repainted."""
from pathlib import Path
from collections import Counter, deque
from PIL import Image
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
DELIVERIES = ROOT.parent / "deliveries"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_png(path):
    # Inspect native RGBA coverage and connected pieces without changing pixels.
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    counts = Counter(alpha.getdata())
    remaining = {(x, y) for y in range(image.height) for x in range(image.width)
                 if alpha.getpixel((x, y)) != 0}
    pieces = []
    while remaining:
        start = remaining.pop()
        pending = deque([start])
        count = 1
        while pending:
            x, y = pending.popleft()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    point = (x + dx, y + dy)
                    if point in remaining:
                        remaining.remove(point)
                        pending.append(point)
                        count += 1
        pieces.append(count)
    assert image.size == (128, 128), str(path)
    assert set(counts).issubset({0, 255}), str(path)
    return {"size": list(image.size), "alpha_counts": dict(counts),
            "bounds": alpha.getbbox(), "components_8_connected": sorted(pieces, reverse=True),
            "sha256": digest(path)}


def freeze(folder_name, spec_name, raw_names, zip_name, readme):
    folder = ROOT / folder_name
    target_zip = DELIVERIES / zip_name
    if target_zip.exists() or (folder / "manifest.json").exists():
        raise RuntimeError(f"Refusing to mutate frozen submission: {folder}")
    catalog = json.loads((folder / "catalog.json").read_text(encoding="utf-8"))
    audit = {}
    for entry in catalog["entries"]:
        image = folder / (entry["key"] + ".png")
        audit[entry["key"]] = audit_png(image)
        assert digest(image) == entry["sha256"]
        if "copied_from" in entry:
            original = ROOT / entry["copied_from"].removeprefix("res://")
            assert image.read_bytes() == original.read_bytes()
            audit[entry["key"]]["preserved_source_verified"] = str(original)
    (folder / "source").mkdir(exist_ok=True)
    sources = {}
    for name in raw_names:
        original = (ROOT / "prompts" / name) if name.endswith(".txt") else (ROOT / "source" / "turnarounds" / name)
        destination = folder / "source" / name
        shutil.copy2(original, destination)
        sources[name] = {"sha256": digest(destination), "original": str(original)}
    shutil.copy2(ROOT / spec_name, folder / "registration.json")
    shutil.copy2(ROOT / "export_static_snapshot.gd", folder / "export_static_snapshot.gd")
    (folder / "source_provenance.json").write_text(json.dumps(sources, indent=2), encoding="utf-8")
    (folder / "native_static_qa.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    (folder / "README.md").write_text(readme, encoding="utf-8")
    payloads = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix != ".import")
    manifest = {"status": "PENDING_TA_STATIC_REVIEW", "files": {
        p.relative_to(folder).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size}
        for p in payloads}}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in payloads + [folder / "manifest.json"]:
            archive.write(path, path.relative_to(folder).as_posix())
    with zipfile.ZipFile(target_zip) as archive:
        for name, item in manifest["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == item["sha256"]
    receipt = {"folder": str(folder), "zip": str(target_zip), "sha256": digest(target_zip),
               "bytes": target_zip.stat().st_size, "payload_count": len(payloads),
               "native_png_count": len(audit), "archive_hash_validation": "PASS",
               "status": "PENDING_TA_STATIC_REVIEW"}
    print(json.dumps(receipt))
    return receipt


receipts = [freeze(
    "static_preflight_v002_patrol", "static_registration_patrol_v002.json",
    ["enemy_patrol_remaining_five_v003.png", "enemy_patrol_remaining_five_v003.txt",
     "enemy_patrol_remaining_five_v004.png", "enemy_patrol_remaining_five_v004.txt"],
    "enemy_patrol_seven_directions_v013_s002_2026-10-06.zip",
    """# 巡逻兵七个新方向静态复审 s002

状态：待技术美术总监审核，不代表任何新增动画通过。

联系图按行排列：原 down / c002 同向身份诊断 / SW；W / NW / N；NE / E / SE。
原 down、c002 同向诊断与 SW、SE 均逐字节保留。新增 W、NW、N、NE、E 来自固定 v004 五视图母版；v003 的 NE 方向错误已在 v004 修正。

128×128、Nearest、根点(64,104)。新五视图共用一个源图密度 52/392，绝不单视图或逐帧 bbox 归一化。该图是 512 格，与 c002 的 724 格源图不同；原生角色站立高度仍约 52 px。对应源图、完整提示词、注册点与缩放均有记录，请审核侧背向身份、工具侧别与尺度连续性。

native_static_qa.json 仅说明尺寸、透明度、连通性及复制校验，不能替代视觉验收。export_static_snapshot.gd 是主工作项目中的导出器快照；本静态包不是独立 Godot 动画工程，res:// 源定位对应登记的工作项目。
"""), freeze(
    "calibration_check_c003_drone", "static_registration_drone_c003.json",
    ["enemy_scout_drone_diagonals_c003.png", "enemy_scout_drone_diagonals_c003.txt",
     "enemy_scout_drone_diagonals_c003r1.png", "enemy_scout_drone_diagonals_c003r1.txt"],
    "enemy_drone_diagonal_calibration_v013_c003_2026-10-06.zip",
    """# 侦察机斜向刚性转向复审 c003

状态：待技术美术总监审核。此次仅修正 SW、SE；其余新方向及动画未计为完成。

联系图从左至右：原 down、已通过的 c002 同向身份诊断、SW、SE。前两张逐字节保留，未重新生成正面。源图 c003r1 是提交前的内部修正，c003 初稿未送审。

两轴心差：SW = (30.680, 11.069) px；SE = (30.577, 10.993) px，接近正向 44 px 跨距在 45 度转向后的 31×11 px 投影。axis_guides_8x.png 只用于诊断；交付 neutral PNG 不含参考线。保持双电机、双四叶转子、小探头及暗红窄传感条，未整体横向压缩正面图。

新二格源图共用 c002 缩放 26/244 × 单次源格密度换算 724/887。横向根注册为双轴中心的中点，纵向注册为中央小探头底端(64,80)，地面根仍(64,104)。未按各风扇或单帧缩放。

native_static_qa.json 与 manifest.json 绑定清洁 PNG、源图、提示词与诊断。export_static_snapshot.gd 是主工作项目导出器快照；本包仅供静态审查，不是独立动画工程。
""")]
(ROOT / "qa" / "static_revision_submissions.json").write_text(json.dumps(receipts, indent=2), encoding="utf-8")
