# Robot collect knee v012 rc01：独立技术复审

结论：**PASS_TECHNICAL_SOURCE_SCOPE_COLD**。本报告覆盖固定候选的来源、改动范围、像素组合、资源完整性与实际运行。未发现新增技术 P1/P2。膝盖、腰髋的动作自然度由独立视觉报告和主 TA 实际播放审查判定，本报告不以关节坐标固定代替观感审查。

## 固定对象与完整性

- 候选：`art-source/ember/robot-eight-way-v011/revisions/collect-knee-v012`。
- ZIP：`art-source/ember/deliveries/robot_collect_knee_v012_rc01_2026-10-07.zip`，14,181,428 bytes，698 载荷文件及 1 份 manifest。
- ZIP SHA256：`4dc7298a4b1f3782635bd461eca6dc2be1179e79b35dc4ecfa7ac04a6030f209`。
- manifest SHA256：`86214fe22664b7ceaeced7084cd4fd111a5dc5147a0b58869a8ca23cb9614890`。
- atlas SHA256：`4c964f4d4d633b98c743d496354bce6e1d91f3c1cbefa741cf5055c6f5db7aac`。

独立读取 ZIP、manifest 和固定目录，698 项逐文件大小及 SHA 一致。完整解包复制用于检查；审查没有运行会覆盖交付文件的作者导出流程，没有改动固定候选。

旧版冻结对象为 `robot-eight-way-v011/delivery/robot-v011`，对照原 final ZIP（SHA256 `8dc65a715b41b2c61a09eb6e2afbcd31134db60228f4b3081a0a39e4d153f4bb`），**336 项原载荷全部保持**。当前 112 张运行帧中仅八方向 collect F01/F02 共 16 张变化，其余 **96 张 PNG 字节保持**。16 张 before/after SHA 与提交清单逐项吻合。

## 原部件、姿态与生成来源

独立核验 `source/fixed-source-mapping.json` 的 **96 项原固定片**：每方向 12 项复制文件与原 `source/action-fixed-parts` 字节、SHA 一致，并与原 rig 账本记录的解码 RGBA SHA 一致。八份 `original_rig_and_poses.json` 与原生产记录字节一致；SW 使用原 `action-rig-pilot/collect/down_left`，其余七向使用原 `action-rig-batch/collect`。

姿态逐结构比对证明：F00/F03 沿用原完整状态；F01/F02 沿用原身体和手臂状态，仅将 pelvis 与腿 upper/lower/end 固定到原注册位置。pelvis pivot 为 (32,56)、位移为 (0,0)、角度为 0；各腿使用原 hip/knee/ankle、角度为 0、lift 为 0。此处证明实际采用的配方与注册来源，不宣称这些数值本身能证明动作自然。

八个采纳的 imagegen 原文件、确切输入与提示词逐 SHA 绑定到 `source/imagegen-ledger.json` 及 `run-manifest.json`；本机原始生成输出仍存在，八份 SHA 均与包内原图相同。生成审计不是本次重新请求 imagegen。SE 的实际输入为 **`source/down_right/imagegen_input_v2.png`**，superseded 的第一版输入对应生成图没有参与最终组合。

每方向输入为 512×768 的 2×2 格；独立缩至 128×192 后，32 个格与各自 `fixed_support_raw_f*.png` 的 Alpha 和可见 RGB 全部相同。八份生成原图为 1024×1536 RGBA，整体统一最近邻缩至 128×192；不存在逐帧重新按轮廓缩放对齐。

## 独立重建与 AI 采纳边界

审查脚本独立反向最近邻采样原部件，按实际层次合成上肢、下肢与保护区，再重建固定支撑阶段：**32 帧原支撑 RGBA 总残差为 0**。F01/F02 的重建替换区为 y≥53、避开上身与膨胀 1px 的手臂保护，并限制在原/新下肢各膨胀 3px 的范围内。

AI 颜色只采纳 x=21..42、y=54..62；S 的 y 范围进一步收窄到 58..62。还必须同时满足固定支撑原像素不透明、body/arms 保护片为空、生成采样 Alpha≥160。RGB 量化到原有 11 色。**最终 Alpha 完全取自固定支撑，不采纳 AI Alpha。** F01 和 F02 都使用生成整图的 F01（右上）格，同坐标采样，不从两个独立生成姿态格分别取色。

