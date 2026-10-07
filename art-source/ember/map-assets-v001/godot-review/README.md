# Ember 十三材质地板 v006 独立工程

用Godot打开 `project.godot`，默认运行十三材质混铺地图。数字键4～9和0选择原七种；F1／F2／F3选沥青、砖、木，F4／F5／F6选沙土、碎石、苔石。`[`／`]`循环材料；左键铺刷或换表面、右键擦除；2宽桥、3窄桥，Ctrl+Z／Y撤销重做、Ctrl+S／L保存载入。

启动脚本 `run_showcase.ps1 -Map sand -GodotPath <Godot可执行文件路径>` 支持mixed／sand／gravel／moss。脚本先等待导入，再运行选定地图，单材质场景默认选中对应笔刷。工程使用Godot4.7 Compatibility。

[三种新地图与十三材质混铺对比](assets/ember/environment/reference_floor_v006/gpu_material_comparison_v006.png) · [使用说明](assets/ember/environment/reference_floor_v006/README.md) · [标准](docs/shader-learning/reference-floor-v006-materials.md)

对比图左上沙土、右上碎石、左下苔石、右下十三材质混铺，全部来自实际TileMapLayer渲染。共用47型结构、桥口、压顶与32world格；碎石与苔斑只是平面底色。运行 `run_validation.ps1 -GodotPath <Godot路径>` 可复验交界、铺刷、运行时撤销、存档、快捷键和负原点地图；原生编辑器GUI撤销未验证。

三份内置imagegen母稿、完整提示词与SHA清单位于 `art-source/ember/reference-floor-v006/`。包内保留v002～v005依赖；Godot只nearest注册与遮罩拼装，不程序改色。ZIP不携带本机 `.godot` 导入缓存。
