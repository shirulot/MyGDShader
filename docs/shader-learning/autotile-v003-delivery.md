# v003：官方模板与美术原图订正交付

本次实际完成新的美术母稿、原生图集、7 个 Godot Terrain 和独立铺刷场景；v002 全部保留。**技术检查通过，未登记用户视觉验收通过。**

## 文件入口

- 正式来源母稿：`art-source/ember/autotiles-v003/industrial_tile_master_v003.png`，1374×1145 RGBA，imagegen 内置工具生成，原始字节保留。
- 完整提示词：同目录 `prompt.txt`；来源、母稿哈希、13 个裁剪框、色板与整理步骤：`generation-record.json`；原生采样：`samples/`。
- 引擎图集：`assets/ember/environment/autotiles_v003/{floor,wall,water,bank,pipe,rail,bridge}_autotile_v003.png`。
- 笔刷资源：同目录 `{类型}_terrain_v003.tres`，每层 Terrain Set 0 / Terrain 0。
- 坐标与连接：同目录 `catalog.json`。八邻接位序 N/NE/E/SE/S/SW/W/NW；路径位序 N/E/S/W。
- 结构放大图：同目录 `structure_review.png`；实际自动选择的拼接预览：`layout_preview.png`。
- 可交互铺刷：`scenes/ember/autotile_sandbox_v003.tscn`，F6，左键画、右键擦；水面和岸沿同步。试画不自动保存。

## 母稿如何成为图集

母稿提供五类美术形状。生成结果没有精确遵守均匀网格、32px 和调色板，墙体局部带透视，水域有不合要求的波纹，因此**母稿不能直接切片作为合格原生 atlas**。

整理时登记 13 个有效裁剪区域：三个地板面、墙顶、墙立面、渠岸、静态水色、横纵栏杆、立柱、横纵格栅、桥梁平台。低频面材质去除缩小后颗粒，统一到注册 16 色和二值 Alpha；母稿的材质与构件保留，v002 只提供拓扑轮廓和端口约束，闭合边及方向光另作原生校正。水面去除波纹，只保留静态水色。管线像素完整复用前版，未重画用户认可的拐角。

这属于 **AI 母稿采样 + 原生像素接口整理**，不是“模型直接输出了严格可用的 47 型图集”，也不是仅给 v002 加一个母稿文件名。最终每类来源区域都可在记录中复查。所有版本均未登记为 CC0。

地板 47×3=141，墙体 47，水面 47，岸沿 47，管线/栏杆/桥梁各 16，总计 330 个图块。面积基准为完整 47 型；路径 16 型与 Godot 官方简化 3×3 minimal 16 图块不同。来源与适用范围已写入 `art-generation-standard.md` 的“官方模板依据与 v003 订正规则”。

## 验证与复现

```text
python tools/build_ember_autotiles_v003.py
python tools/review_ember_autotiles.py --revision v003
godot --headless --path . --editor --import --quit
godot --headless --path . --script res://tools/build_ember_autotiles.gd -- --revision=v003
godot --headless --path . res://scenes/ember/autotile_sandbox_v003.tscn --quit-after 5
```

Godot 4.7.2 重新加载保存资源，检查完整邻域、随机布局、擦除后重建：25,541 格，失败 0；兼容像素端口 Alpha 截面检查 8,112 对，失败 0；管线解码像素与 v001/v002 一致。详见输出目录 `validation.json`、`pixel_validation.json`，导入/构建/运行日志在母稿批次目录。

放大图展示中心、边、内外角、孤立、窄连接、端头与十字；实际布局含凹洞、分支与长直段。测试验证连接拓扑与透明轮廓，不宣称不同方向边缘 RGB 完全相等；方向光和材质允许受控色差。

## 尚未计为完成

用户尚未确认美术观感；32px 下的材质密度仍可继续审阅。没有新增碰撞、导航、多材质混合过渡或桥下穿行逻辑，也没有代做课程 Shader。没有将 330 个派生配置计作新增 330 项独立艺术母稿。2×2 与简化 16 模板只作为对照来源，未将其当作本项目完整覆盖。
