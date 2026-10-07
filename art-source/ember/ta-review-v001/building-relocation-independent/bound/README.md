# 最终建筑资源包

控制塔、维修工坊、物流仓库的最终资源、交互预制体、可运行示例和制作来源集中在此目录。采用已通过技术美术审核的 v004r1 图片；完整屋顶、墙体与转角保持原图连接，移动只更新资源路径。

## 从这里开始

| 用途 | 入口 |
| --- | --- |
| 看实际效果 | [闭合全貌](textures/previews/gpu_intact_closed_v004r1.png)、[开门](textures/previews/gpu_intact_open_v004r1.png)、[交互界面](textures/previews/gpu_demo_ui_v004r1.png) |
| 运行独立示例 | 用 Godot 打开 [examples/standalone/project.godot](examples/standalone/project.godot)，按 F5 运行，视口 1408×800 |
| 放入当前项目 | [scenes/](scenes/)：3 个交互预制体、3 个静态预制体和 1 个示例场景 |
| 使用图片 | [textures/](textures/)：3 张完整图、15 张功能图、3 张覆盖图；另有 11 张原审核预览 |
| 后续制作 | [建筑样式与交互规范](docs/ember-building-standard-v002.md) |

交互预制体为 [control_tower.tscn](scenes/control_tower.tscn)、[repair_workshop.tscn](scenes/repair_workshop.tscn)、[logistics_warehouse.tscn](scenes/logistics_warehouse.tscn)；同名 `_static.tscn` 为静态版本。完整图与功能层共享登记坐标，勿重新缩放单独的屋顶、墙面或门框。

## 交互与示例操作

WASD／方向键移动；靠近门或控制点后，E 开关人门、G 开关货门、C 开关检修盖、F 设备启停、R 维修、P 供电、L 人门锁、X 故障；I 切换已登记的前窗亮暗；F5／F9 保存与恢复。H 整壳遮挡、J 塔顶盖为检视操作。

门有开关、锁定、断电暂停、防夹重开及对应碰撞；灯面跟随状态变化。进入建筑后整壳即时切换到 Alpha 0.14。开门显示深暗洞口，当前范围不含完整室内、分楼层遮挡、风机旋转或环境动态照明；具体边界以规范为准。

## 文件分工

| 目录 | 内容 |
| --- | --- |
| `textures/` | 完整图、功能层、覆盖图、最终登记 JSON 和原审核预览 |
| `scenes/`、`scripts/`、`shaders/` | 当前工程使用的正式场景及交互实现 |
| `examples/standalone/` | 可单独运行的同步副本，含地板和机器人依赖 |
| `source/` | 用户原始选图、三视图、完整母图、提示词与来源记录 |
| `docs/` | 建筑现行规范及相关生产说明 |
| `tools/` | 同步、覆盖导出、功能层导出和交互验证工具 |
| `verification/` | 本次迁移后的运行检查和完整性结果 |
| `review/` | 原版 TA 回执、之前的整合审核和路径迁移记录 |
| `delivery/` | 原 v004r1 冻结 ZIP，保留原审核字节 |

正式生产入口是本包的 `textures/scenes/scripts/shaders`。独立示例是同步副本，修改正式资源后从项目根目录运行：

```powershell
& .\assets\ember\buildings_final\tools\sync_building_demo.ps1 -Verify
```

主工程中的示例沿用项目共享地板和机器人；独立示例已附这两项依赖。复制到其他项目时可直接使用独立示例中的项目结构，或同时带上依赖。`examples/`、`source/`、`docs/`、`review/`、`delivery/` 与 `verification/` 用 `.gdignore` 隔离，避免主工程导入历史资料和嵌套示例；独立项目仍正常导入自身资源。

## 审核与迁移记录

原图片和交互范围已通过 [v004r1 原审核](review/original-v004r1/review-building-v004r1.md)；前次运行整合和规范通过 [TA 回执](review/ta-review.md)。原回执及报告中的路径、哈希和计数属于审核当时的快照，未改写历史。

本次移动的旧址、新址及移动前哈希见 [relocation-plan.json](review/relocation-plan.json)；最新验证见 [迁移结果](verification/relocation-result.json)及 [Godot 检查](verification/validation.json)。本包只集中最终有用文件，原废弃隔离目录继续留在包外。
