# Ember 七材质地板 v004 独立工程

打开 `project.godot`，默认运行七材质混铺地图。`4/5/6/7`选原蓝灰、浅灰控制区、深灰防滑、锈褐钢面，`8/9/0`选新增浅砂混凝土、青绿旧涂层、灰白地砖。`[`／`]`循环材质；左键铺刷或换表面，右键擦除；`2`宽桥、`3`窄桥；Ctrl+Z／Y撤销重做，Ctrl+S／L保存载入。

也可运行 `run_showcase.ps1 -Map concrete -GodotPath <Godot可执行文件路径>`。`-Map`接受mixed/concrete/teal/ceramic，启动脚本等待首次资源导入再运行场景，三个单材质地图启动即选中对应笔刷。已在Godot4.7.2 Compatibility下验证。

[实际地图对比](assets/ember/environment/reference_floor_v004/gpu_material_comparison_v004.png) · [使用说明](assets/ember/environment/reference_floor_v004/README.md) · [统一标准](docs/shader-learning/reference-floor-v004-materials.md)

对比图左上混凝土、右上青绿、左下地砖、右下七材质混铺，均来自实际TileMapLayer渲染。七种表面共用原v002的47型结构、桥头、压顶、立面和统一比例。地砖填缝只是表面图案。材质交界不生成内部边框。

运行 `run_validation.ps1 -GodotPath <Godot路径>` 可复验30组材质交界、12个桥口、局部／全域像素一致性、撤销与存档。原生编辑器GUI撤销仍未验证；技术通过不代表用户已经认可新增材质。新表面母稿、提示词和SHA清单见 `art-source/ember/reference-floor-v004/`；所有v002/v003依赖与旧报告也在包内。PNG经过nearest注册后按世界相位采样，没有程序改色。包不携带本机 `.godot` 导入缓存。
