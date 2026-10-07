"""只为新目录生成导入缓存，再在真实项目中验证；不触发旧资源批量重导入。"""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
TARGET = REPO / "assets/ember/characters/enemies_v003"
MIRROR = ROOT.parent / "qa-cold/enemy_v027_installed_import_v001"
GODOT = r"E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

# 相同的 res:// 相对路径会生成实际项目可用的 remap 路径。
# 隔离项目只包含本轮新增资源，既不扫描旧资产，也不修改主项目导入默认值。
assert not MIRROR.exists(), "Use a fresh mirror directory for a repeat import."
MIRROR.mkdir(parents=True)
(MIRROR / "project.godot").write_text(
    'config_version=5\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n',
    encoding="utf-8",
)
mirror_target = MIRROR / TARGET.relative_to(REPO)
shutil.copytree(TARGET, mirror_target)
with (ROOT / "qa/installed-import.stdout.log").open("wb") as out, (
    ROOT / "qa/installed-import.stderr.log"
).open("wb") as err:
    result = subprocess.run(
        [GODOT, "--headless", "--editor", "--path", str(MIRROR), "--import"],
        stdout=out,
        stderr=err,
        timeout=60,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
assert result.returncode == 0, "See installed-import logs."

records = []
for png in sorted(TARGET.rglob("*.png")):
    imported_meta = MIRROR / png.relative_to(REPO).with_suffix(".png.import")
    metadata = imported_meta.read_text(encoding="utf-8")
    cache_match = re.search(r'^path="res://([^"]+)"', metadata, re.M)
    assert cache_match, imported_meta
    cache_relative = Path(cache_match.group(1))
    assert cache_relative.parts[:2] == (".godot", "imported")
    assert cache_relative.suffix == ".ctex"
    for key, value in [
        ("compress/mode", "0"),
        ("detect_3d/compress_to", "0"),
        ("mipmaps/generate", "false"),
        ("process/fix_alpha_border", "false"),
        ("process/premult_alpha", "false"),
    ]:
        assert re.search(r"^" + re.escape(key) + "=" + value + r"$", metadata, re.M)
    copied_cache = []
    for relative in (cache_relative, cache_relative.with_suffix(".md5")):
        source, destination = MIRROR / relative, REPO / relative
        assert source.is_file()
        # 主编辑器如果刚好已导入，只接受相同缓存，避免覆盖并发产生的异版内容。
        if destination.exists():
            assert sha(source) == sha(destination), destination
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        copied_cache.append(dict(path=relative.as_posix(), sha256=sha(destination)))
    assert sha(png) == sha(MIRROR / png.relative_to(REPO))
    shutil.copy2(imported_meta, png.with_suffix(".png.import"))
    records.append(dict(path=png.relative_to(REPO).as_posix(), cache=copied_cache))

receipt = dict(
    status="PASS_NEW_DIRECTORY_IMPORT_ONLY",
    mirror=str(MIRROR),
    png_count=len(records),
    records=records,
    scope="Only enemies_v003 PNG metadata and their uniquely named cache entries were installed.",
)
(ROOT / "qa/installed_import_receipt.json").write_text(
    json.dumps(receipt, indent=2), encoding="utf-8"
)
print(json.dumps(dict(status=receipt["status"], png_count=len(records))))
