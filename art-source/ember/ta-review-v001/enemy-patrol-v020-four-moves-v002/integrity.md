# 巡逻 P20 v002 技术返修复审

2026-10-07。**两项 NE 来源/分区技术返修已闭合，固定包、48 格导出及最小独立冷加载通过；最终美术裁决以根回执和视觉报告为准。** 本轮仍是 SW/NW/N/NE 四条移动 32 帧的候选复审，加保留旧 S/SE 16 帧；本包没有 W/E 移动。

## 固定身份与范围

| 对象 | 独立绑定 |
|---|---|
| ZIP | `enemy_patrol_four_moves_v020_v002_2026-10-07.zip`；3,225,225 B；SHA-256 `7bc4982abe5fdcfb7a205ddae599cffade57961b347fcd6200bb2f59a1f244a7` |
| 清单 | 144 载荷 + manifest =145 文件；ZIP CRC、全部字节数/SHA、固定目录逐字节相同。 |
| manifest SHA | `30d02a0928f83ff2c964abfff06f58147f377f76bd23fbdc3ed45cf83addc8ba` |
| catalog SHA | `6ff3f3d757485709d27f4c358bc113cbe3190f87e65464d9ae4071f1ac122f81` |
| rig SHA | `2a9aee21b1cbd09fd1bd013c8f4751beb543e80edf6bcf148c1bc866c858b0c5` |
| TRES SHA | `34f71bc413c5a1215dc4faefc1f02b990c7cc4fedfd7791551c6c8bed731116c` |

使用完整 ZIP 分别建立只读分析副本和新冷加载副本，没有执行作者构建/修图脚本。前版正式返修回执及真实源路线保留。详见 [technical-zip-binding.json](technical-zip-binding.json)、[technical-prepare.py](technical-prepare.py)。

## NE 两项修复的实际证据

与 v001 逐字段比对，`rig.json` 仅 NE 部件的 `polygon`/`exclude` 改变。`rig.gd`、shader、8 张源图、所有骨点/端点/z 层次/heading/腿长登记/相位及全部 catalog pose 记录保持不变；其余三套新方向 config 全部相同。没有更换角色源或改源 RGB。

**原 15 个浅色甲片源点全部归回刚性 body。** 八帧中这 15 点都只随 body 的整数 y 位移，在实际最终 PNG 上逐 RGBA 保持，没有被 `left_thigh` 轴向复制拉长。该连接片现在恰好只含原 `(57..58,80..84)` 的 10 个深色实体源点，没有浅甲。新旧源图相同，修复的是源归属，而非逐帧重绘浅色表面。

**原重复 20 点现各有唯一归属：6 点 body、9 点 left_cap、5 点 left_foot。** 四套源 mask 全部无原实体遗漏或重复。除计数外，独立按真实渲染层次逆采样追踪这 20 点的八帧最终顶层路线，每个原点每帧最多一处实际可见，所有命中点都与最终 PNG 的原 RGBA 一致。例如：

| 原点及 RGBA | F02 唯一路线 | F03 唯一路线 | F04 唯一路线 |
|---|---|---|---|
| 浅甲 `(62,82)` `[192,182,169,255]` | body→`(62,82)` | body→`(62,81)` | body→`(62,82)` |
| 黄铜 cap `(62,89)` `[113,61,2,255]` | left_cap→`(62,89)` | left_cap→`(60,90)` | left_cap→`(60,91)` |
| 靴边 `(62,96)` `[109,127,143,255]` | left_foot→`(62,96)` | left_foot→`(61,97)` | left_foot→`(59,97)` |

v001 中这些 cap/靴点经 right_cap/right_foot 再显露一次的路线已消除，浅甲点也不再沿可伸缩 thigh 反复采样。所有 20 点、八帧的完整路线和实际颜色均在 [technical-ne-revision.json](technical-ne-revision.json)，独立脚本 [technical-ne-revision.py](technical-ne-revision.py)。这些事实支持返修闭合，但最终轮廓/承接仍由视觉逐帧审查决定。

## 影响范围与导出

NE F00–F07 的实际 RGBA 改动数为 `40,42,15,57,57,40,44,39`，合计 **334 像素次**。其余 **40 PNG / 5 atlas** 与 v001 完全同字节。此前通过的 16 张 S/SE PNG 及两个 atlas，也分别对回原 v012/pilot 固定 ZIP 一致；8 张源图与已过 S002 固定 ZIP 和输出中性图同字节。

全部 48 PNG 与六 atlas 逐格完整 RGBA 一致、SHA 正确、二值 Alpha；128×128、root=(64,104)。六个 TRES move 均 8 帧/8FPS/loop，W/E move 缺席符合本次申报。四向中性绑定图对源图 RGBA 零差。

独立重算改动的 NE 八帧姿态、支撑与端点，和登记一致；body、cap、靴为恒等基底平移。工具保护 140 个实体点全归 body，NE 八帧实际输出原色无差。其他三向源/参数和结果均未变，继承 v001 的技术检查；本轮没有无谓重算其 24 帧完整 CPU 光栅。

## CPU 模型残差与冷加载

新 NE 八帧独立双精度 CPU 逆采样与最终 PNG 共 **17 个 RGBA 残差**，逐帧 `3,1,0,0,8,3,2,0`；其中 9 个 Alpha 覆盖分歧，8 个双方均不透明的 RGB 分歧，最大单通道差 199。坐标/源 UV/预测与实际值保留在 [technical-pixel-integrity.json](technical-pixel-integrity.json)。不宣称 CPU 全零差，也不将残差全归因为已证明的某一种浮点机制。

对字节、配置均未变的 SW/NW/N，沿用 v001 已记录残差 34/9/0；若汇总四新向可得到 60 个残差，但这不是本轮重新光栅了全部 32 帧。N 原 F02/F06 的短连接投影退化也未变化，既有视觉非阻塞判断不扩大为“所有连杆永不退化”。

**完整隔离最小 cold PASS。** 直接从固定 ZIP 完整复制 145 文件，无初始 `.godot`，保留原有全部导入设置；Godot 4.7.2 headless 导入 5.171s、探针 1.778s，均 exit 0、stderr 0。原 144 载荷导入后 SHA 全保持：

- 六条移动 / 48 个 atlas 资源格完整 RGBA 对原 PNG 一致，region、时长和播放参数正确。
- 八张中性依赖和预览两个 nearest/centered=false 节点实际可加载；14 个缓存项是八中性加六移动。
- 实际 NE rig 读回 9 张 ownership mask，与独立 mask 逐像素零差；8 组实时 pose 与登记最大误差 0。

见 [technical-minimal-cold-load.json](technical-minimal-cold-load.json)、[technical-cold-receipt.json](technical-cold-receipt.json)，探针 [technical-cold-probe.gd](technical-cold-probe.gd)。本次没有 GPU 截帧、自然播放器或切向矩阵重跑。

## 作者证据边界

作者 `gpu_roundtrip.json` SHA `613d6f616aee85d5b55d04c8201064560e83bb2a77974116859b02799507c355`；`runtime.json` SHA `aaaa7331184f24d6f5ae244d5ec780cb5c09eff0a29ac40a60aa409ce5683929`。两者绑定本次 catalog，80 项 GPU、12 条播放器、8 次方向选择记录结构与所报 PASS 保持。仅核作者证据绑定，没有冒称 TA 独立重跑这些矩阵。

本报告只裁定限定技术返修已闭合。是否放行四条新移动，以根最终回执为准；此包不能单独证明巡逻八向移动或全部动作已经完成。