| 方向 | F01 实际改色像素 | F02 实际改色像素 | 两帧共有位置颜色 |
|---|---:|---:|---|
| S / down | 6 | 6 | 一致 |
| SW / down_left | 17 | 15 | 15 个共有位置一致 |
| W / left | 6 | 6 | 5 个共有位置一致 |
| NW / up_left | 14 | 14 | 一致 |
| N / up | 70 | 71 | 70 个共有位置一致 |
| NE / up_right | 32 | 31 | 29 个共有位置一致 |
| E / right | 3 | 3 | 一致 |
| SE / down_right | 67 | 67 | 一致 |

合计 F01 为 215 个、F02 为 213 个实际改色坐标，两帧共 **428 像素次**；这不是 428 个新 Alpha 像素。两帧有 209 个共有改色位置且最终颜色一致；保护、原有颜色与遮挡随姿态变化，因此两个实际改色 mask 不必完全相同。逐点采样坐标、原生成 RGBA、量化结果在 `technical-integrity.json`，32 份 `technical-adopt-mask-*.png` 显示实际改色位置。独立颜色组合与最终 32 张 collect RGBA **全部零差**；y≥63 保持固定支撑阶段，上身/手臂保护区没有被采纳。

最终 16 张改帧 **y<53 的全部 RGBA 与原帧一致**；全部 32 张 collect **y≥70 的全部 RGBA 与各方向原 baseline F03 中性靴一致**。这里分别说明“对旧帧”和“对固定支撑”的比较对象，不能把重建腿部的变化写成整张旧图不变。

## PNG、atlas、SpriteFrames 与实际冷载入

112 张 PNG 均为 64×96、二值 Alpha，全部可见 RGB 属于原 11 色。atlas 为 512×2304，全部区域与对应 PNG 的完整 RGBA 一致。24 clips 包含八向 idle（2 帧、2fps、循环）、walk（8 帧、8fps、循环）、collect（4 帧、6fps、单次），根锚 (32,80)。

使用**完整 ZIP 解包**到新 `technical-cold-load`，保留导入配置，起始没有 `.godot` 缓存。Godot 4.7.2 stable 从该目录导入，再加载真实主入口 `res://preview/preview_full_actions.tscn`；导入和实际运行均 exit 0、stderr 为 0。GPU 为 NVIDIA GeForce RTX 4070 Laptop GPU，Compatibility 渲染。

独立运行探针读取实际 SpriteFrames：**24 clips / 112 格导入纹理完整 RGBA、区域与帧参数全部通过**。实际节点为 1× 和 4× 两个 AnimatedSprite2D，Nearest、uncentered、offset (-32,-80)。八方向均自然播放 collect F00→F01→F02→F03 一次，期间方向锁定、结束信号一次、两个节点均回同向 idle F00，节点根位置保持。

另取本批确实修改过的 **SE F01** 实际 GPU 输出独立对照：1× 比较 1,416 个不透明采样，4× 比较 22,656 个不透明采样，均 **0 mismatch**。该 GPU 检查没有扩充成全部 64 样本矩阵；完整 112 格的解码 RGBA 校验与两份实际 GPU 画面验证分别登记。结束后重新核 698 载荷 SHA，无文件变化。

作者 `runtime/evidence/collect-gpu-validation.json` 的 64 GPU 样本、8 次回待机记录已按 SHA `cfed3250f1167977c65574d90ee9efa01dab3ee668c44beaa6e1ac65170ce2d2` 绑定；作者记录为零 mismatch。该矩阵**仅绑定，未当成本次独立重跑**。

## 证据与边界

- `technical-prepare.py`、`technical-zip-binding.json`：ZIP/manifest/固定目录及旧 336 载荷。
- `technical-resample.cjs`、`technical-resample.json`、八份 `technical-resampled-*.png`：整图缩放及原图尺度。
- `technical-audit.py`、`technical-integrity.json`、32 份采纳 mask：源、姿态、原支撑和最终组合独立复现。初始结果状态保留为阶段性状态，最终技术结论见本报告及 `technical-final-receipt.json`。
- `technical-cold.py`、`technical-cold-probe.gd`、`technical-cold-receipt.json`、`technical-runtime-entry.json`、导入/运行日志：完整隔离冷导入、实际入口和自然回待机。
- `technical-entry-collect-se-f01.png`：实际入口 SE F01 的 GPU 截图。

本次支撑重建、输入格比较、最终组合没有待掩盖的 CPU 残差。未宣称每个新帧都独立进行了 GPU 逐像素全矩阵验证，未将数值稳定扩大为视觉通过；八向姿态自然度、连续播放腰髋读感由并行视觉与主 TA 结果共同组成最终验收。
