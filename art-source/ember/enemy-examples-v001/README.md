# Ember 敌人单位示例 v001

本轮提供 4 款静态造型参考，用于比较敌人的轮廓、职能与体量。沿用现有机器人的浅装甲、蓝灰机械结构、少量黄铜接头和旧工业像素风。

[查看统一比例板](enemy_examples_comparison_v001.png)。最左侧为现有正式机器人，其他单位按各自建议的主体尺寸保持宽高比缩小，再统一最近邻放大 4 倍。悬浮机额外上移显示，像素比例相同。

| 编号 | 单位 | 造型与职能参考 | 生成母稿 | 提示词 |
|---|---|---|---|---|
| 01 | 轻型巡逻兵 | 双足、单侧臂枪，普通巡逻与远程单位 | [透明母稿](enemy_patrol_master_v001.png) | [prompt](prompts/enemy_patrol.prompt.txt) |
| 02 | 近战切割工蜂 | 低伏机身、外伸圆盘与夹具，快速近战单位 | [透明母稿](enemy_cutter_master_v001.png) | [prompt](prompts/enemy_cutter.prompt.txt) |
| 03 | 履带重装机 | 宽低双履带、前置短炮，重装压制单位 | [透明母稿](enemy_tracked_heavy_master_v001.png) | [prompt](prompts/enemy_tracked_heavy.prompt.txt) |
| 04 | 悬浮侦察机 | 双侧包覆风扇与中央传感器，空中侦察单位 | [透明母稿](enemy_scout_drone_master_v001.png) | [prompt](prompts/enemy_scout_drone.prompt.txt) |

全部母稿使用内置 imagegen 分别生成，要求透明背景。参考图片为现有机器人 `robot_idle_down_v001.png`、实际矿区地图预览 `gpu_dry_mine_v001.png` 和已登记的设备素材库 `sprite_library_v001.png`。各个 `.generation.json` 保留生成工具、原始保存位置、工作区副本及参考路径。

比例板使用独立 Godot 4.7.2 预览工程渲染，直接读取上述 PNG。只按 alpha ≥ 0.1 的可见主体确定裁切范围、保持宽高比最近邻缩放与摆放，不重绘或改色；裁切范围内保留原 RGBA。母稿含少量非常浅的透明边缘，因此比例小图不能用于证明成品边缘已清理。

`*_scale_example_v001.png` 是观察缩小可读性的尺寸研究图。母稿细节密度仍高于现有机器人的原生像素图，传感窗已带静态橙红色亮点。本轮没有制作四向、动作帧、独立状态灯、碰撞、战斗逻辑或正式资源场景。

完整参数与提示词在 [source_specs_v001.json](source_specs_v001.json)，本轮渲染与缩放记录在 [preview_report_v001.json](preview_report_v001.json)。

重新生成比例板：

```powershell
& 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe' --path 'E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/enemy-examples-v001/preview-project' --rendering-method gl_compatibility --audio-driver Dummy --script res://compare.gd
```
