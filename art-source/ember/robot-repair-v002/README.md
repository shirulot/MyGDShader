# 机器人v002修复记录

使用入口与修复范围见[修复交付说明](../../../docs/shader-learning/asset-production-robot-repair-v002.md)。旧QA位于`../quality-audit-2026-10-04/`，保留缺陷记录；本目录记录修复后的独立数值测量、主审视觉复核和实际Godot结果。

- `annotations/`：可编辑rig与关节补像素标注；原部件位移不变。
- `finished-frames/`：16行走帧与图集，同正式v002 PNG逐字节一致。
- `previews/`：固定调色板四向GIF、精确125ms APNG与原生前后对照。
- `independent/`：不调用制作器的PNG连通性／色板／归属检查和逐帧审阅图。
- `godot-stage-exits.json`：9阶段实际退出码、日志SHA。
- `godot-render.json`、`render/`：40个1×／2×真实GPU病例。
- `fresh-godot-render.json`、`fresh-render/`：无原缓存／autoload新工程的40病例。
- `independent-repair-review.json`：主审最终视觉结论，明确区分代理制作、独立数值工具与主审复核。
- `final-acceptance.json`：生产资源、源标注、证据、文档和历史冻结的最终SHA绑定。

`fresh-project-v001/`只供本地验证，交付包排除其副本和所有缓存。独立编写的测量工具由另一代理提供，但最终候选的视觉复核在使用限额后由主审完成。v001资源和历史报告不会随本次修复改写。
