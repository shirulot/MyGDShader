# Ember 建筑资源 v002

用 Godot 4.7.2 Compatibility 打开包根目录 `project.godot`，运行三栋建筑交互演示。所有依赖都是实体文件；无需原工作区或 junction。

## 直接使用

主资源为控制塔、维修工坊、物流仓库三栋完整建筑：

- `assets/ember/building_assets_v002/buildings/<建筑ID>/complete_closed.png`：干净透明整栋闭合图。
- 同目录 `fixed_shell.png`：合并的固定主体。
- `scenes/ember/building_assets_v002/<建筑ID>_static.tscn`：单张完整图的静态预制体。
- `scenes/ember/building_assets_v002/<建筑ID>.tscn`：含门、设备、碰撞与遮挡的可交互预制体。

建筑ID为 `control_tower`、`repair_workshop`、`logistics_warehouse`。同栋的整图和功能层共用 canvas/pivot，按原生比例放置。交互预制体加载必要的功能合层，不再逐柱梁组装。`fixed_shell.png`用于固定主体复用；不能与已包含相同像素的静态功能层叠加显示。具体尺寸、接口与分层理由见资产、场景目录 README 及 `docs/shader-learning/building-assets-production-v002.md`。

运行 `demo.tscn`：WASD/方向键移动；E人门、G货门、C检修盖、F设备、R维修、P供电、L锁门、X故障、I窗后明暗。H/J检查遮挡与屋顶检修资源；F5/F9保存和载入。门完全打开才允许通行，关门遇到角色会重新打开，断电冻结门片。读档先恢复角色位置与真实占用，再恢复建筑，避免读档前的门口占用干扰存档。

`evidence_player.tscn`可暂停查看18张实际GPU动作帧；播放器的0.5秒换帧间隔是查看间隔，门机械行程仍为0.8秒。预览目录另含整栋、检修、灯态、前后遮挡证据。

## 来源与范围

v001目录保留47个原拆件、28个接受母稿、2个明确拒收母稿和30份提示词，仅作辅助来源和复算基线。v002通过整数坐标同源合成保持已审外观，没有重新生成造型。v001基础脚本为继承依赖，v002演示入口使用已修复的读档实现。主资源不是拆件目录。

当前交付为三栋南向固定建筑，包含交互与遮挡演示；完整室内、屋顶通行、其他朝向和建筑自动笔刷不在本包范围。地板沿用已接受的项目资源。制作方验收通过与外部TA最终审核分别记录。

## 复验

首次先运行 `godot --headless --editor --path . --quit`，再执行：

```text
godot --path . --script res://tools/validate_building_composition_v002.gd
godot --headless --path . --script res://tools/validate_building_interactions_v002.gd
godot --headless --path . --script res://tools/validate_building_ta_regression_v002.gd
godot --headless --path . --script res://tools/validate_building_save_matrix_v002.gd
```

第一项必须使用实际GPU，校验同源像素、整栋PNG、静态及交互预制体、新旧24种建筑状态。重拍预览用 `tools/capture_building_assets_v002.gd`。包内逐文件SHA清单为 `portable_file_manifest_v002.json`；ZIP总SHA和独立打包复验报告放在ZIP外的v002来源目录，避免循环引用。
