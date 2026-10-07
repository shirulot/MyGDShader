# 余烬采能站：Terrain 自动铺设

> 当前入口为 **[v007 全项风格统一](autotile-v007-style-unification.md)**。自动铺刷：`scenes/ember/autotile_sandbox_v007.tscn`；完整 67 项手工笔刷页：`scenes/ember/manual_brush_preview_v007.tscn`。128px 纹理对应 32 世界单位；尚待用户视觉认可。以下 v002 说明仅为历史结构基线。

## v001 复审问题与 v002 对应修订

- 地板：从 16 格重复贴图改为 47 种有实际收边的结构，每种有干净、划痕、轻锈 3 个内区变体，共 141 张不同图片。
- 墙体：移除每格重复的正面面板。中心为连续墙顶，仅在外露南侧显示立面、东侧显示深侧面，其他方向按统一左上光照包边。
- 水岸：由细框改为宽 8px 的铆接渠岸，包含外缘、压顶、水侧轮廓及内外角；水面独立，无动态效果烘焙。
- 栏杆：直段仅留薄接套；端头有黄铜柱帽，转角有连接柱，T/十字有扩大节点。长直线如需承重立柱，用独立支撑道具按固定间距布置，不强制每格一柱。
- 栈桥：各方向臂按行进方向安排踏板；转角、T、十字使用铆接平台，封闭边才放边梁；孤立平台和端头另有检修盖。
- 管线：整个 16 格图集与 v001 像素一致，SHA-256 相同，包含用户认可的四个弯管。用户认可范围仍以实际反馈为准。

修订验收采用原生与 4 倍图：先对比中心、四边、凹凸角、窄条和端头，再看矩形区域、L 形、凹洞、T 形和长直段的实际拼图。结构差异与材质随机变化分开验收；不得用不同连接编号或细小纹理变化替代正确的边角结构。

## v002 历史入口

原 `environment/tilesets/` 的 62 块是手工拼接版，没有 Terrain peering bits，部分形状缺失。
v002 使用独立 `assets/ember/environment/autotiles_v002/`，提供完整连接组合及 Godot 资源。
打开 `scenes/ember/autotile_sandbox_v002.tscn`，按 F6 运行：每个面板左键画、右键擦。
场景中的格子已序列化，可直接在编辑器修改；运行时操作不会保存回场景。

| 层 / 资源前缀 | 模式 | 组合数 | 内容 |
|---|---|---:|---|
| Floor / floor | Match Corners And Sides | 141 | 47 种结构 × 3 个内部材质变体 |
| Wall / wall | Match Corners And Sides | 47 | 中心、外边、凹凸角、窄条、端头、孤立块 |
| Water / water | Match Corners And Sides | 47 | 静态水面底色，适合独立挂水面 shader |
| Bank / bank | Match Corners And Sides | 47 | 与水面同步的岸沿，不含水面动画 |
| Pipe / pipe | Match Sides | 16 | 孤立、四端头、直线、转角、T、十字 |
| Rail / rail | Match Sides | 16 | 孤立柱及全部四向连接 |
| Bridge / bridge | Match Sides | 16 | 24px 栈桥，端头、转角、分支及十字 |

共 **330 个 Terrain 图块配置**，即 236 个基础连接配置加 94 个地板材质变体。其中水面与岸沿共享占用拓扑，但输出两张图。不要将这些装配组合重复计入独立母稿生图预算。每类独立 TileSet，Terrain Set = 0，Terrain = 0；尺寸 32×32，固定 16 色，二值 Alpha，无有向光照旋转。

## 编辑器画法

1. 选择对应 TileMapLayer，例如 `Wall`。
2. 打开底部 TileMap 面板的 **Terrains**，选择该层唯一地形。
3. 用 **Connect** 连续画或矩形填充，Godot 会自动挑选边角；使用 Tiles 面板单块绘制不会自动连接。
4. 管线、栏杆和栈桥也可使用 Path 笔刷。相邻但希望互不连接的路径应分层，避免 Connect 自动连通。

水面与岸沿必须保持相同格子集合。运行沙盒时已自动同步；在编辑器分别画两层时需自己保持一致。贴花、阀门、检修口和建筑继续独立叠放，不能当成地形连接端点。

## 程序化批量铺设

```gdscript
# 地图算法只需输出占用坐标，不需要自己挑选边角贴图。
var cells: Array[Vector2i] = [Vector2i(0,0), Vector2i(1,0), Vector2i(1,1)]
$Wall.clear()
$Wall.set_cells_terrain_connect(cells, 0, 0, false)

# 水域与岸沿传入相同坐标；分层后 shader 不会同时扭曲岸沿。
for layer in [$Water, $Bank]:
    layer.clear()
    layer.set_cells_terrain_connect(cells, 0, 0, false)
```

`false` 将空邻居作为匹配约束，正确选择封闭边和端头。小地图擦除后整层重建示例见 `scripts/ember/autotile_painter.gd`；大地图应分区重建并保留边缘邻域，避免每次拖动重铺整个世界。

## 生成与验证

先运行 `tools/build_ember_autotile_atlases.py`（Python + Pillow），执行 Godot 编辑器导入，再执行：

```text
godot --headless --path . --script res://tools/build_ember_autotiles.gd
```

普通重建保留已存在的沙盒；需要恢复演示布局时追加 `-- --rebuild-demo`。

v002 的五类修订使用可编辑原生像素结构源 `tools/ember_autotile_shapes.py` 重建，沿用既定调色板和世界方向光照；没有生成新的 AI 母稿。管线复用原生像素成品。水岸为本版 8px 规则结构，与手工版 12px 岸带不能直接混拼。栈桥采用整合边梁版，无需再叠加旧边梁。

构建器在 Godot 4.7.2 中重新加载落盘 TileSet，穷举面积类 256 种邻域、路径类 16 种邻域，并验证固定种子随机地图和擦除后重建。结果：25,541 个格子连接检查通过，见 `assets/ember/environment/autotiles_v002/validation.json`。`layout_preview.png` 来自引擎实际选出的瓦片，而非手工挑选的展示拼图。

运行 `tools/review_ember_autotiles.py` 可生成 `structure_review.png` 原生 4 倍语义对照图，并检查所有兼容接口的 Alpha 截面。本版通过 8,112 对接口检查；各图集独立图片数等于配置数，管线图集哈希与旧版一致。详见同目录 `pixel_validation.json`。哈希不同只能排除完全复制，仍须人工检查结构是否合理。

本次完成视觉自动连接；未添加物理碰撞、导航、多材质混合过渡或桥梁上下穿行逻辑。它们需按关卡规则另行配置。水面底图刻意保持静态，波纹、泡沫和动态发光仍由课程 shader 实现。

后续生图验收新增要求：面积地形按 47 blob 或可无缝组合的象限模板交付；路径按完整 16 型交付；随图提交连接位、同向端口、图集坐标与 Terrain 资源。仅有中心、四边、四角的展示图不算自动铺设完成。

Godot API 说明：https://docs.godotengine.org/en/stable/classes/class_tilemaplayer.html#class-tilemaplayer-method-set-cells-terrain-connect
