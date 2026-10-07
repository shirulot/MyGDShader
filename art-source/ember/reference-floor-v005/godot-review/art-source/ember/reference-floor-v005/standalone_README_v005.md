# Ember 十材质地板 v005 独立工程

打开 `project.godot`，默认运行十材质混铺地图。数字键4～9和0选择原七种地板；F1／F2／F3选择旧沥青、砖红铺装、灰褐木栈道。`[`／`]`循环材质，左键铺刷或换表面、右键擦除；2宽桥、3窄桥，Ctrl+Z／Y撤销重做、Ctrl+S／L保存载入。

也可运行 `run_showcase.ps1 -Map asphalt -GodotPath <Godot可执行文件路径>`，Map接受mixed／asphalt／brick／wood。启动脚本先等待资源导入，再运行场景。单材质地图自动选中对应地板。工程使用Godot4.7 Compatibility。

[三种新地图与十材质混铺对比](assets/ember/environment/reference_floor_v005/gpu_material_comparison_v005.png) · [使用说明](assets/ember/environment/reference_floor_v005/README.md) · [统一标准](docs/shader-learning/reference-floor-v005-materials.md)

对比图左上沥青、右上砖红、左下木栈道、右下十材质混铺，均为实际TileMapLayer渲染。十种表面共用原47型结构、桥口、压顶和比例。砖缝／木板接缝只属于平面表面图案。运行 `run_validation.ps1 -GodotPath <Godot路径>` 可复验交界、运行时撤销、存档、原生材料输入与偏移地图重建。原生编辑器GUI撤销仍未验证。

源码与完整提示词见 `art-source/ember/reference-floor-v005/`，包内含v002／v003／v004依赖。内置imagegen生成艺术母稿，Godot只nearest注册与遮罩拼装，不程序改色。ZIP不携带本机 `.godot` 导入缓存。
