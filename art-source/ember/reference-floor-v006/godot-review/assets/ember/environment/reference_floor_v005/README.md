# 地板扩展 v005：道路、厂区与木栈道

新增三份内置imagegen母稿：旧沥青、砖红工业铺装、灰褐木栈道。原七种表面及ID不变，现在共十种可混铺地板。本轮新增美术为视觉候选。

| ID | 快捷键 | 材质 | 适用区域 |
| --- | --- | --- | --- |
| 0 | 4 | 蓝灰涂装钢板 | 普通平台与通道 |
| 1 | 5 | 浅灰控制区地板 | 清洁操作区 |
| 2 | 6 | 深灰防滑钢板 | 设备检修区 |
| 3 | 7 | 锈褐旧仓区钢板 | 旧仓库与港区 |
| 4 | 8 | 浅砂混凝土 | 装卸作业平台 |
| 5 | 9 | 青绿旧涂层 | 泵房与工艺处理区 |
| 6 | 0 | 灰白旧地砖 | 实验室与铺砖操作区 |
| 7 | F1 | 旧沥青 | 道路与室外装卸区 |
| 8 | F2 | 砖红工业铺装 | 旧厂区与工作院落 |
| 9 | F3 | 灰褐木栈道 | 木制码头与临水作业区 |

## 实际试铺

打开[十材质混铺地图](../../../../scenes/ember/reference_floor_sandbox_v005.tscn)。这里是完整独立工程包。解压后用Godot打开根目录 `project.godot`，运行即可铺刷。

`1`当前地板、`2`宽桥、`3`窄桥；数字键与F1～F3选材质并回到地板笔刷，`[`／`]`循环所有材质。左键铺刷／换表面，右键擦除。Ctrl+Z／Y撤销重做，Ctrl+S／L保存载入。每个单材质地图启动即选中自身笔刷。

独立场景：[旧沥青](../../../../scenes/ember/reference_floor_asphalt_sandbox_v005.tscn)、[砖红铺装](../../../../scenes/ember/reference_floor_brick_sandbox_v005.tscn)、[灰褐木栈道](../../../../scenes/ember/reference_floor_wood_sandbox_v005.tscn)。包内启动脚本 `run_showcase.ps1 -Map asphalt`，参数接受mixed／asphalt／brick／wood，可指定 `-GodotPath`。

[实际GPU对比](gpu_material_comparison_v005.png)：左上旧沥青、右上砖红、左下木栈道、右下十材质混铺。该图直接组合真实TileMapLayer截图。[完整混铺图](gpu_mixed_scene_v005.png) 展示十种表面的实际衔接。

## 不变的铺刷标准

128texture格／32world格、TileMapLayer.scale=0.25、相机zoom=2。压顶8world、南向立面32world、二格桥体40world、接岸两侧各12world肩口。Floor／Bridge共同47型拓扑负责占用与收边，所有表面都共用桥头、立面与外压顶。

沥青用细骨料区分钢板；砖红铺装使用齐平的错缝小砖；木栈道使用低彩度水平木板与细接缝。砖缝／木板接缝都是表面图案，不是结构孔洞、内部压顶或碰撞边。世界纹理相位固定，混铺只改变地面材质。

`FloorMaterials`是普通材质索引输入层，source0、coord(id,0)。编辑器先铺Floor，再铺对应材质索引；空白默认为0钢面。材料ID由 [catalog.json](catalog.json) 读取，不进入Terrain随机候选。新三种无需新增三套拓扑。

v005读取旧v2／v3／v4存档，原ID0～6保留；旧读取器不会保留它尚未注册的新ID。快照仍为version3结构，默认文件 `user://reference_floor_v005_layout.json`。同尺寸偏移地图保留v004的CPU缓存原点与派生TileMap格坐标修复。

## 来源与复用

源稿、完整提示词、来源SHA及参考图见 [generation_manifest_v005.json](../../../../art-source/ember/reference-floor-v005/generation_manifest_v005.json)。通过内置imagegen逐素材生成，Godot nearest注册为1024×1024周期，按世界相位与共享几何遮罩拼装，不程序重绘或改色。母稿的实际砖列／木板条数没有完全遵循提示词，因此按真实接缝测量裁艺术片：60块砖注册为128×64的8列×16行错缝周期；15条木板注册为16条64px板带。跨周期半砖从同一艺术片循环闭合，避免砖缝错位。每片裁切、放置和RGBA来源见 [source_processing_v005.json](source_processing_v005.json)。

复用时保留v002公共构造、v003／v004旧表面和v005新表面，使用共享 `reference_floor_compiler_v002.gd` 与本轮 `reference_floor_painter_v005.gd`。独立包含全部依赖、角色和设备。装饰、碰撞、导航与课程Shader维持原用途。

48组横纵材质交界、12个四向桥口／3072断面像素、12次增量／完整RGBA对照、运行时撤销重做、JSON／场景重载、原生材质刷与旧v004六种非零ID存档均通过。真实键盘事件验证F1→7、F2→8、F3→9、`]`→0。负原点平移／恢复与504个context世界格映射通过，七份旧表面RGBA相同；旧143份生产资源和代码与v004交付SHA相同。

技术验收见 [independent_validation_v005.json](independent_validation_v005.json) 与 [gpu_capture_v005.json](gpu_capture_v005.json)。四场景实际GPU截图与三次换材质通过，最大RGB样点误差0。原生编辑器GUI撤销与实际篡改PNG后的缓存回退分支不在本轮自动测试范围。本机完整编译14.2秒、局部材质刷新约0.7～1.2秒，缓存地图启动直接读取成品图层。

[统一标准](../../../../docs/shader-learning/reference-floor-v005-materials.md) · [生产脚本](../../../../tools/build_reference_floor_v005.gd)

