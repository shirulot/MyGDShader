# Ember 多材质地板 v003 独立工程

打开 `project.godot`，运行默认混铺地图。`4/5/6/7`分别选蓝灰、浅灰、深灰、锈褐地板；左键铺刷或换表面，右键擦除；`2`宽桥、`3`窄桥；Ctrl+Z/Y撤销重做，Ctrl+S/L保存载入。

也可运行 `run_showcase.ps1 -Map control -GodotPath <Godot可执行文件路径>`。`-Map`接受mixed/control/service/rust，启动脚本先自动导入资源。已在Godot4.7.2 Compatibility下验证。

[四种实际地图对比](assets/ember/environment/reference_floor_v003/gpu_material_comparison_v003.png) · [使用说明](assets/ember/environment/reference_floor_v003/README.md) · [标准](docs/shader-learning/reference-floor-v003-materials.md)

运行 `run_validation.ps1 -GodotPath <Godot路径>` 可复验材质交界、局部编译、撤销与存档。包内保留3份新母稿及完整提示词，也保留v002共享构造、来源和原验证文件。本轮独立验证不会重写v002报告。
