# 最终建筑资源与示例

正式目录已整理为一套最终建筑：控制塔、维修工坊、物流仓库。沿用已通过 TA 的 v004r1 图片；运行组件已展开旧继承链，独立示例不再依赖旧版本代码。

本次将**独立示例**的旧导入缓存归档后重新冷导入，通过制作方 94/94 实际 Godot 检查；主工程及其编辑器缓存未改。正式图片、原始母图和原 v004r1 冻结包保持原内容。

**技术美术总监已正式通过本次规范与运行组件整合审核**，见[本轮 TA 回执](ta-review.md)。独立定点检查为 23/23，并在真实 OpenGL Compatibility 后端复核同组 23/23；制作方 94 项与 TA 独立检查分别记录。归档映射核对通过，永久删除仍未执行。

| 用途 | 入口 |
| --- | --- |
| 直接运行示例 | 用 Godot 打开 [demo/project.godot](demo/project.godot)，运行主场景；独立视口 1408×800 |
| 正式 PNG | [building_assets_v004r1](../../../assets/ember/building_assets_v004r1/)：3 张完整图、15 张功能图（含 3 张固定主体）、3 张共享覆盖图 |
| 放入现有项目 | [预制体目录](../../../scenes/ember/building_assets_v004r1/)：3 个静态、3 个交互预制体和 1 个 demo |
| 正式组件 | [建筑](../../../scripts/ember/building_asset.gd)、[示例](../../../scripts/ember/building_demo.gd)、[角色](../../../scripts/ember/building_demo_actor.gd)、[完整建筑 Shader](../../../shaders/ember/building_intact.gdshader) |
| 实际预览 | [闭合](../../../assets/ember/building_assets_v004r1/previews/gpu_intact_closed_v004r1.png)、[开门](../../../assets/ember/building_assets_v004r1/previews/gpu_intact_open_v004r1.png)、[交互界面](../../../assets/ember/building_assets_v004r1/previews/gpu_demo_ui_v004r1.png)；共保留 11 张原审核证据图 |
| 后续制作规范 | [建筑样式与交互规范 v002](../../../docs/shader-learning/ember-building-standard-v002.md) |
| 初始选型 | [用户选中整图](../selected-buildings-v001/references/)与[选择记录](../selected-buildings-v001/selection_record_v001.json) |
| 生产来源 | [完整母图](../building-assets-v004/masters/)、[提示词](../building-assets-v004/prompts/)、[生成记录](../building-assets-v004/generation_manifest_v004.json) |
| 原版审核 | [原 v004r1 TA PASS](../ta-review-v001/building-v004r1-independent/review-building-v004r1.md)，结论仍仅对应原冻结版本及其声明范围 |
| 原版可恢复交付 | [原 v004r1 ZIP](../deliveries/building_assets_v004r1_2026-10-06.zip)，SHA256 保持 `22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32` |
| 本轮复验 | [运行结果](verification/validation.json)、[整合记录](verification/consolidation-result.json)、[固定快照](verification/review-snapshot.json) |
| 本轮正式审核 | [规范、运行整合与归档增量 TA 回执](ta-review.md)：规范／运行 PASS，删除仍待解除环境拦截 |

## 示例操作与范围

方向键／WASD 移动；E 人门、G 货门、C 检修盖、F 设备启停、R 维修；靠近面板 P 供电、L 人门锁、X 故障；I 前窗亮暗；H 整壳遮挡检视、J 塔顶盖检视；F5/F9 保存／恢复。

进入建筑时整壳透明度即时切为 0.14，离开恢复；开门／开盖显示深暗口。灯改变登记灯面和前窗；本示例不含完整室内、分楼层遮挡、环境动态照明或风机动画。

## 唯一来源与同步

主工程的 `assets`、`scenes`、`scripts`、`shaders` 是正式生产入口，`demo` 是独立运行的同步副本。修改正式资源后运行 `tools/sync_building_demo.ps1 -Verify`，避免两处各自修改。共享地板与机器人只作为示例依赖保留；其他素材线不在本次清理范围。

`demo/SOURCE_SYNC_MANIFEST.json` 记录从正式目录复制时的来源哈希；`demo/SYNC_MANIFEST.json` 记录示例验证结束后的实际文件哈希。验证会生成自己的报告／截图，不能把生成后的文件继续声称为原来源快照。`consolidation-provenance.json` 保留原冻结包和整合前来源；新脚本的独立 TA 增量审核已通过，范围与原版本回执分开记录。

## 旧材料处理状态

已从正式目录移走 9,628 个文件（1,912.70 MiB，137 个目标）。**状态为 `ARCHIVED_PENDING_DELETE`；实际删除 0 个文件，释放 0 字节。** 自动审批以 `blocked by policy` 拒绝删除，未提供更细原因；因此仅作可恢复归档，没有绕过拦截执行删除。

工作区旧版本集中到 [building-cleanup-hold](../building-cleanup-hold/)，按原相对路径保存并使用 `.gdignore` 排除导入；五份旧便携 stage 位于本 chat 的 visualizations 下同名归档目录。它们均不参与正式示例或交付。独立 TA 的最终截图、结果和探针继续保留在原回执目录；重复冷解包内容已归档。

[清理清单](cleanup-manifest.json)逐项记录原位置、归档位置、文件数、字节数和处理状态。需要追溯旧版时按清单到归档查找，原 v004r1 发布内容也可从保留 ZIP 恢复。清单中独立示例的旧缓存已经归档，原位置会正常生成新的导入缓存。
