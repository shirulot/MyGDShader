# 机器人 v003：当前帧复查与新增动作

> 历史记录：用户指出多种动作仍有关节断裂后，v004 逐关节复查确认 v003 曾漏判部分薄轴和错位肘。本文中的关节通过判断不作为当前验收结论；最新素材与逐帧修复见 [机器人关节修复 v004](robot-joint-repair-v004.md)。旧文件保留用于对照。

日期：2026-10-06。沿用项目已认可的 64×96 原生机器人、浅装甲／蓝灰结构／黄铜工具。先复查现用的 4 张待机 v001 和 16 张行走 v002，再制作新增动作；本次没有重新生成另一套角色。

## 当前帧与地图修复

本次重新读取 20 张实际生产 PNG：二值 Alpha、透明边界、单个 8 连通主体、目录 SHA、atlas 对应区域均通过。Godot 4.7.2 透明 4 倍 GPU 读回与原 PNG 的 Alpha、可见 RGB 差异为 0。旧 walk v001 的髋部与靴边断裂属于历史文件，现用 walk v002 已修复。详见 [当前基准审查](../../art-source/ember/robot-audit-v003/README.md)。

三张新地图另有足底注册错误：原 `centered=true, offset=(0,-48)` 将画布底 y96 当作地面，而正确虚拟脚底是 `(32,80)`，导致足底位于节点上方 10.4 世界像素。本次最小修改为 `centered=false, offset=(-32,-80)`，保留现有地图中的角色尺寸与摆放点，并修正装配脚本的同一处源头。

- `tools/assemble_map_asset_previews_v001.gd`
- `scenes/ember/map_assets_tidal_port_v001.tscn`
- `scenes/ember/map_assets_dry_mine_v001.tscn`
- `scenes/ember/map_assets_overgrown_lab_v001.tscn`

独立工程重新加载上述三张地图，实际坐标变换后的足底误差均为 0，真实截图及报告保存在 `art-source/ember/robot-actions-v003/map-registration/`。此前地图 ZIP 保留为交付时快照；本次角色 ZIP 是独立动画工程。

## 新增帧与使用入口

共新增 **20 张 PNG**：四方向各 1 张待机微动、4 张采集动作。组合资源复用旧 20 张已确认 PNG，共 **40 个姿态、12 段动画**。

| 动画 | 每方向帧数 | 播放速度 | 循环 |
| --- | --- | --- | --- |
| `idle_down/left/right/up` | 2，第一帧复用原待机 | 2 FPS | 是 |
| `walk_down/left/right/up` | 4，复用修复后 v002 | 8 FPS | 是 |
| `collect_down/left/right/up` | 4，准备／下探／保持／收回 | 6 FPS | 否 |

正式文件：

- `assets/ember/characters/robot/actions_v003/`：20 张新独立 RGBA PNG。
- `assets/ember/characters/robot/robot_animations_v003.png`：640×384 图集，10 列×4 行，零间隔；按行 down、left、right、up，按列 idle 2／walk 4／collect 4。
- `assets/ember/characters/robot/robot_sprite_frames_v003.tres`：可直接指定给 `AnimatedSprite2D.sprite_frames`。
- `assets/ember/characters/robot/robot_frames_catalog_v003.json`：40 个姿态的坐标、SHA、时序与运行时窗口位置。
- `scenes/ember/robot_animation_sandbox_v003.tscn`：四向×三动作自动展示和键盘控制角色。

运行示例场景，方向键或 WASD 行走，E／空格采集，松开方向键返回待机。采集中暂时停止移动，结束后回到当前方向待机；此逻辑仅用于本次可操作预览。展示网格中的采集角色会在单次结束后停顿并显式重播，资源本身仍为非循环动作。

新动画仍采用 **64×96、脚底 `(32,80)`、Nearest**；预览放大 4 倍，避免非整数放大引起像素宽度交替。使用该资源时，设置 `centered=false, offset=Vector2(-32,-80)`；不要按各帧可见包围盒重新对齐脚底。

## 可编辑制作方式与关节审查

新动作从已审阅 idle RGBA 与 v002 修复后部件分区制作，源像素保留原色，使用整数部件位移与明确的关节像素标注。原角色头盔、工具手、调色板和支撑足保持一致；没有整图缩放／扭曲、镜像换手、自动擦除碎片、Alpha 膨胀或自动填缝。

首版左向采集曾将整条工具臂横移，像素虽然连通，肩甲位置仍不自然。因此最终动作将工具侧肩／上臂与前臂／腕工具明确分区，肩甲随躯干保持连接，前臂伸出采集；下向伸腕也保留上臂连接。关节要求同时采用连通测量与放大图人工审阅，不能仅凭“主体只有一个连通域”判定姿态自然。

可编辑来源：`art-source/ember/robot-actions-v003/poses/` 与 `source-rigs/`，由 `tools/build_robot_actions_v003.gd` 渲染；`tools/build_robot_animation_v003.gd` 组装资源并独立验证。胸部状态窗口跟随躯干部件更新坐标，未制作窗口 mask，也未把能量状态或发光烘焙进 PNG。

保留旧玩家场景、课程 Shader、旧 v001／v002 PNG 和动画示例。本次新增资源未接入 M0 战斗逻辑或完整游戏角色状态机。

## 验证与复验

最终证据保存在 `art-source/ember/robot-actions-v003/`：

- `frame_manifest_v003.json`：24 个 idle／collect 姿态记录，包含复用的 4 张 idle；新增 PNG、源部件、姿态、SHA 与原生测量。
- `runtime_build_v003.json`、`runtime_verify_v003.json`、`runtime_gpu_v003.json`：组合目录与图集、导入资源、12 段动画时序、真实播放、交互状态切换及 1／4 倍 GPU 读回。
- `map-registration/map_registration_v003.json`：三张地图足底注册。
- `protected_sources_after_v003.json`：旧生产资源及课程／玩家保留检查，单列本次授权的地图注册修正。
- `visual_review_v003.json`：逐方向新增动作与完整回环的人工审阅。
- `previews/preview_encoding_v003.json`：实际 Godot PNG 序列的无损 WebP 编码与 GIF 角色色检查，编码不改画面。

`previews/.gdignore` 仅阻止 Godot 把浏览器动画 WebP 当作单张生产纹理导入；正式 PNG／atlas 在 `assets/`，照常导入和播放。动态图用于审阅，不作为 SpriteFrames 输入。

在独立工程中运行，不需要导入主项目：

```powershell
& 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe' `
  --path '<独立工程目录>' --headless --editor --import

& 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe' `
  --path '<独立工程目录>' --headless `
  --script res://tools/build_robot_animation_v003.gd -- `
  --verify-only --report='<报告绝对路径>'
```

GPU 比较运行同一验证脚本并去掉 `--headless`，增加 `--gpu --snapshot`。独立 ZIP 自带 `project.godot`、启动与复验脚本，可直接打开新预览；打包报告绑定逐文件 SHA，并在新解压目录完成冷启动验证。
