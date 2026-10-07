# 地板材质扩展 v004

在同一构造标准下继续新增三份实际生图：浅砂混凝土、青绿旧涂层、磨损灰白地砖。连同原蓝灰、浅灰控制区、深灰防滑和锈褐旧仓区，共七种可混铺表面。当前新增材质为视觉候选。

| 材质ID／快捷键 | 表面 | 适用区域 |
| --- | --- | --- |
| 0／4 | 蓝灰涂装钢板 | 普通平台与通道 |
| 1／5 | 浅灰控制区地板 | 清洁操作区 |
| 2／6 | 深灰防滑钢板 | 设备检修区 |
| 3／7 | 锈褐旧仓区钢板 | 旧仓库与港区 |
| 4／8 | 浅砂混凝土 | 装卸区、公共作业平台 |
| 5／9 | 青绿旧涂层 | 泵房、工艺处理区 |
| 6／0 | 磨损灰白地砖 | 实验室、铺砖操作区 |

## 试铺入口

打开[七材质混铺场景](../../../../scenes/ember/reference_floor_sandbox_v004.tscn)。工作区完整交付：[独立工程ZIP](../../../../art-source/ember/deliveries/reference_floor_v004_2026-10-06.zip)。解压打开根目录 `project.godot`，运行即可试刷。

`1`当前地板、`2`宽桥、`3`窄桥；`4～9`及`0`选表面并回到地板笔刷；`[`／`]`循环材质。左键新增地板或换材质，右键擦除。Ctrl+Z／Y撤销重做，Ctrl+S／L保存载入。

独立地图：[混凝土](../../../../scenes/ember/reference_floor_concrete_sandbox_v004.tscn)、[青绿涂层](../../../../scenes/ember/reference_floor_teal_sandbox_v004.tscn)、[灰白地砖](../../../../scenes/ember/reference_floor_ceramic_sandbox_v004.tscn)。每张地图启动即选中对应材质，避免误刷成默认钢面。启动脚本参数 `-Map mixed/concrete/teal/ceramic`，可指定 `-GodotPath`。

[实际GPU对比图](gpu_material_comparison_v004.png) 左上混凝土、右上青绿、左下地砖、右下七材质混铺。[完整混铺图](gpu_mixed_scene_v004.png) 可查看跨材质桥口与外边结构。均为实际TileMapLayer场景截图。

## 固定标准与材质变化

保持128texture格、32world格、TileMapLayer.scale=0.25；示例Camera2D.zoom=2。压顶8world、南向立面32world、默认二格桥体40world、接岸每侧12world肩口保持原样。

混凝土增加骨料、细坑与稀疏发丝裂纹；青绿涂层增加银灰露底与少量腐蚀；地砖使用低对比、齐平的细填缝，属于表面图案。地砖线不是平台边框或结构缝，不会制造碰撞、立面或漏水孔。

七种材质共用一份Floor／Bridge占用。原生47型只计算结构，`FloorMaterials`普通输入层保存材质ID，context自动组合艺术像素。编辑器先刷Floor范围，再在FloorMaterials选择对应索引块；空白是默认钢面。材质交界不会产生内墙或内部压顶。

材质目录 [catalog.json](catalog.json) 驱动合法ID、索引宽度、快捷循环和独立地图默认笔刷。v004可以读取旧v2、v3存档；旧v003读取器不会保留新材质ID 4～6。v004存档仍为version3结构，文件为 `user://reference_floor_v004_layout.json`。PNG SHA和布局签名在启动时核验缓存，局部铺刷不重复读原稿。

## 复用、验证与来源

复用时保留v002公共构造、v003前三份新增表面、v004新表面与索引集，使用 `reference_floor_compiler_v002.gd` 与 `reference_floor_painter_v004.gd`。完整独立包已包含依赖和机器人／采能站。装饰仍单独摆放，碰撞、导航与课程Shader未改变。

新增源稿、完整提示词和SHA见 [generation_manifest_v004.json](../../../../art-source/ember/reference-floor-v004/generation_manifest_v004.json)，通过内置imagegen生成。nearest注册为1024×1024世界相位表面周期，不程序改色或量化艺术像素。整理记录见 [source_processing_v004.json](source_processing_v004.json)。

30组横纵材质交界、12个四向桥口、12次增量／完整RGBA对照、运行时撤销重做与JSON／场景重载均通过。负坐标原点平移并恢复的布局也通过全域像素与504个context格映射检查，避免同尺寸偏移时错误复用缓存。三种新材质实际GPU更新与CPU样点一致，最大RGB误差0。旧103份生产资源与代码和v003交付包SHA相同。

验证见 [independent_validation_v004.json](independent_validation_v004.json) 与 [gpu_capture_v004.json](gpu_capture_v004.json)。原生编辑器GUI撤销重做仍为未测，PNG实际篡改后的缓存回退分支未额外执行测试。本机新布局完整编译14.5秒，普通局部刷新约0.7～1.2秒，测量见catalog与GPU报告；运行已缓存地图直接读取成品图层。

[统一标准](../../../../docs/shader-learning/reference-floor-v004-materials.md) · [生产脚本](../../../../tools/build_reference_floor_v004.gd)
