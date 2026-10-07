# 地板扩展 v006：沙土、碎石与苔石

新增三份内置imagegen母稿：压实沙土、灰色碎石、苔石地坪，供干燥作业区、矿区和废弃区域使用。原十种材质与ID0～9保留，现在共十三种可混铺表面。新增美术为视觉候选。

| ID | 快捷键 | 材质 |
| --- | --- | --- |
| 0 | 4 | 蓝灰涂装钢板 |
| 1 | 5 | 浅灰控制区地板 |
| 2 | 6 | 深灰防滑钢板 |
| 3 | 7 | 锈褐旧仓区钢板 |
| 4 | 8 | 浅砂混凝土 |
| 5 | 9 | 青绿旧涂层 |
| 6 | 0 | 灰白旧地砖 |
| 7 | F1 | 旧沥青 |
| 8 | F2 | 砖红工业铺装 |
| 9 | F3 | 灰褐木栈道 |
| 10 | F4 | 压实沙土 |
| 11 | F5 | 灰色碎石 |
| 12 | F6 | 苔石地坪 |

## 运行与铺刷

打开[十三材质混铺地图](../../../../scenes/ember/reference_floor_sandbox_v006.tscn)。这里是完整独立工程包。解压后用Godot打开根目录 `project.godot`，运行即可试铺。

数字键4～9及0选择原七种；F1～F3保留沥青／砖／木，F4～F6选择新增沙土／碎石／苔石。`[`／`]`循环全部材质；`1`当前地板、`2`宽桥、`3`窄桥。左键铺刷或换材质，右键擦除；Ctrl+Z／Y撤销重做、Ctrl+S／L保存载入。独立材质地图启动会选中对应笔刷。

单材质地图：[沙土](../../../../scenes/ember/reference_floor_sand_sandbox_v006.tscn)、[碎石](../../../../scenes/ember/reference_floor_gravel_sandbox_v006.tscn)、[苔石](../../../../scenes/ember/reference_floor_moss_sandbox_v006.tscn)。包内 `run_showcase.ps1 -Map sand` 支持mixed／sand／gravel／moss，可通过 `-GodotPath` 指定Godot。

[实际GPU对比](gpu_material_comparison_v006.png)：左上沙土、右上碎石、左下苔石、右下十三材质混铺。[完整混铺图](gpu_mixed_scene_v006.png) 展示同一占用与收边上的十三种表面。对比由实际TileMapLayer截图组合。

## 固定标准

128texture格／32world格，TileMapLayer.scale=0.25、示例相机zoom=2。压顶8world、南向立面32world、二格桥体40world、接岸两侧各12world肩口，Floor／Bridge各47型共同拓扑。所有表面共用外压顶、立面、桥头、边梁与coverage，材质交界不生成内部边框。

沙土用低彩度赭黄细砂与磨痕区别于混凝土；碎石用小灰色矿物颗粒区别于沥青；苔石用灰石与稀疏灰绿苔斑区别于青绿涂层。它们都是平面的地板底色：碎石与苔斑不新增凸起、草丛、孔洞、碰撞或导航边界。

`FloorMaterials`普通索引层保存材质：source0、coord(id,0)，不参与Terrain随机选择。编辑器先刷Floor占用，再刷对应材质索引；空白默认为0钢面。合法ID、索引宽度、循环与独立地图默认笔刷由 [catalog.json](catalog.json) 驱动。

v006读取旧v2～v5存档，原ID0～9保持；旧读取器会舍弃未注册的新材质。快照继续使用version3三元组格式，默认文件 `user://reference_floor_v006_layout.json`。保留v004的缓存／显示原点修复，偏移地图会重建正确的世界纹理相位和派生格坐标。

## 来源与验证

源稿、完整提示词和来源SHA见 [generation_manifest_v006.json](../../../../art-source/ember/reference-floor-v006/generation_manifest_v006.json)。三份母稿由内置imagegen独立生成，Godot整图nearest注册为1024×1024周期，再按世界相位与共享遮罩拼装；不程序重绘、改色或量化。处理见 [source_processing_v006.json](source_processing_v006.json)。旧砖／木周期直接复用v005校准成品。

复用时保留v002公共构造、v003～v005旧表面与v006新表面，使用共享 `reference_floor_compiler_v002.gd` 和本轮 `reference_floor_painter_v006.gd`。独立包包含全部依赖、机器人和设备；装饰、碰撞、导航与课程Shader维持原用途。

验收见 [independent_validation_v006.json](independent_validation_v006.json) 和 [gpu_capture_v006.json](gpu_capture_v006.json)，两份报告均PASS、失败项为0。33对材质的横纵66组交界、12个桥口的3072个截面像素、270个单材质缓存样点、十份旧材质RGBA、12次局部与全域六层RGBA比较、504个世界坐标映射全部通过。实际输入事件验证了F1及F4～F6、12→0循环；四次运行时撤销／重做、JSON与场景存档、旧ID1～9恢复、原生索引采用和负原点平移还原均通过。

四张地图来自实际GPU渲染；三次纯材质换刷的GPU与CPU采样误差均为0。此机独立测试的局部材质重建697～1061ms，GPU换刷重建1234～1239ms，原生输入采用1100ms；连续拖刷在释放时提交，缓存地图启动直接读取成品图层。原生编辑器GUI撤销和实际篡改PNG后的缓存回退分支不在本轮自动测试范围。

[统一标准](../../../../docs/shader-learning/reference-floor-v006-materials.md) · [生产脚本](../../../../tools/build_reference_floor_v006.gd)

