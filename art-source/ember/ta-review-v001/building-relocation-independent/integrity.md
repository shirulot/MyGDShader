# 建筑最终包迁移：独立文件完整性核验

**结论：RELOCATION_MAPPING_AND_ART_HISTORY_INTEGRITY_PASS。** 本轮未发现迁移目标缺失、路径越界、建筑图片/母稿/Shader/原冻结 ZIP 或历史 TA 证据的字节漂移。通过范围是文件、原包和注册绑定；没有重新图审，没有启动 Godot，也不代替另代理的代码和实际运行复核。

## 核验快照与映射

快照时间：2026-10-06 23:12:28 +08:00。

- `assets/ember/buildings_final/review/relocation-plan.json` SHA256 `a448dba09352fb047cb0658fe98bd2829c542a162bac8687cd7bb59850377b73`。
- `verification/relocation-result.json` SHA256 `3b1307b2c85b773b860e6a0c5055730008b7db0822fc32c8e6fa92a498e8359b`。它是制作方回执，本报告的结论来自独立复算，而非其 PASS 字段。
- 308 条文件映射、165 个 operation 均独立展开检查：旧/新名称无重复，路径无 `..`/绝对路径逃逸，解析后均留在工作区，新址均落在最终包内；每文件的相对后缀与相应目录/文件 operation 一致，各 operation 数量匹配。
- **308/308 目标存在，308/308 清单旧址当前不存在，missing=0。** 迁移前字节总数独立汇总为 93,339,422 B，与计划/回执一致。这说明当前映射完整，不据此宣称观察了全部历史移动过程或从未删除文件。

## 字节保持与原包交叉绑定

逐项重算 308 个当前文件 SHA：192 个仍与 plan beforeSHA 一致。进一步独立展开 **149 个关键文件的去重集合**：83 张 PNG、2 个 Shader、1 个 ZIP、65 个历史 review 文件，扣除同时归入 PNG 的 2 张历史图；149/149 的 SHA 和字节数均与迁移前记录相同。历史 review 的代码、JSON、日志和 11 份 Markdown 都包含在此核验中。

制作方的 `protected_files_unchanged=115` 只给了计数，没有列出该集合成员。本报告不猜其分组，也不把 115 直接称为独立检查项数；提供上面的 308 全项核对和可逐条追溯的 149 关键集合。

- 原冻结 ZIP 当前在 `assets/ember/buildings_final/delivery/building_assets_v004r1_2026-10-06.zip`，28,875,505 B，SHA256仍为 `22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32`。重新检查全部 CRC 和 78 manifest 载荷 SHA/字节数，79 条目一致。
- 从该 ZIP 直接比对当前 **32 张正式 PNG**，均逐字节一致；独立 standalone 的对应 32 副本也逐字节一致。原 3 张完整母稿、3 张用户选图，以及原 Shader 对当前主/standalone 两副本，均逐字节一致。合计 39 个原包成员绑定，另含 33 个副本一致性核对。
- 三母稿 SHA 仍为：控制塔 `3989ea530ae9200b3b95763826c3b0113139f3274fa168a0db1b84308f82b7fa`；维修间 `c61f2ad82b4e99f096321289a737b23fd7af25af7b4838cb3e1f0b600a20317c`；物流仓库 `9f9f74df29d9d62259be77fa0da0cb362368e2b0640ca977aac5b9ba5b9ecc50`。
- 当前主/standalone 两份 catalog 均精确等于原 ZIP catalog 按 plan 的路径映射替换字符串后的结构。全部非路径数值、几何、pivot、scale、门/设备区域及层定义保持；没有把预期路径元数据改写误判为注册漂移。
- 原 v004r1 审查迁至 `review/original-v004r1/`，本代理原报告 `integrity/report-integrity.md` 保持 beforeSHA。前次整合 TA 回执在 `review/ta-review.md`，SHA256 `63192fe924c675c21e635ccc1d8bb55b1ee41302437f335daa3ac66cda359477`；归档/规范/运行定点报告在 `review/consolidation-ta/`，全部原字节保留。历史路径文字没有追溯改写，当前位置由 mapping/current review README 提供桥接。
- 主项目 `project.godot` SHA256 `f1b0b9d3a429cbc38d19cfcb9c0d683f15e6543a53c175b78b2c6296ca6718ba`，与迁移前计划一致。

## 当前路径及再生元数据的差异边界

308 项中其余 116 个 SHA 有变：5 JSON、70 `.import`、8 Markdown、14 scene、10 GDScript、1 PowerShell、1 standalone project、7 UID。这里如实保留差异，不虚写“308 项全部原字节不变”。本轮已实际证明 catalog 仅做声明路径替换；代码及场景正文的等价性另由代码审查方核实。

`verification/path-repair.json` 保存的是路径修复阶段的 afterSHA；当前 70 个 `.import` 已再生，全部不再等于该阶段的 afterSHA。不能把此旧阶段回执称为当前缓存快照，也不把导入元数据重生当成 PNG 或 Shader 改变。

还有 9 项当前变更未列入该阶段 path-repair：

- `tools/sync_building_demo.ps1`：当前 SHA `7cdf6f61e075ba22b49c37401c4368b875162ffff09316e5b9fb16aecbbd1049`。已精确通知根代理，由代码方核验其同步入口改动；本报告不未经复算称其“只有路径变化”。
- `examples/standalone/assets/ember/buildings_final/textures/previews/validation_v004r1.json`：为 standalone 重验结果，不是原图片载荷。当前 SHA 已记入 binding。
- 同一 standalone 包内 `scripts/` 的 3 个 UID、`shaders/` 的 1 个 UID、`tools/` 的 3 个 UID：当前已重生；原脚本、Shader 字节检查与 UID 是否改变分别登记。完整旧/新 SHA、路径均在 binding。

上述没有造成当前目标缺失或确认的美术/历史证据漂移。本报告绑定保存记录，不把制作方的冷导入/GPU 94 项回执冒称本代理重跑；运行结论由另代理实际审核。未遍历无关个人目录，未操作归档 hold，未移动、删除、恢复或编辑生产及历史报告。

逐条数据：[binding.json](binding.json)。复算脚本：[verify_integrity.py](verify_integrity.py)。
