# 机器人 v008 独立固定包与导入审查

结论：**显示/正常播放技术有条件通过；全 RGBA 冷导入证据需一项 P2 修订。** 这不是人物形变或可见颜色问题，不要求重画八帧。美术结论由主审与视觉审查另行决定。

范围仅 `walk_down` 八帧、64×96、8 FPS、固定 root `(32,80)`；未验其他方向、动作或主玩法速度同步。使用独立解包工程、Godot 4.7.2 Steam 与 RTX 4070 Laptop GPU，未操作用户已有编辑器，未改生产资源/提交 ZIP。

固定 ZIP SHA256：`ac74a58d6ac1751556751046571d5d983a9dcc4f9f85a146b4494706b055ff1b`（144 文件，642215 bytes）。固定 rig SHA256：`e11638a6751cdaab475224cea772aa80425066daadcfab6e71436f84fd1341a4`。

## 通过证据

- `package-source-report.json`：319 项全部通过。逐项比对 144 个 ZIP 文件与生产提交目录；帧/rig/播放报告源 SHA 绑定有效；八张 PNG 均为 64×96、二值 Alpha，与 512×96 atlas 对应整格 RGBA 完全相同；八份 pose 帧序/root/rig 绑定正确。
- 23 个中性源层不重叠，原坐标重组 1492 原始实体像素及完整 RGBA 与冻结母稿相等；37 个层归属变化与账本及冻结 v007 masks 一致，未改这些原像素 RGBA；rig 中 17 套隐藏结构/袖套定义由同一源定义复用。旧归属复核依赖工作区 `robot-fixed-rig-v007/source/part_masks_v007.json`，其 SHA 与 v008 ledger 冻结引用一致。
- 原包冷导入成功退出 0。实际 GPU 读取八帧 × 1×/4× 共 16 项逐像素 PASS，可见实体与 Alpha 无变化；自然 `AnimatedSprite2D` 信号在 2.2 秒内顺序 `0…7,0…7,0,1`，两次循环。首次事件 97ms，后续间隔均 125ms；未用 `stop()` 重置帧伪造末首事件。
- 87 个生产保护文件与既有冻结 baseline 相同，审查完成再核仍无改变。

## P2：固定 ZIP 缺导入参数，声明的全 RGBA 忠实不能冷复现

位置：提交 ZIP 缺少 `godot-review/assets/robot_walk_down_atlas_v008.png.import`；工作区该配置第 34 行是 `process/fix_alpha_border=false`。包内 `godot-review/verify_fixed_rig_playback_v008.gd:45` 使用全 RGBA 字节比较，而固定包不携带影响该比较的配置。

重现：从固定 ZIP 全新解包，运行独立工程 `--headless --editor --import`，随后在实际 GPU 模式运行 `--script res://verify_fixed_rig_playback_v008.gd -- --workspace=<独立解包根>`。Godot 自动生成 `process/fix_alpha_border=true`，原验证脚本退出 1，八个 imported region 均 `rgba_exact=false`。未覆盖原提交：失败 JSON 和 stderr 在本审查目录保留。

独立读取实际导入 atlas 定位到八帧分别 1099/1083/1078/1087/1094/1085/1083/1089 个 **Alpha=0 的隐藏 RGB** 变化，总计 8698。实体 RGBA 改变 0、Alpha 改变 0。示例 F00 `(23,18)` 从 `[0,0,0,0]` 到 `[16,24,32,0]`。这是默认透明边缘处理与验证契约的冲突，不是视觉错误；16 个完整 GPU 捕获已证实显示仍与源 PNG 一致。

隔离因果对照：从同一 ZIP 再建干净 `import-control-workspace`，仅补回生产工作区的上述 `.import` 配置，再冷导入和运行未改动的原验证脚本，退出 0，8 个 imported region 全 RGBA PASS、16 GPU PASS、自然两次循环，stderr 空。原帧、atlas、rig、pose、SpriteFrames 与验证脚本未改。

建议最小修订：交付必要的可携带纹理导入设置，或提供确定性生成配置步骤；若不要求隐藏 RGB 字节保真，也可明确把比较契约改为可见 RGBA 与 Alpha 并相应修正声明。按最终声明重新冷运行，登记新证据/ZIP SHA。当前全 RGBA PASS 声明不可直接沿用。

## 证据边界

1492 原 RGBA 完全复用只适用于 **中性源层原坐标静态重组**。由 rig 投影和一次作者定义的套嵌形成的 fixed canonical 有 1463 个不透明像素，与原母稿有 805 个坐标 RGBA 不同，不能称为母稿逐像素相同；已在候选方法中声明。工具 F01 两个逆 UV Unknown 已声明。本审查不把 IK、owner、哈希、单个连通域或编码 PASS 当作身份/步态/末首视觉 PASS。

## 直接证据文件

- `technical-summary.json`：总体范围、冻结哈希、通过/失败数量、生产保护再核。
- `package-source-report.json` 与 `verify_package_source.py`：独立包/源层/Alpha/atlas/ledger 检查。
- `cold-playback-report.json` 与 `playback-rerun.stderr.log`：原固定包冷运行失败原证据；其中 16 GPU 与自然播放通过。
- `cold-import-diagnosis.json`、`cold-imported-atlas.png`：独立实际导入像素定位；代码在 `cold-workspace/art-source/ember/robot-fixed-rig-v008/godot-review/ta_import_inspect.gd`。
- `control-playback-report.json` 与 `control-playback.stderr.log`：仅补参数后原验证脚本 PASS；控制准备代码 `prepare_import_control.py`。
- 捕获图分别位于两个独立 workspace 中 `art-source/ember/robot-fixed-rig-v008/gpu-playback/`；所有创建/更新都在 TA technical 目录内。
