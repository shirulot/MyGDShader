"""只读检查整数预览逐像素一致性与本批交付尺寸，不改变图片。"""
import json
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[4]
batch = root / "art-source/ember/batch-01"
index = json.loads((batch / "diagnostics/index.json").read_text(encoding="utf-8"))
results = []
for asset in index["assets"]:
    # 打开一次，直接核对每个源像素的四个2倍展示像素，包含透明RGB与Alpha。
    with Image.open(root / asset["probe"]) as source, Image.open(root / asset["preview_2x"]) as preview:
        a, b = source.convert("RGBA"), preview.convert("RGBA")
        expected = tuple(asset["probe_size"])
        passed = a.size == expected and b.size == (a.width * 2, a.height * 2)
        passed = passed and all(b.getpixel((x * 2 + dx, y * 2 + dy)) == a.getpixel((x, y))
                                for y in range(a.height) for x in range(a.width)
                                for dx, dy in [(0, 0), (1, 0), (0, 1), (1, 1)])
        results.append({"id": asset["id"], "size": a.size, "exact_rgba_2x": passed})
with Image.open(root / "art-source/ember/references/batch01_style_scale_diagnostic_v001.png") as board:
    assert board.size == (1536, 1024)
with Image.open(batch / "diagnostics/all_floor_adjacencies_v001.png") as board:
    assert board.size == (1536, 1024)
for kind in ("clean", "worn", "grate", "wet"):
    with Image.open(batch / f"diagnostics/tiling_{kind}_3x3_4x.png") as tiled:
        assert tiled.size == (384, 384)
assert all(item["exact_rgba_2x"] for item in results)
assert not list((root / "assets/ember").rglob("*.png"))
print(json.dumps({"integer_previews": results, "diagnostic_board_sizes_passed": True,
                  "formal_pngs": 0}, ensure_ascii=False, indent=2))

