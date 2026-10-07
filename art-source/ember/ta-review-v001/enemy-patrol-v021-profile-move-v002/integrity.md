# P21 v002 W/E 移动独立技术复审

2026-10-07。结论：**RETURN_P2_RIGID_BOOT_EDGE_IN_AFFINE_SHIN**。包体、C002 固定拆件、中性绑定、步相、32 PNG/atlas/TRES 和最小完整冷载通过；**E 两点浅靴边误归柔性 shin，已经出现可见的非刚性靴位移，需要局部返修**。视觉线以独立按刚性靴锚点对齐的未标注浅深图复核，确认 F04 亮尖和 F07 上移硬边。旧 C002 静态闸门仍成立；这里核查的是新动作的部件归属。

## P2：E 浅甲归属到柔性 shin

实际 C002 near 纹理中 `(61,94)` 为 `(244,237,225,255)`，`(61,95)` 为 `(238,227,213,255)`，属于浅靴的上沿；far 是同方向固定副本，对应 `(64,91)` / `(64,92)`。当前这些点分别被分给 `right_shin` / `left_shin`，随 `apply_segment()` 做端点仿射，而非随 `_foot` 做整数平移。因此“仅短暗连接伸缩、靴子保持刚性”的约束并未完整满足。

独立用实际 pose 逆采样并检查 PNG：near F04 的 shin 轴向尺度为 2.1213，源 `(61,95)` 的连续中心相对正确刚性 foot 位置偏移约 `(+1.225,-1.725)` px，实际同源浅色可见于 `(66,93)`；`(67,94)` 另在保留的 CPU 采样边界残差中，不能混称精确 CPU 零差。F07 源 `(61,94)` 偏移约 `(-0.120,-1.565)` px，实际可见 `(59,92)`。F05/F06 两点所在段尺度为 1，与 foot 平移一致。大多数其他帧被靴/上层遮住，本报告没有把隐藏的理论偏差都算作可见缺陷。

源点、连续变换、实际可见点和遮挡分别保存在 `technical-e-shin-trace.json`，图为 `technical-e-shin-armor-12x.png`；独立视觉证据为 `visual-e-foot-aligned-*.png`。视觉线另核原 PNG 的 F04 `(66,93)/(67,94)` 均为 `(238,227,213,255)`、F07 `(59,92)` 为 `(244,237,225,255)`，确认浅甲上缘被向上/前方拖动。整体仍保留原靴身份，但局部硬甲违反刚性约束，不能因仅两点而豁免。

最小修正方向是把这两点及 far 对应点归还同源刚性 foot，保留已过 C002 六张源图和 RGB，不重新生图、不改近远腿身份；修正后应仍保持 C002 bind 零差，并核 E 全 8 帧和循环。W 和旧 S/SE 应保留已审原字节，正式返修回执由主 TA 合并。

## 冻结包与固定来源

- ZIP `enemy_patrol_profile_moves_v021_v002_2026-10-07.zip`，2,883,551 B，SHA256 `c5e82a238abaf9c0d258370322c02503cc320364cacca7f17d7b59547925481b`。
- **130 payload + manifest =131 文件**；CRC、成员集合、安全路径、每项大小/SHA、冻结目录字节一致。catalog SHA256 `bd3f70e183fad3c713c59c2e5336c7915903810f57896528426c09b330f24b10`。
- 8 张原母图与 S002 原 ZIP `28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1` 及本包同方向 reference 字节相同。
- 六张 actual `body/near/far` 和两张 C002 neutral 与静态校准 ZIP `87d0ecf437c93451eddcdad59387f6f03191efcdfdfa1cb197b6e41e819f4ab2` 字节相同。没有使用被退 v001 的生图腿靴。
- 本包实际 `qa/bind`、输出 neutral、独立 mask/z 中性合成均对 C002 neutral **全 RGBA 零差**。对原 S002 仍为 **W49 / E50**，历史新 Alpha W8/E12、失 Alpha W9/E4，y103 原行仍相同。不能把 C002 零差写成原 S002 零差、全原像素零删除或独立双腿源。
- 旧 S/SE **16 PNG +2 atlas** 分别与 v012 原 ZIP 和巡逻 SE 过审 pilot 原 ZIP 逐字节相同。

## 独立归属、步相与动作约束

