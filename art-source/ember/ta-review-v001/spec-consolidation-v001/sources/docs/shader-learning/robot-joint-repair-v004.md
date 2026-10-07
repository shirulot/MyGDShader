# 机器人关节修复 v004

本版针对现用 40 个姿态复查并修补关节，保留其中 27 帧原 PNG 的路径和 SHA。11 帧修复肩、髋或工具肘的薄连接，另 2 帧改善已有实心接头的明暗可读性；总计修改 13 帧，每帧仅改 2–9 个原生像素。没有增加动作或更换角色。

此前 v003 的“全身单个 8 连通主体”只能说明像素总体连接，不能证明每个肩、肘、髋都自然承接。GPU 读回相同也只说明渲染忠实，不能代替美术审查。本版逐张看实际 PNG，并分别核对关节位置、部件遮挡及动作连续播放。

## 使用入口

- `assets/ember/characters/robot/robot_sprite_frames_v004.tres`：最新完整 SpriteFrames。
- `assets/ember/characters/robot/robot_frames_catalog_v004.json`：完整 40 帧路径、SHA、原帧来源、改动标记和动画顺序。
- `scenes/ember/robot_animation_sandbox_v004.tscn`：Godot 四方向 × 待机／行走／采集的可操作审阅场景。
- `art-source/ember/deliveries/robot_joint_repair_v004_2026-10-06.zip`：独立素材审阅工程；解压后双击 `Start.cmd`。
- `art-source/ember/robot-joint-repair-v004/previews/robot_actions_loop_v004.gif`：实际 Godot 播放板的动画预览。

新目录 `repairs_v004/` 只有被修改的 13 张 PNG；完整动作资源还引用保留的 27 张旧 PNG，因此应使用完整目录或 ZIP。原 40 张 PNG 都保留，能够逐项对照、回退。

## 逐帧修复范围

| 动作与朝向 | 帧 | 修改 |
| --- | --- | --- |
| 行走 down | f01、f03 | 单像素髋轴改为三像素暗钢接头 |
| 行走 up | f01、f03 | 同上，保留腿摆幅和两腿间负空间 |
| 行走 right | f01 | 远侧骨盆至大腿的薄接头 |
| 行走 right | f02 | 拓宽近侧肩轴，保留下方腋下负空间 |
| 行走 up | f02 | 闭合肩轴内部两个像素的穿孔 |
| 采集 left | f01、f02 | 补上臂至侧移前臂的折向肘套 |
| 采集 right | f01、f02 | 补远侧工具肘，保留胸甲遮挡与工具所在侧 |
| 采集 down | f01、f02 | 原接头没有透明断缝；只提亮实心接头中段 |

全部 8 帧待机、全部 4 帧向上采集、right 行走 f03 的已有完整髋带，以及其他没有真实断缝的姿态均保留。肩甲、靴边的正常遮挡或轮廓角点没有自动删掉。

原生画布仍为 **64×96**，虚拟脚底 **(32,80)**，静态调色板仍为原 11 色。主体包围盒、头部源遮罩、脚部、胸部状态窗、工具位置均受保护。动作顺序保持：各方向 idle 2 帧／2 FPS 循环，walk 4 帧／8 FPS 循环，collect 4 帧／6 FPS 单次。

`AnimatedSprite2D` 使用 Nearest，并设置 `centered=false`、`offset=Vector2(-32,-80)`。审阅场景采用整数放大。WASD 或方向键行走，E／空格采集；采集结束回到当前方向待机。

## 可编辑来源与验证

`joint_overlay_plan_v004.json` 明确列出每个关节的原生像素坐标、颜色、ROI 和修复理由。`tools/repair_robot_joints_v004.gd` 只执行这些人工补点，原 PNG 永不覆盖；没有整张重生、部件位移、自动膨胀、删点或调色板替换。

证据位于 `art-source/ember/robot-joint-repair-v004/`：

- `joint_repair_v004.json`：每帧原／新 SHA、实际 RGBA 差异坐标和数量、关节补点、保护区域检查。
- `frame_manifest_v004.json`：完整 40 帧清单，保留帧仍使用同一原文件。
- `native-review/*_comparison_8x.png`：左侧修复前、右侧修复后；原生像素整数放大。
- `audit/independent/postrepair_visual_findings_v004.md`：独立逐帧视觉复核。
- `runtime_build_v004.json`、`runtime_verify_v004.json`、`runtime_gpu_v004.json`：图集装配、真实动作播放和 40 帧在 1×／4× 下的 GPU 读回。
- `visual_review_v004.json`：逐帧及连续播放审阅，绑定实际 manifest、catalog、SpriteFrames 和 atlas SHA。
- `previews/preview_encoding_v004.json`：实际播放板 PNG 的无损 WebP 编码与 GIF 原色检查。
- `protected_sources_after_v004.json`：原 40 张角色 PNG、旧资源、M0 和主工程设置的保留核查。
- `package_validation_v004.json`、`package_cold_start_validation_v004.json`：逐文件 ZIP SHA 与无缓存冷导入、场景启动、运行验证。

`previews/.gdignore` 使动画媒体仅供文档预览，生产纹理仍从 `assets/` 正常导入。本版修改独立角色素材与审阅场景；主项目玩家、课程和地图继续保留现状。

重建关节 PNG 时，在独立辅助工程运行：

```powershell
# 使用 --workspace 读取主项目中的可编辑源，输出新的 v004 文件。
& 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe' --headless --path '<独立辅助工程>' --script '<本项目>/tools/repair_robot_joints_v004.gd' -- --workspace='<本项目绝对路径>'
```

ZIP 内 `run_validation.ps1` 可复验完整资源，不需要导入主工程。

