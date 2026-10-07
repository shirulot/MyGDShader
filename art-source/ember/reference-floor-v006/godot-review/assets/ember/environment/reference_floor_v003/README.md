# 多材质地板 v003

沿用用户认可继续扩展的v002构造风格，新增三种实际生图表面，共四种可混铺材质。当前新材质仍为视觉候选。

| ID／快捷键 | 地板 | 场景用途 |
| --- | --- | --- |
| 0／4 | 原蓝灰涂装钢板 | 普通平台、通道 |
| 1／5 | 浅灰控制区地板 | 控制室、清洁操作区 |
| 2／6 | 深灰防滑钢板 | 设备检修区、维修平台 |
| 3／7 | 锈褐旧仓区钢板 | 老旧仓库、港区平台 |

[四种地图的实际GPU对比图](gpu_material_comparison_v003.png) 按左上蓝灰、右上浅灰、左下深灰、右下锈褐排列。[混铺图](gpu_mixed_scene_v003.png) 展示同一地图内的材质交界；均来自实际TileMapLayer场景，不是背景效果图。

## 直接试铺

打开[混铺场景](../../../../scenes/ember/reference_floor_sandbox_v003.tscn)运行。这里是完整独立工程包。解压后打开根目录 `project.godot`；启动脚本也会自动导入首次资源。

- `4`／`5`／`6`／`7`：选材质并切到地板笔刷，左键新增地板或覆盖已有地板材质。
- `1`：当前材质地板；`2`：2×2宽桥；`3`：单格窄桥。
- 右键擦除；`Ctrl+Z`／`Ctrl+Y`撤销重做；`Ctrl+S`／`Ctrl+L`保存载入。
- 存档为 `user://reference_floor_v003_layout.json`。v2存档按原蓝灰钢板加载。

另有完整同构地图：[控制区](../../../../scenes/ember/reference_floor_control_sandbox_v003.tscn)、[检修区](../../../../scenes/ember/reference_floor_service_sandbox_v003.tscn)、[旧仓区](../../../../scenes/ember/reference_floor_rust_sandbox_v003.tscn)。独立工程可运行 `run_showcase.ps1 -Map control -GodotPath <Godot路径>`，`-Map`接受 `mixed/control/service/rust`。

## 编辑器铺刷与复用

`Floor`、`Bridge`仍是统一的原生47型Terrain输入。选 `FloorMaterials` 普通图块层，刷对应的四个索引块即可修改已有地板材质；该层只保存材质，不创建Floor范围，空白表示原steel。不要把多种材质作为同一Terrain的随机候选。

复制完整示例时保留 `reference_floor_v002/` 的公共结构资源、`reference_floor_v003/` 的新表面与索引资源、两个铺刷脚本 `reference_floor_compiler_v002.gd`、`reference_floor_painter_v003.gd`，以及机器人／采能站PNG。独立包已包含全部依赖。新索引资源为 [floor_materials_v003.tres](floor_materials_v003.tres)，目录为 [catalog.json](catalog.json)。

**所有输入和派生TileMapLayer仍采用128纹理格、0.25缩放，逻辑格32world。** 相机zoom为2，不额外缩放场景根节点。压顶8world、南立面32world、默认桥体40world与两侧12world肩口保持v002标准。材质只改变顶面，交界不生成内部压顶、立面或平台缝隙。

材质和占用一同参与局部脏区、撤销、存档、输入轮询与缓存签名；纯换材质也刷新显示。示例四张地图有预编译PNG缓存，新布局首次完整编译约10秒，后续普通局部刷新约1秒，具体以验收JSON为准。context层为派生缓存，不应手刷；`FloorMaterials`是可保存的输入。

## 验证与来源

结构和材质验证见 [independent_validation_v003.json](independent_validation_v003.json)，实际GPU连续换材质见 [gpu_capture_v003.json](gpu_capture_v003.json)。本轮重点是材质交界、材质纯编辑、局部／完整RGBA一致性、撤销和存档；既有v002结构验证另外保留。原生编辑器GUI撤销未通过UI实际操作验证。

本轮独立验收PASS：12个材质对交界case、四向1024像素桥截面、9次增量／完整RGBA精确比较、材质撤销／存档／场景重载均通过。原三参数编译的六层输出与冻结v002 PNG逐字节一致；三张独立地图缓存抽查270个点匹配。材质局部编译本机测量0.69～1.28秒；GPU连续两次换材质的像素探针误差均为0。

三份新纹理由内置imagegen生成，原稿、完整提示词和SHA256见 [generation_manifest_v003.json](../../../../art-source/ember/reference-floor-v003/generation_manifest_v003.json)。完整母稿nearest注册为1024×1024表面周期，未程序改色或量化材质；整理记录见 [source_processing_v003.json](source_processing_v003.json)。原蓝灰与公共构造复用v002，装饰仍独立摆放，未新增碰撞或导航。

生产脚本：[build_reference_floor_v003.gd](../../../../tools/build_reference_floor_v003.gd)。统一标准：[reference-floor-v003-materials.md](../../../../docs/shader-learning/reference-floor-v003-materials.md)。