W 近腿使用解剖左腿，E 近腿使用解剖右腿；另腿是同源 far 实例。每个实例内部源像素恰好被一个部件拥有，完全覆盖，未把两个复用实例混称成唯一原画实体。

| 源实例 | body | 每腿 thigh | 每腿 shin | 每腿 cap | 每腿 foot |
| --- | ---: | ---: | ---: | ---: | ---: |
| W | 624 | 19 | 14 | 34 | 111 |
| E | 599 | 13 | 15 | 40 | 92 |

W near/far 各 178 个不透明像素，E 各 160。W thigh/shin 的 RGB 上界分别 `(29,55,82)` / `(41,66,94)`；E thigh 上界 `(27,53,80)`，但 E shin 上界达到 `(244,237,225)`，正是上述被柔性段带走的浅靴边，未将它们算成全暗连接。

八相位与既有已过 P20/S/SE 的登记相同：F01–F03 右腿抬起、F05–F07 左腿抬起，F00/F04 交替接触。F00 是跨步接触，真正中性来自 `reset_bind()`。独立 world-knee、投影整数舍入、短段端点数学复算全部 **16 pose**，与 catalog 和实际 rig 一致；登记支撑时 sole=ground，连接端点最大误差 0，未出现塌缩连接。body、cap、foot 节点基均 identity 且平移为整数；这不自动覆盖误归到 shin 的两点硬甲。

W 223 / E 226 个原工具保护区不透明像素在各帧随机身 bob 后全部保持原 RGBA。短连接逐源点颜色、实际 mask、z 和像素数均留在 `technical-integrity.json`。

## 最小完整 ZIP 冷载

新建完整 ZIP 隔离副本，最初不存在 `.godot` 缓存。Godot 4.7.2 导入后读取 **4 clips /32 嵌入纹理格**，与 atlas/PNG 全 RGBA 一致；8 帧、8 FPS、loop、区域和 frame duration 均核对。

实际 preview 两个 actor 为 Nearest、未居中；缓存确为 **8 original +8 neutral +4 move =20**，四个批外方向回退静态，未误写成本批已完成。实例化 W/E rig，核 **18 actual mask、6实际源纹理分配、16 pose、两组 reset_bind transforms**。导入 6.197 s，probe 2.438 s；退出码 0、stderr 均 0 B，原130 payload SHA 未变。

全部32正式 PNG为二值 Alpha、正确画布，与相应 atlas 格和 catalog SHA 一致。作者 **48 GPU、8 player、8 switch** 证据与本 catalog SHA 绑定，条目数/全帧记录/循环存在；本线未重跑该矩阵，也未将作者 GPU 结果代称独立验证。

## CPU 残差与真实接地边界

W 8帧 CPU 重建均零差；E 保留 **19 RGBA 像素事件残差，其中7 Alpha**：F00=5、F01=1、F02=1、F03=1、F04=9、F05=0、F06=0、F07=2。完整原坐标及 CPU/实际 RGBA 保留；没有为追零修改采样规则或生产 PNG。上面的浅甲归属问题独立成立，不以“CPU有残差”替代定位，也不把残差全部当成美术失败。

E 的名义 sole x 坐标落在斜靴底透明区：near 源 `(58,103)`、far 源 `(61,100)` 都不属于实际不透明 foot，因此不能拿这些点证明脚掌可见。其 y 登记正确；已另按每个真正 foot 的最低不透明行逐像素核对。两方向32个腿/帧底行，共 **256 源像素事件，200 个实际自显、56 个被其他部件遮挡**，28/32 条底行有至少一个自显像素。所有自显点原 RGBA 相同；真实底行+1等于 sole_y，支撑时也等于 ground_y。其余4条底行完全遮挡，不能声称已观测到接地。

W16个名义点在源 foot 上，但仅10处该点自显；E16个名义点均不能作不透明脚掌测点。建议制作方把名义登记与真实可见接地测点区分，或将 E sole 的横坐标移到稳定脚底实像素；不要把透明测点改成画新脚底。

证据入口：`technical-prepare.py`、`technical-audit.py`、`technical-cold-probe.gd`；结果 `technical-zip-binding.json`、`technical-cold-receipt.json`、`technical-minimal-cold-load.json`、`technical-integrity.json`，局部浅甲证据另见前述 trace。

冻结包和生产目录保持未改。本技术线与独立视觉线均支持 E 局部 P2 返修；未给制作方发通过通知，正式回执由主 TA 执行。
