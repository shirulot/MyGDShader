# 参考效果地板 v002

本包按认可效果图重新制作，保留实际 AI 母稿的涂装、厚压顶、深立面、格栅和桥头像素。`pixel_floor_v001` 保留为旧结构基线，其视觉已被用户否定。

当前艺术状态为候选；结构验收结果见 [independent_validation_v002.json](independent_validation_v002.json)。最终预览为 [Godot 实际实拼图](gpu_reference_scene_v002.png)，地板由 TileMapLayer 渲染，不是效果图背景 Sprite。

完整交付：[独立工程 ZIP](../../../../art-source/ember/deliveries/reference_floor_v002_2026-10-06.zip)。解压后打开根目录 `project.godot`，或用 `run_showcase.ps1 -GodotPath <Godot可执行文件路径>` 启动。包内含源母稿、提示词、生产资源、铺刷脚本和验证脚本。

本次结构复验 **27,909 格通过、失败0**；两套47型覆盖256邻域、不同刷序、四方向桥口与L／T／X连接。局部编译与完整重建RGBA逐字节一致；GPU中连续两次2×2擦除的水面探针均与CPU结果一致。具体证据见 [GPU结果](gpu_capture_v002.json) 与 [视觉审阅记录](art_review_v002.json)。

## 直接试铺

打开 [reference_floor_sandbox_v002.tscn](../../../../scenes/ember/reference_floor_sandbox_v002.tscn) 并运行；也可打开交付包内的独立 `project.godot`。该工程不依赖主项目的 Game autoload。

- `1`：地板；`2`：二格宽桥；`3`：单格桥。
- 鼠标左键铺刷，右键擦除。二格桥按2×2 stamp拖刷，松开鼠标后补齐。
- `Ctrl+Z`／`Ctrl+Y`：示例工具撤销／重做。
- `Ctrl+S`／`Ctrl+L`：保存／载入布局 JSON。存入 Godot 的 `user://reference_floor_v002_layout.json`。

在编辑器选场景中的 `Floor` 或 `Bridge`，通过原生 Terrain 面板铺刷；补全器监听输入修改并低频检查占用，自动更新派生图层。两层是语义输入，实际艺术显示来自 context 层。编辑器要得到参考宽桥，应刷至少两格宽区域；runtime 的 `2` 键已提供对应笔刷。

## 放入自己的场景

复制 `assets/ember/environment/reference_floor_v002/` 与 `scripts/ember/reference_floor_{compiler,painter}_v002.gd`，最好从示例的铺刷节点开始复用。复制完整示例场景时还需机器人与采能站两个PNG；独立包内已包含它们。地板和桥的原生 TileSet 分别为 [floor_terrain_v002.tres](floor_terrain_v002.tres) 与 [bridge_terrain_v002.tres](bridge_terrain_v002.tres)。

**每层 TileSet.tile_size 与 atlas region 均为128，TileMapLayer.scale必须为0.25，世界格才是32。** 示例通过 `Camera2D.zoom=(2,2)` 展示1536×1024画面，不要再把外层节点缩放两倍。通过铺刷器 `bounds_cells` 设置画布范围，默认24×16格，界外笔刷被忽略。

两套47型配置负责地形拓扑；[catalog.json](catalog.json) 记录坐标和规格。水纹、立面、钢面、压顶、桥面与桥头六个 context 层根据联合像素足迹自动派生。桥接入地板的40world通道开放，两侧各12world肩边保留压顶；T／X内口不保留横挡侧梁。

只取两张47型 atlas 可以使用原生 Terrain，但大面相位和跨材质桥口、立面效果需要补全器。不要直接在派生 context 层继续刷；它们会随输入重建。保存场景只保存输入布局，派生图层可恢复，避免把大幅 ImageTexture 嵌入场景文本。

## 可选装饰与范围

[details_catalog_v002.json](details_catalog_v002.json) 提供六件实际艺术切片：水平／竖直／转角板缝、检修格栅、水平／转角栏杆。它们作为独立 Sprite2D 装饰摆放，不参与 Terrain 邻接；示例中已组合稀疏板缝、格栅和栏杆。

本轮自动补全范围是地板、桥、桥口、压顶和平台立面。装饰网络、碰撞、导航和课程 Shader 未自动配置。示例工具的撤销重做已纳入结构验收；原生编辑器GUI撤销重做未通过UI实际操作验证，不能用runtime结果替代。

全24×16新布局的完整艺术编译约9秒；原示例校验输入布局签名后从原始PNG预热缓存，普通局部刷擦使用脏区编译。新建或重新加载无缓存布局仍需完整编译。测量值与增量／完整结果比对以独立验收JSON为准，不是所有电脑的性能承诺。

## 来源与复现

使用内置 imagegen，共五份新母稿：平台、桥、八方向角、细节和水纹。完整提示词与原文件位于 `art-source/ember/reference-floor-v002/`；[generation_manifest_v002.json](../../../../art-source/ember/reference-floor-v002/generation_manifest_v002.json) 记录源文件和SHA256。

整理仅裁切实际 artist 像素、nearest缩放、显式几何 Alpha、跨层组合与 atlas 排列。生图母稿含不透明背景，生产切片不会把这些背景误当透明。水纹是独立生图，非先前参考水域裁片。机器人和采能站复用项目已有PNG，仅在新演示中调整显示比例。

生产脚本：[build_reference_floor_v002.gd](../../../../tools/build_reference_floor_v002.gd)、[build_reference_details_v002.gd](../../../../tools/build_reference_details_v002.gd)。独立复验：[validate_reference_floor_v002.gd](../../../../tools/validate_reference_floor_v002.gd)。本包来源为 AI 生成美术，不登记为 CC0。
