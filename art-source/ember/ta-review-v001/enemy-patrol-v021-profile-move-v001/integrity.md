# 巡逻 P21 v001 W/E 必要技术审查

2026-10-07。**固定包、资源加载和候选动作约束通过；整体仍受新侧腿/靴改变既有身份的 P2 阻塞。** 原始 imagegen、prompt、登记和中性形体差异由 [identity-review.md](identity-review.md) 专项裁定，本报告不以技术一致性覆盖身份结论。

## 固定交付

| 项目 | 绑定结果 |
|---|---|
| ZIP | `enemy_patrol_profile_moves_v021_v001_2026-10-07.zip`；3,688,508 B；SHA-256 `4c907f50f6851787d84e7212a0cd7c64215566baf482a520fde937212db10b61` |
| 清单 | 123 载荷 + manifest =124 文件；ZIP CRC、字节数、全部 SHA 及固定目录原字节匹配。 |
| manifest SHA | `912f40ad1b328773c2cf439f6c06ab1b52c372b6b5c31a541da241984e60bbf1` |
| catalog SHA | `b9d5126648a815db4d8a3d13bfba3d848389ae5695a3cd3ade1089c0eb799480` |
| rig SHA | `1970315ec03ddfb979b4cb9bb812302cdfd211b63dbcb4af6e7e1344505943e1` |
| TRES SHA | `626bf9afb2f9a40ca90ea8074d12194e6b1d3889790363821dee1fd1a348eb90` |

本批只有 W/E 两条新移动 16 帧，保留 S/SE 两条 16 帧；四条共 32 帧。SW/NW/N/NE 的移动不在本包，预览回退中性图，不能把八张中性图计作八向移动完成。证据见 [technical-zip-binding.json](technical-zip-binding.json)。

## 既有资产和候选来源边界

八张 canonical 源母图和八张 `reference` 对照图，均与已通过 S002 ZIP `28951089e1403c65f6a8446aed5f049fdba704809175da36a391c6c5fa1e99a1` 同字节。旧 S 的 8 PNG/atlas 与 v012 原 ZIP 相同；旧 SE 的 8 PNG/atlas 与已通过 pilot 原 ZIP 相同，合计 16 PNG +2 atlas 保持。

**母图文件保持不等于候选新绑定保持。** W/E 的新腿取自一张 imagegen 双侧腿源，同方向分别注册成 near/far 两个物理实例，属于明确的部件结构复用，不是两张独立生成的腿。登记 source SHA 与实际文件一致；每个 near/far 实例各 180 个实体点，实例内分配无遗漏或重复。本检查没有把两个实例的同源复用误写成零重复来源，也没有声称 W/E 对原母图 RGBA 零差。原始生成、注册过程和 W/E 中性改变 209/213 像素的详细范围由身份专项记录。

## 16 个候选姿态的独立约束核对

W/E 的相位表与前 P20 相同。独立步态投影公式对上 16 个 catalog pose 的 hip/knee/ankle/support 及部件变换；所有支撑脚 sole=ground，解剖左右仍按原相位交替。

body、cap 和 boot 的 16 组基底均恒等，仅平移，未发现它们在动作中缩放；短连接件按端点映射，独立端点算术闭合，本批没有折为零的连接段。上述仅说明候选部件在序列中稳定，不说明这套新部件符合既有造型。

原 canonical 的工具/手臂保护区 W/E 各 223/226 个实体像素保留在 body；16 张最终 PNG 对每一保护点按 body 位移追踪，完整 RGBA 差 0。每条腿实例的实际 mask 分区和层次独立解析，未运行生产导出脚本。

全部 32 PNG/四 atlas 按每格 128×128 完整 RGBA 精确相同，登记 SHA、atlas SHA 和 TRES SHA 匹配；二值 Alpha，root=(64,104)，四条 move 都是 8 帧、8 FPS、loop=true。

上述逐项证据见 [technical-integrity.json](technical-integrity.json)，独立脚本 [technical-audit.py](technical-audit.py)。

## CPU 残差与最小完整冷加载

独立 CPU 双精度逆采样的 16 帧模型保留 **18 个 RGBA 残差**：全在 W，F00–F07 为 `6,1,0,2,3,1,1,4`；E 为 0。其中 8 个 Alpha 覆盖分歧，10 个双方均不透明的 RGB 分歧，最大 RGB 单通道差 250。具体坐标及预测/实际 RGBA 均记录，没有为追求零差调整最终素材或掩盖数值；本轮也不把全部差异冒称为已精确证明的浮点取样原因。

从 ZIP 完整解压到无初始 `.godot` 的 `technical-cold-load/`，保留全部交付文件/导入设置。Godot 4.7.2 headless 独立验证 **PASS**：四 clips/32 个实际嵌入 atlas 格完整 RGBA 对原 PNG 一致；预览两个 nearest/centered=false 节点可加载；实际 W/E rig 的 18 张 ownership mask 与独立解析逐像素零差，16 组 pose 与登记在 2e−5 容差内一致。原 123 载荷 SHA 保持，修正后探针 exit 0、stderr 0。

初次从 P20 复用的 TA 探针错误地把预览缓存数写为 12。P21 为比较原设定与新绑定，实际有 **8 original +8 neutral +4 move=20** 项；这与 `preview.gd` 一致。初始 32 格 RGBA 和 16 pose 已通过，仅缓存数量断言失败。只修正 TA 的计数断言后重跑最小探针，未改生产文件；初始 FAIL JSON 和日志保存在 `technical-initial-*`。这项探针修正不属于资产返修。

证据：[technical-minimal-cold-load.json](technical-minimal-cold-load.json)、[technical-cold-receipt.json](technical-cold-receipt.json)、[technical-cold-probe.gd](technical-cold-probe.gd)。没有独立重跑 GPU、自然播放器或切向矩阵。

## 作者记录和最终范围

作者 `gpu_roundtrip.json` SHA `a1eadba3fe2db1cbe5fa5080f2ca6898b316d748e60353aac3359b5d85194cb3`，`runtime.json` SHA `c2c22046eb57b9957a726785d1f020370d180e799add400a587218a9f44e92b5`。48 条 GPU、8 个播放器和 8 次切向记录与当前 catalog 绑定，仅核作者记录；不冒称 TA 重跑这 48 条 GPU。

本报告证明这套候选可以按登记稳定加载和播放所需数据，并未解决既有侧腿/靴形体被替换的身份 P2。原 S/SE 的批准范围保持；W/E 候选须按根回执返修，不能据本技术通过补记为八向全部移动已通过。
