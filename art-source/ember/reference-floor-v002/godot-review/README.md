# Ember reference floor v002 独立工程

打开本目录 `project.godot`，默认运行实际 TileMapLayer 铺刷场景；或运行 `run_showcase.ps1 -GodotPath <Godot可执行文件路径>`。启动脚本会先自动完成首次资源导入。资源说明：[地板 README](assets/ember/environment/reference_floor_v002/README.md)。

`1`地板，`2`二格桥，`3`单格桥；左键铺、右键擦；Ctrl+Z/Y撤销重做，Ctrl+S/L保存／加载布局。首次新增／修改布局的派生缓存由补全器生成，不依赖原主项目或原 `.godot` 缓存。

验证：`./run_validation.ps1 -GodotPath <Godot 4.7 executable>`。若本机Godot在项目原路径，默认参数可直接使用。脚本先导入再运行独立验证，结果与实拼诊断图在 `assets/ember/environment/reference_floor_v002/`。

此工程保留原母稿、提示词、规范、切片生成器与验证脚本。仅改变新示例，不推进课程或替换主游戏；最终视觉仍由用户评判。
