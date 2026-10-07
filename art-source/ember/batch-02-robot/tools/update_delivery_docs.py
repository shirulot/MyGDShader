"""Godot通过后同步当前计数和文档；保留首批与瓦片包的历史范围。"""
import csv
import io
import json
from pathlib import Path

BATCH = Path(__file__).resolve().parents[1]
ROOT = BATCH.parents[2]
DOCS = ROOT / "docs/shader-learning"
proof = json.loads((BATCH / "review/godot_validation_v001.json").read_text(encoding="utf-8"))
if proof.get("status") != "GODOT_ROBOT_ANIMATION_VALIDATED":
    raise SystemExit("Godot尚未通过，不能登记资源完成")

def update(path, before, after):
    text = path.read_text(encoding="utf-8")
    if before not in text:
        if after in text:
            return
        raise ValueError(f"未匹配预期文档段落：{path.name}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")

update(ROOT / "assets/ember/README.md",
       "当前已正式交付 **64/123 个艺术单元，剩余 59 未完成**：三套瓦片集共 62 单元，加机器人朝下待机一帧与采能站各 1。共 **5 张生产 PNG**（3 张 atlas＋2 张对象图）；图集打包、重复刷块与审阅图不增加艺术计数。三套 TileMapLayer 瓦片资源已通过 Godot 4.7.2 实际导入、保存重载与渲染验证。",
       "当前已正式交付 **83/123 个艺术单元，剩余 40 未完成**：三套瓦片集共 62 单元、机器人四向 20 帧与采能站 1。共 **25 张生产 PNG**（3 张瓦片 atlas＋20 张角色单帧＋1 张角色 atlas＋1 张采能站）；图集打包、重复刷块与审阅图不增加艺术计数。TileMapLayer 和机器人 SpriteFrames 已通过 Godot 4.7.2 实际导入、保存重载与渲染验证。")
update(ROOT / "assets/ember/README.md", "C01 仅完成 1/20 帧；其余 19 帧尚未制作。",
       "C01 **20/20 帧完成**，详见[四向动画报告](../../docs/shader-learning/asset-production-batch-02-robot.md)。将[robot_sprite_frames_v001.tres](characters/robot/robot_sprite_frames_v001.tres)指定给自己的 AnimatedSprite2D，或打开[机器人预览场景](../../scenes/ember/robot_animation_sandbox.tscn)。walk 8 FPS；centered=false、offset=(-32,-80)、Nearest。")
update(DOCS / "tilemap-reusable-tilesets.md",
       "全套正式进度为 **64/123，剩余 59 未完成**，首批 **6/6** 完成。C01 仍仅 1/20 帧，详细数值见[首批最新结果](asset-production-batch-01.md#当前交付2026-10-04-原生像素整理完成)。",
       "当前全套正式进度为 **83/123，剩余 40 未完成**，首批 **6/6** 完成。后续 C01 四向 **20/20 帧已完成**，见[机器人动画报告](asset-production-batch-02-robot.md)；本文瓦片范围仍为 62 单元。")
update(DOCS / "asset-production-batch-01.md",
       "## 当前交付：2026-10-04 原生像素整理完成",
       "当前后续进度为 **83/123，剩余 40**；C01 四向 **20/20 帧已完成**，详见[机器人动画报告](asset-production-batch-02-robot.md)。下文保存首批完成时的范围与计数；原朝下待机、采能站和四地板未改动。\n\n## 首批交付快照：2026-10-04 原生像素整理完成")
update(DOCS / "asset-production-batch-01.md",
       "这些历史状态不覆盖上面的 2026-10-04 正式结果。",
       "这些历史状态不覆盖首批正式结果与后续机器人动画交付。")
resources = DOCS / "resources.md"
addition = "2026-10-04 后续批次：C01 机器人四向 **20/20 帧及 8 组 SpriteFrames 动画已完成**；本批 19 次实际 imagegen 调用、19 份母稿及原生整理记录见[机器人动画报告](asset-production-batch-02-robot.md)和[生成记录](../../art-source/ember/batch-02-robot/generation-record.json)。来源为 `AI_MATERIAL_AND_POSE_REFERENCE_WITH_NATIVE_PIXEL_FINISH`，不登记为 CC0。原朝下待机 SHA 不变；当前全套 **83/123，剩余 40**。下方 64/123 是瓦片批次完成时的历史快照。\n\n"
text = resources.read_text(encoding="utf-8")
if addition not in text:
    resources.write_text(text.replace("## 资源原则", addition + "## 资源原则", 1), encoding="utf-8")
manifest = DOCS / "asset-generation-manifest.csv"
rows = list(csv.DictReader(io.StringIO(manifest.read_text(encoding="utf-8"))))
for row in rows:
    if row["id"] == "C01":
        row["proposed_path"] = "assets/ember/characters/robot/robot_animations_v001.png"
        row["status"] = "NATIVE_ANIMATION_20_OF_20_GODOT_VERIFIED"
buffer = io.StringIO(newline="")
writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n")
writer.writeheader()
writer.writerows(rows)
manifest.write_text(buffer.getvalue(), encoding="utf-8")
update(DOCS / "asset-production-batch-02-robot.md",
       "Godot 资源和独立工程验证正在执行，完成后补入本报告。",
       "[Godot 实际报告](../../art-source/ember/batch-02-robot/review/godot_validation_v001.json)已确认导入、SpriteFrames 保存重载与实际播放；完整循环、渲染及无原缓存复用证据见本批 review 目录。")
record_path = BATCH / "generation-record.json"
record = json.loads(record_path.read_text(encoding="utf-8"))
record.update(approved_new_production_frames=19, total_C01_accepted_frames=20,
              status="C01_NATIVE_20_FRAMES_ART_AND_GODOT_VERIFIED", completed_art_units_total=83,
              remaining_art_units=40, art_review="art-source/ember/batch-02-robot/art-review-v001.json",
              godot_review="art-source/ember/batch-02-robot/review/godot_validation_v001.json")
record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print("C0120/20、全套83/123及当前文档已同步")
