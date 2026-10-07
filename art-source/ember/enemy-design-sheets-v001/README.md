# Ember 敌人三视图与零件拆分设定 v001

日期：2026-10-06。以已认可的 4 张敌人母稿为造型基准，沿用浅装甲、蓝灰结构、少量黄铜和克制磨损。共 8 张最终设定图。

| 单位 | 三视图：正面 / 右侧 / 背面 | 零件拆分设定 |
|---|---|---|
| 轻型巡逻兵 | [查看](three_views/enemy_patrol_three_views_v001.png) | [查看](parts/enemy_patrol_parts_v001.png) |
| 近战切割工蜂 | [查看](three_views/enemy_cutter_three_views_v002.png) | [查看](parts/enemy_cutter_parts_v002.png) |
| 履带重装机 | [查看](three_views/enemy_tracked_heavy_three_views_v001.png) | [查看](parts/enemy_tracked_heavy_parts_v002.png) |
| 悬浮侦察机 | [查看](three_views/enemy_scout_drone_three_views_v002.png) | [查看](parts/enemy_scout_drone_parts_v002.png) |

三视图保持原母稿的轻俯角正交镜头，仅绕机身竖轴改变朝向；用于确定造型、前后体积和工具位置。所有“左 / 右”均指单位自身：正面看时，单位右侧在画面左侧。图片之间为各自清晰展示做排版，不用于跨单位量取实际尺寸。

拆分图按主要装配件标号，图中短英文标签对应 [中文零件清单](parts_index_zh_v001.md)。配对部件使用同一编号分组；工蜂明确为 4 支承重腿与 2 条工具臂，侦察机为 2 套护罩 / 转子 / 电机，重装机为左右两套履带。

本轮交付范围是静态像素美术设定母稿，可作为原生像素修整、分层与动作设计的依据。背部维修盖与简洁内部框架是基于母稿补充的设计。本轮图片带设定板背景和编号，不是已裁切注册的透明游戏零件或动画帧。

已复核工具左右、侧视投影、部件数量和编号。最终版本修正了工蜂侧视锯盘、侦察机侧视风扇遮挡、履带左右名称，以及分件图中底盘 / 护罩的重复形状。

全部生成与定点修正均使用内置 imagegen，原始输出保留在工具默认目录。工作区的三视图、分件图、母稿副本及每次提示词均有保存。最终版本以 [design_catalog_v001.json](design_catalog_v001.json) 为准；[source_specs_v001.json](source_specs_v001.json) 保留初始生成约束，`prompts/` 包含初稿与修正提示词。每张 PNG 旁的 `.generation.json` 记录工具、原始路径、参考路径及提示词。

[下载最终设定包](enemy_design_sheets_v001_2026-10-06.zip)：仅包含 8 张选定图、对应生成记录、4 张认可母稿、全部提示词、中文清单和索引；草稿留在工作区供追溯。

