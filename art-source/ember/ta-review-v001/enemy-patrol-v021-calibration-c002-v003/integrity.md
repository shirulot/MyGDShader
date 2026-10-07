# P21 C002 v003 双向静态校准技术复审

2026-10-07。结论：**PASS_STATIC_TECHNICAL**。冻结 ZIP、S002 原源、实际 body/near/far 拆件、整数平移、原色连接来源和完整冷重建通过。本项只含 W/E 中性母稿及六张实际拆件，**0 条新动作**；旧 P21 v001 的移动帧没有因此转为通过。静态造型结论另见 `visual-review.md`、`root-preview.md`。

## 交付绑定与冷重建

- ZIP `enemy_patrol_profile_calibration_v021_c002_v003_2026-10-07.zip`，44,513 B，SHA256 `87d0ecf437c93451eddcdad59387f6f03191efcdfdfa1cb197b6e41e819f4ab2`。
- 21 payload + manifest = 22 文件，逐项大小/SHA、完整成员集合、安全相对路径及冻结目录字节一致。`manifest.json` SHA256 `f3f6c95bce4e61d52940bb041b51a1be04f458326eb040f7f46e515b44dbf546`。
- `technical-cold.py` 完整解压到新 `technical-cold-load`，首次无 `.godot` 缓存；先独立导入，再用真实 Godot 4.7.2 Compatibility GPU 执行已读过的 `export.gd`。两张中性、六张拆件和一张对照图共 **9 PNG** 重建后，原 **21 payload SHA 全部不变**；两个进程退出码 0，stderr 均 0 B。导入 3.039 s，重建 1.614 s。
- 所有重建仅发生在 TA 隔离副本；冻结包 21 payload 未改。未复跑或暗示运行任何动作 GPU 矩阵。

证据：`technical-zip-binding.json`、`technical-cold-receipt.json`、`technical-cold-{import,export}.{stdout,stderr}.log`。

## 原源、拆件和实体来源

两张 `source` 分别与 S002 原 ZIP 内 `neutral_left.png` / `neutral_right.png` 字节相同；原 ZIP SHA256 `28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1`。画布仍为 128×128，root `[64,104]`。独立按配置多边形、保护区和矩形边界计算 mask，再核实际拆件 PNG：

| 项目 | W / left | E / right |
| --- | ---: | ---: |
| body 不透明像素，逐像素取原源 | 624 | 599 |
| near 中原腿刚体像素，RGBA 原位相同 | 159 | 144 |
| near 实际不透明像素（含连接） | 178 | 160 |
| far 对 near 的实际整图整数位移 | `(-3,-3)` | `(3,-3)` |
| 原保护区不透明像素，候选颜色全保持 | 223 | 226 |

far 的 Alpha 和全部不透明 RGBA 精确等于本方向 near 平移，没有镜像、重色或独立缩放。它们是复用同一原腿设计的两个物理实例，不能表述成 S002 原稿提供了两张独立腿源。实际输出按 **far → near → body** 组合，与中性候选全 RGBA 零差。

原图及全部实际拆件、候选的 A=0 隐藏 RGB 均为白色 `(255,255,255)`。本审查使用相同透明白底做全 RGBA 比较；用透明黑画布合成会产生不可见 RGB 差异，不能当作可见变形。

原源有 W 41 / E 38 个不透明像素没有被 body 或原 near mask 直接保留，位置均记录在 JSON。这是当前腿部重组的实际边界，**不能宣称全原像素零删除或唯一归属无复用**；近、远实体本身又刻意复用同源腿像素。来源是否清楚与最终造型是否合格分别核验。

## 候选差异与原色连接

| 对 S002 原源的实际差异 | W | E |
| --- | ---: | ---: |
| 全 RGBA 差异 | 49 | 50 |
| 原透明变不透明 | 8 | 12 |
| 原不透明变透明 | 9 | 4 |
| 两边均不透明但 RGB 改变 | 32 | 34 |

每个变化位置独立追到实际最上层和原源采样，结果坐标与作者审计一致。头胸、手臂/工具保护部分保持原色；y103 整行 RGBA 保持，最低不透明 y 仍为 103。W `(66,94)` 是 `(32,58,84,255)`；E `(59,94)` 是 `(34,63,93,255)`，均仍属原 near 胫部 mask。

连接为腿组内 z=-1、宽 4 px 的固定四边形，nearest 采样原图 2×2：W `[66,92,2,2]`、E `[58,92,2,2]`。其颜色全部来自这四个原像素；body 在上层遮挡连接。near 中除了原腿刚体，W 19 / E 16 个像素属于该连接四边形且命中原 2×2 颜色。far 也随同连接一起整数平移。**沿用原 RGB 不等于没有新输出 Alpha**，上表明确记录最终新 Alpha。

CPU 对 Polygon2D 的最近邻 UV 采样近似存在真实残差：W near `(66,83)`、`(68,84)`、`(65,85)` 共 3 点，E near `(58,84)` 1 点，均是仍不透明的原 2×2 颜色间选择差异，没有 Alpha 残差。组合到最终候选后剩 W 2 点 / E 1 点。首次以 CPU 推算单一 UV 坐标作强断言触发审查脚本断言，随后保留实际残差和全部可匹配原源坐标；没有把它改写成 CPU 零差。独立 GPU 冷重建全部字节零差，原腿刚体本身的 RGB 也为零差。完整数值保留在 `technical-integrity.json` 的 `cpu_near_residual`、`cpu_final_residual` 和 `final_difference_routes`。

## 放行范围

本技术线未发现新增 P1/P2，支持主 TA 合并视觉结果后关闭这次静态校准闸门。后续动作仍须以本次固定母稿与拆件为基线，独立检查髋连接、遮挡、步相、接地和循环；静态整数副本不能证明动作一致性。

复核入口：`technical-audit.py`，证据 `technical-integrity.json` 与四张 `technical-mask-*.png`。冻结包和生产目录均未修改；生产通知由主 TA 执行。
