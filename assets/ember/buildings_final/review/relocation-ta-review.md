# 最终建筑目录迁移 TA 回执

日期：2026-10-06。结论：**PASS_RELOCATION_ONLY**。当前正式入口为 [最终建筑资源包](../README.md)，独立示例为 [project.godot](../examples/standalone/project.godot)。本次迁移未发现新的 P1/P2，原 v004r1 图片、已审核交互和规范范围继续有效。

## 独立核验结果

| 范围 | 结果及证据边界 |
| --- | --- |
| 文件映射 | 308/308 新址存在、清单旧址均不存在；165 个 operation 与逐文件映射一致，目标均在声明包内。192 项仍与迁移前 SHA 相同，其余差异逐项登记。 |
| 美术与历史证据 | 独立展开的 149 个关键去重文件全部保持原字节；原 ZIP 的 CRC 和 78 项载荷清单通过。32 张正式 PNG、对应示例副本、三母稿、三用户参考及 Shader 与原包一致。制作方保护数量 115 未提供成员列表，不计为独立复现的检查项数。 |
| 运行文件 | 14 份代码、场景和工具正文严格等于旧基线按声明映射替换路径；两份正式 JSON 的非路径数值、几何、锚点及状态保持。同步 PowerShell 工具另有 UID 白名单复制，已单独审 diff，不归入“仅路径替换”。 |
| 路径及同步 | 53 个实际引用点在主工程和示例双侧的 106 次检查全部闭合；两份同步清单各 66 项均重算通过，当前二者唯一差异为示例重新生成的验证 JSON。7 个正式 UID 未变，示例 7 个 UID 现与正式来源逐字节一致；运行文件没有 uid:// 引用。 |
| 新入口实际运行 | 独立隔离工程冷导入 exit 0、stderr 0；真实 OpenGL Compatibility 后端定点 **18/18**，exit 0、stderr 0。包含 7 场景加载、三栋建筑实际入树初始化及 demo 的三栋定义、1100 格共享地板和角色纹理加载。 |
| 规范与文档 | 现行建筑规范仅有 21 个 Markdown 链接目标变更，正文、数字和验收范围不变；包内当前文档 54 个直接本地链接有效。根代理另核共享导航五份文档的 93 个本地链接，无缺失。以上为各自固定快照计数。 |

本轮实际运行限于上述 18 项。制作方 94/94 仅绑定证据，不称为 TA 独立复跑；前次 23 项行为审核和原视觉审核保留原范围。本轮没有重新图审，也没有新增完整室内、分楼层遮挡、风机旋转或真实环境照明的通过结论。

`path-repair.json` 属于修复阶段快照，其后 70 个 `.import` 已再生；另有同步工具、示例验证 JSON 和 7 个示例 UID 变化。完整性和运行分报告分别解释这些差异，没有把缓存/身份元数据变化误记成正式图片漂移。历史报告按原字节保留，原路径通过 [迁移映射](relocation-plan.json) 查询当前地址。永久删除已停止，本次审核没有操作废弃隔离目录。

## 固定来源与分报告

- 原 v004r1 ZIP SHA256：`22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32`。
- 当前规范 SHA256：`5d3861adf4be17d82ec691771ca1600272f21ee5a142ee011ad65271c5559e5c`。
- 前次 TA 回执 SHA256：`63192fe924c675c21e635ccc1d8bb55b1ee41302437f335daa3ac66cda359477`。
- 主工程 project.godot SHA256：`f1b0b9d3a429cbc38d19cfcb9c0d683f15e6543a53c175b78b2c6296ca6718ba`。
- [独立完整性报告](../../../../art-source/ember/ta-review-v001/building-relocation-independent/integrity.md)、[逐项绑定](../../../../art-source/ember/ta-review-v001/building-relocation-independent/binding.json)。
- [独立运行报告](../../../../art-source/ember/ta-review-v001/building-relocation-independent/runtime-review.md)、[18 项实际结果](../../../../art-source/ember/ta-review-v001/building-relocation-independent/cold-project/ta-relocation-load.json)。
- [独立文档报告](../../../../art-source/ember/ta-review-v001/building-relocation-independent/docs-review.md)。

允许以新目录作为当前交付和后续维护入口；未来实质资源、动画或行为改动仍按改动范围提交增量审查。
