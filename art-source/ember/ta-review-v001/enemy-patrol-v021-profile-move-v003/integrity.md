# P21 v003 正侧移动：独立增量技术复审

2026-10-07，**PASS_INCREMENTAL_TECHNICAL**。新固定包及冷载通过，旧 E 浅靴缘 P2 的四个源点已唯一归属刚性 foot。实际视觉闭环见 [视觉复审](visual-review.md)；正式整批结论由根合并实际网页后发出。

## 固定对象及变化范围

ZIP `enemy_patrol_profile_moves_v021_v003_2026-10-07.zip`，SHA256 `4e7bf6c2dc794ec64bb576c74b5755d4f08c9b8d5703c9dd4f15703c4a1c5a95`，2,887,268 bytes。132 payload 加 manifest，共 133 成员；CRC、成员集合、逐项大小/SHA、冻结目录字节全部独立相符。catalog SHA256 `53702cd8beefdf73d51754c3587d6bb54ee6fe8e1dddb27a652e7df096336c5f`。

实际与 v002 固定载荷对照：

| E 帧 | F00 | F01 | F02 | F03 | F04 | F05 | F06 | F07 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RGBA 改变像素数 | 4 | 2 | 2 | 2 | 4 | 0 | 0 | 5 |

六帧合计 19 像素次。E F05/F06、W 八帧及旧 S/SE 十六帧共 26 PNG 保持 v002 字节；W/S/SE 三张 atlas 保持。32 PNG 的 catalog SHA、二值 Alpha、128×128 画布与各 atlas 格全 RGBA 独立相符。16 张 source PNG 全部保持，包括 C002 六拆件、两中性和 S002 八原源；六拆件另与 C002 固定 ZIP 原字节绑定。两方向实际 bind 与 C002 全 RGBA 零差；相对 S002 历史 W49/E50 差异仍保留，未被改写为零差。

## 四个源点及实际运行归属

| E 实例 | 原源坐标 | 原 RGBA | v002 → v003 唯一归属 |
| --- | --- | --- | --- |
| near | (61,94) | (244,237,225,255) | right_shin → right_foot |
| near | (61,95) | (238,227,213,255) | right_shin → right_foot |
| far | (64,91) | (244,237,225,255) | left_shin → left_foot |
| far | (64,92) | (238,227,213,255) | left_shin → left_foot |

这是独立读取新旧 Godot 实际 ownership mask 后，在各自 source_kind 不透明源上逐点比较的结果。只有上述四点改变实体归属；每个 near/far 实例仍无漏归属、无重复归属。没有仅以作者 `revision_v003.json` 的声明作为证明。

`rig.gd`、`preview.gd` 和 shader 与 v002 同字节；`rig.json` 的实际变化是版本文字、四点相关 polygon/exclude 边界及四条真底行测点说明。18 张新运行 mask 与独立 polygon 复算一致，16 pose 与既有步相数学和 catalog 一致。body/cap/foot 仍为 identity basis 加整数平移；源点运动按 foot 平移复核。短连接端点误差为 0，无塌缩连接。F04 的旧 (66,93)/(67,94) 浅尖已不在，原浅甲落回 foot 对应 (65,94)/(65,95)；F07 近靴浅甲回到 (59,94)/(59,95)。这些实际 RGBA 变更仍须以视觉判断是否自然，见配套报告。

## 真底行与名义 sole

新增 `visible_sole_source_pixel_center` 分别为 W near (64.5,103.5)、W far (61.5,100.5)、E near (63.5,103.5)、E far (66.5,100.5)。独立确认其整数像素是对应刚性 foot 最低不透明源行的真实实体，随后按实际整数 foot 位移映射。

32 个新登记测点中，按层级与源归属独立判断 **26 自显、6 被其他部件遮挡**；未仅凭最终 RGBA 等于某颜色判断可见。扩展到所有真实底行像素共 256 次，200 自显、56 遮挡；32 条足底行中 28 条至少露出一个真实足底像素。E 原名义 sole 的横坐标仍可能落斜底透明处，它是运动登记，不是可见像素探针；纵向最低边登记正确。未绘制额外脚底，也未把遮挡测点当作支撑显示证据。

## 新完整 ZIP 冷载及边界

从完整新 ZIP 建立无 `.godot` 的隔离副本，保留包内导入配置。Godot 4.7.2-stable (steam) 导入与独立探针均退出 0，stderr 为空；**4 clips / 32 嵌入格** 的导入 RGBA 与对应 atlas、PNG 相符，8 帧/8 FPS/loop、duration、区域、画布/root、实际预览实例注册、18 ownership mask、16 pose 及中性变换均核对。导入后 132 载荷 SHA 不变。

独立 CPU 重建 W 八帧零差；E 保留 16 次 RGBA、其中 5 次 Alpha 的采样边界残差（v002 为 19/7），不冒称 GPU 零差。作者 48 GPU、8 player、8 switch 证据只核绑定；本线没有重跑完整 GPU/播放器矩阵，也未验证主游戏地面速度。根另做实际网页正常/慢速及重点帧。

根当前实际入口发现标题及 h1 仍显示 **v002**，登记为 **P3 展示版本标签**；固定 ZIP、catalog、实际资源以本报告绑定的 v003 为准。此项由根网页观察提供，不改变固定包，也不回写生产内容。

证据：[完整包绑定](technical-zip-binding.json)、[新冷载回执](technical-cold-receipt.json)、[32格与实际 rig 读回](technical-minimal-cold-load.json)、[独立技术明细](technical-integrity.json)、[增量/四点/真底行明细](incremental-review.json)、[增量脚本](incremental-review.py)、[技术脚本](technical-audit.py)、[冷探针](technical-cold-probe.gd)。所有新增文件仅位于本 TA 目录，冻结包未改。
