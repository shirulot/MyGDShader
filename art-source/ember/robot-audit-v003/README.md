# 机器人当前版本只读审查（2026-10-06）

本次重新读取正式目录中的原始 PNG，不依赖旧报告的通过状态。结论是：**当前采用的 4 张 idle v001 和 16 张 walk v002 没有确诊的主体碎片、肢体断裂或边界裁切，可作为增加动作的造型基准。三张地图另有足底锚点注册错误，应该在场景集成时修正。**

## 当前版本与旧版本

三张 `scenes/ember/map_assets_*_v001.tscn` 目前只放置 `robot_idle_down_v001.png`。`robot_animation_sandbox_v002.tscn` 使用 `robot_sprite_frames_v002.tres`，后者引用 `robot_animations_v002.png`；其四张待机帧沿用 v001，行走帧全部采用修复后的 v002。

旧 `robot_animation_sandbox.tscn` 仍引用 v001 动画资源，是保留的历史示例。旧 walk v001 的下列缺陷在本次原图读取中再次确认，**不能将旧版行走图重新拼入新动作资源**：

| 文件 | 原生坐标（左上 0,0） | 确认问题 | 当前使用影响 |
| --- | --- | --- | --- |
| `assets/ember/characters/robot/robot_walk_down_f01_v001.png` | `(32,62)` | 1 像素髋部碎片 | 新地图及 v002 动画均不消费该帧 |
| `assets/ember/characters/robot/robot_walk_down_f03_v001.png` | `(30,62)`、`(31,62)` | 2 像素髋部碎片 | 同上 |
| `assets/ember/characters/robot/robot_walk_left_f02_v001.png` | `x27..29 / y73..78`；精确 14 点见 JSON | 14 像素靴边脱落 | 同上 |

对应 v002 的三帧均只有一个 8 连通主体，旧碎片已经并回正确的髋/腿/靴轮廓。

## 当前帧实测与视觉审阅

`alpha_audit_v003.json` 记录当前及旧版共 40 个目录帧案例（其中 4 张待机共用，实际是 36 张独立帧 PNG）、两张 atlas 的原始 SHA、画布、Alpha、包围盒、连通域、16 个完整循环转换以及三张场景引用。

- 当前 20 帧都是 64×96 画布，足底锚点统一为 `(32,80)`。
- 当前 20 帧各有且仅有一个 8 连通主体；8 连通允许对角像素相连，避免像素轮廓误报。
- 所有当前帧 Alpha 为 0/255，画布四边透明，无越界或贴边裁切；主体包围盒宽 26..40、高 58..60 像素。
- 20 个独立 PNG 的 SHA 与当前目录吻合，20 个 atlas 区域 RGBA 与独立 PNG 逐字节一致。
- Godot 4.7.2 的真实 OpenGL 透明 4× 读回与原始 PNG 比较：Alpha 差异 **0**，可见 RGB 差异 **0**。
- 只读过程结束后源图、目录、图集、已观察场景的 SHA 保持不变。

已经查看原图 atlas、现有全部 20 帧 4× 板、本次真实 GPU 4× 板、down/right 修复前后图，以及 left/up 完整行走回环。肩部、髋部、膝部、手腕、工具与靴轮廓没有新的明显断裂，头盔与胸甲特征保持一致。现有动作只是小幅摆臂、腿部错位与 1 像素上下起伏，不据此声称新增了大步幅运动。

`left f03`、`right f01` 的可见底界是 y78，其余帧 y80；这是保留固定虚拟地面原点后的抬脚/近远投影，不能通过每帧底部自动贴齐来消除，否则会引入整身跳动。腋下、腿间、工具附近的合法负空间仍然保留；连通域通过并不能证明每一处负空间都漂亮，因此关节结论同时采用人工图像审阅。

本次审查图为真实 GPU 渲染，不是新的美术母稿：

- `current_v002_gpu_transparent_4x.png`：透明底，按行 down / left / right / up，按列 idle / walk f00 / f01 / f02 / f03。
- `current_v002_gpu_checker_4x.png`：同一绘制结果加棋盘背景，便于辨认透明缝。
- `down_equivalent_map_scale_1p3x.png`：地图 scale=0.65、Camera zoom=2 的最终等效倍率；Nearest 非整数倍率会有像素宽度交替，原图没有因此断裂。

## 当前三张地图的足底问题

三张正式场景的 `Props/ExistingRobot` 都是默认 `centered=true`、`offset=(0,-48)`、`scale=(0.65,0.65)`。原始画布下脚底 `(32,80)` 相对于节点落在 `(0,-16)`，缩放后是节点上方 **10.4 世界像素**，Camera zoom=2 时为 **20.8 显示像素**。这使节点位置和真实脚底不一致，影响后续对齐、运动及替换动画资源；本次只读阶段没有修改这些场景。

| 场景 | 节点声明位置 | 建议统一的注册方式 |
| --- | --- | --- |
| `scenes/ember/map_assets_tidal_port_v001.tscn` | 第 191 行 `ExistingRobot` | `centered=false`、`offset=(-32,-80)` |
| `scenes/ember/map_assets_dry_mine_v001.tscn` | 第 229 行 `ExistingRobot` | 同上 |
| `scenes/ember/map_assets_overgrown_lab_v001.tscn` | 第 234 行 `ExistingRobot` | 同上 |

如保留默认居中模式，正确 offset 应为 `(0,-32)`。上述行号与本次报告所绑定的场景 SHA 相对应，后续新版本可能调整行号。

## 重跑

`tools/audit_robot_alpha_v003.gd` 可复制到独立 Godot 工程运行，使用 `--workspace=<本项目绝对路径>` 和 `--output=<审查目录绝对路径>`。需要真实 GPU 截图时不能使用 `--headless`；只要运行脚本就只读取原始资源，所有报告与预览写入指定输出目录。审查工程位于本目录的 `godot-review`，未并行导入主项目，未改写任何旧素材或运行脚本。
