# 机器人 v011 正式运行包：独立迁移增量复审

**结论：PASS_MIGRATION_ONLY。** 正式包保留已通过 C2 rc02 的全部 24 段 / 112 帧；资源迁移仅发生在已声明的路径与交付状态信息。独立冷导入和实际新入口的最小运行/GPU检查均通过。本轮没有重新开启已通过美术审查，也没有把原作者 224 GPU 全矩阵写成本轮重新执行。

## 固定输入

| 项目 | 独立核对 |
| --- | --- |
| 正式 ZIP | `robot_eight_way_v011_final_2026-10-07.zip`，1,398,383 B |
| ZIP SHA-256 | `8dc65a715b41b2c61a09eb6e2afbcd31134db60228f4b3081a0a39e4d153f4bb` |
| manifest SHA-256 | `d605101d0e668796995599a44f9cd86010220f108ef0e21adec62faf20797235` |
| 文件 | 336 载荷 + manifest =337；ZIP CRC、路径安全、唯一文件名、清单闭合、逐文件 SHA/bytes 全部通过 |
| 固定目录 | `art-source/ember/robot-eight-way-v011/delivery/robot-v011` 的 337 个交付文件与 ZIP 完全相同 |
| 已审来源 | C2 rc02 ZIP SHA-256 `64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b` |
| atlas | `0340a11ca59efdb18c64385fa24ec8faa833f0c3c6b056b5c6a97d3f3f5b4268` |

## 迁移白名单

- **112 PNG、1 atlas、192 GIF/WebP 均与固定 C2 rc02 来源逐字节相同。** 动作参数、帧内容、图集矩形及方向顺序未改变。
- 以下四项分别仅有一处明确的字符串路径替换，独立对比替换后文件 bytes 与正式包相等：

| 文件 | 来源路径 → 正式路径 |
| --- | --- |
| SpriteFrames | `godot-full-review/robot_eight_way_v011.tres` → `assets/ember/robot_v011/robot_eight_way_v011.tres`；内部 atlas 路径移至同目录 |
| 预览脚本 | `godot-full-review/preview_full_actions.gd` → `preview/preview_full_actions.gd`；内部 TRES 路径移至 `assets/ember/robot_v011/` |
| 预览场景 | `godot-full-review/preview_full_actions.tscn` → `preview/preview_full_actions.tscn`；内部脚本路径改为 `res://preview/preview_full_actions.gd` |
| 工程入口 | `godot-full-review/project.godot` → `project.godot`；main_scene 改为 `res://preview/preview_full_actions.tscn` |

- `.import` 的完整 `[params]` 部分逐字节不变，含 `process/fix_alpha_border=false`、`mipmaps/generate=false`、无预乘 Alpha。其余部分只变化 atlas 源路径及由路径派生的缓存位置；UID、压缩方式等未额外变化。
- metadata 精确只有 28 处变化：24 个 `art_status` 变为 PASS、总状态、atlas 路径、新 `release`、新 `art_acceptance` 绑定。其内嵌 TA 最终回执的 SHA 匹配，并与当前 C2 rc02 正式回执文件同字节。
- 网页对照源包只变第 9/23/36 行：总通过文案、项目链接、状态显示。帧装载、播放与画布逻辑保持原实现。根 TA 另查实际网页入口。
- `frames/.gdignore`、`previews/.gdignore`、`evidence/.gdignore` 只排除编辑器自动导入辅助文件；112 PNG 仍在包中供源像素核对。

## 独立冷导入与实际主入口

使用本目录新建 `technical-cold-runtime-r2/` 从最终 ZIP 解压，初始没有 `.godot`；不运行或修改冻结交付目录。使用 TA 自有 [运行探针](technical-runtime-probe.gd)，实际实例化工程设置中的 `res://preview/preview_full_actions.tscn`，没有用另写的替代预览场景冒充入口。

引擎为 **Godot 4.7.2 stable Steam / Compatibility / NVIDIA GeForce RTX 4070 Laptop GPU**。编辑器冷导入及实际 GPU entry 两次进程均 exit 0、stderr 0。

- 24 段 SpriteFrames 成功加载。112 个 `AtlasTexture` 的 64×96 RGBA 均与相应 PNG 完全一致，逐帧矩形、frame duration=1、FPS 与 loop 参数通过。
- 资源原生画布 **64×96**，素材脚底根锚 **(32,80)**。真实节点 `centered=false`、`offset=(-32,-80)`、Nearest；两个示例显示倍率分别 4×、1×，节点位置为 `(430,490)`、`(800,365)`，运行前后不变。这里的显示位置和倍率不是改动素材根锚或原生尺寸。
- idle 和 walk 各通过真实 `animation_looped` 事件观察一圈；walk 切向保留双方当前**帧索引**。原脚本会重启同动作再设回 frame，当前验证没有把 `frame_progress` 小数进度保留声称为通过；该逻辑与已审源脚本相同。
- 东南 collect 观察到帧 `0→1→2→3`，期间切向被锁定，恰好一次 `animation_finished`，双节点回到同向 idle F00。
- 为稳定 GPU 单帧读取，在实际到达 collect F01 后暂停一次、截图，再恢复自然完成；不将该采样写成连续录像或不间断完整动作画面检查。
- F01 实际 GPU 中，4× 对照 **22,736** 个不透明像素、1× 对照 **1,421** 个不透明像素，均 **0 差异**。已查看 [实际入口截图](technical-entry-collect.png)，两种倍率、状态和帧正确。该检查不声称全面复验所有透明背景像素或旧 224 画面的矩阵。

冷验证后原有 **336 载荷 SHA 全部保持**；原固定交付目录复核同样 0 改动。只有独立冷副本新增引擎缓存及 TA 探针。首次自有探针因 GDScript 对数组取值无法推断布尔变量类型而未运行；已在 TA 探针补明确 bool 类型，并重新从 ZIP 创建 r2 冷副本完成上述有效验证。该问题属于审查代码，交付脚本未作修订。

## 证据与边界

- [迁移逐文件结果](technical-migration.json)、[独立迁移脚本](technical-migration.py)。
- [独立冷执行回执](technical-cold-receipt.json)、[实际入口结果](technical-runtime-entry.json)、[冷执行脚本](technical-cold.py)。
- [导入输出](technical-cold-r2-import.stdout.log)、[入口输出](technical-cold-r2-entry.stdout.log)；对应 stderr 文件均为空。

正式包内 `evidence/runtime-migration-validation.json`、`runtime-import-validation.json`、`runtime-entry-validation.json` 及包外作者 `qa/cold-runtime-final-validation/receipt.json` 已绑定并与最终 ZIP 对应；其记录是作者证据。上文单独列出的冷导入/实际入口才是本轮 TA 独立重跑。原 C2 rc02 美术通过继续有效；本次通过限正式运行包迁移，不包含游戏主工程接入、采集玩法或新增动作。
