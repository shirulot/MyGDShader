# 建筑收尾归档增量复核

**归档映射与现行入口检查通过；当前 README 第 5 行状态/数量待根更新。** 本轮只读清单指定路径，未删除、移动、恢复任何生产或历史文件，未运行 Godot、重验 PNG 或重写历史回执。

## 核验快照

`art-source/ember/buildings-final/cleanup-manifest.json` 的核验 SHA256：`f46a291170f6329df3e0b4d697a8b37e53ebd859ebf77612a5b01a9e1b707830`。读取与检查结束时字节一致；后续归档/缓存变化不包含在本快照结论内。

- 当前状态 `ARCHIVED_PENDING_DELETE`；137 目标（93 文件、44 目录），合计 **9,628 文件、2,005,614,066 B / 1,912.70 MiB**，不是派发时的 9,542 / 1,893.52 MiB。
- 制作方清单声明 `deleted_files=0 / deleted_bytes=0`，记录路径审批阻止删除。本轮可验证归档目标存在及清单匹配，**不能凭当前存在状态证明此前从未删除任何文件**。
- 137 个目标均存在，映射严格为其清单规定的原相对路径；每个目标的文件数/总长度与登记完全一致，无目标缺失或映射越出 hold 根。未逐个比较历史载荷 SHA，因而不把 count/bytes 匹配表述成全部旧内容字节保真。

| 归档组 | 目标 | 文件数 | 字节 |
| --- | ---: | ---: | ---: |
| workspace `art-source/ember/building-cleanup-hold` | 132 | 6,774 | 1,531,261,913 |
| C 盘指定 01a11003 线程的 `building-cleanup-hold` | 5 | 2,854 | 474,352,153 |

C 盘仅读取清单中的 `building-assets-v001/v002/v003/v004/v004r1-portable` 五个 stage 及对应 hold 目标，没有遍历其他个人目录。两个 hold 根均有 `.gdignore`；该新增标记不计入清单载荷数。

136 个原源路径当前不存在。唯一现存源为 `art-source/ember/buildings-final/demo/.godot`，现有 86 文件、20,110,343 B；最新写入 22:26:51 晚于清单归档时间 22:22:40。它可由运行复验再生，不能因此判归档失败，也不能误写“137 个源路径全部消失”。已存在的原归档 cache 目标仍匹配清单，本轮不继续追逐缓存增长。

## 当前入口与旧基线追溯

- `ember-building-standard-v002.md`、统一 `docs/shader-learning/README.md`、`art-style-standard-v002.md`、`buildings-final/README.md` 共 **79 个本地 Markdown 链接，0 断链**。最终完整 PNG、功能层/登记、场景、独立 demo、用户选中参考、v004 母图/提示、正式 v004r1 ZIP 和 TA 回执入口仍存在。
- 历史建筑规范、选中三视图/拆件、完整母图规则与覆盖规则的 16 个辅助链接也存在。v001/v002 独立来源报告、v004r1 正式回执及 v004 注册基线保留。
- v001–v003 制作目录及 v001–v004 旧 ZIP 按清单归档到 workspace hold 的原相对路径，旧独立解包/冷工程亦有明确映射。历史报告中的旧活动路径不能自动视作仍可直接运行；原冻结包与 hold 映射提供追溯入口。本轮没有改写历史回执来伪装新的运行结果。

## 精确待修文档

`art-source/ember/buildings-final/README.md:5` 在发现时仍写「清理尚未执行」「6,688 个文件、1,441.15 MiB」。这与当前 `ARCHIVED_PENDING_DELETE` 及上述核验快照不一致。

根已收到精确位置；待制作方归档稳定后，将当前 README 改为“可恢复归档完成、永久删除待执行”，引用最终清单数量与 hold 映射，并将 94/94 保持为制作方整合运行记录。**不改历史回执，也不把归档核对扩大为新视觉/GPU PASS。** 数量后续如有变化，以稳定后的 manifest 为准，本报告保留本轮快照。
