# 重装机八向移动 v014-v001 独立技术审查

收口：2026-10-07，Asia/Irkutsk。正式包与起始证据文件名仍为 2026-10-06，不追溯改写日期。

结论：**NEEDS_REVISION / P2：N 向左履带透明源 RGB 被搬成可见白块。** 包完整性、来源、旧动作保护、嵌入资源与最小冷加载通过，但当前整批不能正式通过。返修限定 N 的循环采样；SW/W/NW/NE/E 没有本轮确认的同类采样污染。六向动作视觉由独立视觉与根 TA 报告另审，本报告不把源/哈希或连通数量视作美术通过。

**P2 的实际像素证据。** N/up 左窗口 `(28,85)`、cross_width=16、period=16、sign=-1。原图边缘 `(28,98/99/100)`、`(29,99/100)` 为透明 RGBA `(255,255,255,0)`；shader 只循环其 RGB、保留目标原 Alpha，因此这些隐藏白色被搬进原本实体的履带，输出为 `(255,255,255,255)`。F01–F07 共 **33 次** 可见污染。例：F01 `(28,96)`←源 `(28,98)`，F02 `(28,94)`，F03 `(28,92)`，F04 `(28,90)`，F05 `(28,88)`，F06 `(28,86)`；原生帧 8×图上能看到白点/短白边随履带向上滚动。这是实际不透明白块，不是对 Alpha0 隐藏 RGB 本身的新门槛，也不是固定高光或 CPU 算法差。

自有图 `up_left_tread_sampling_8x.png` 使用固定原位置 ROI `(24,82,32,32)`，F00→F07 从左到右，无 bbox 居中；`binding.json/P2_up_tread_white_sampling` 保存33项源/目标坐标与 RGBA。独立 RGB 循环重建完全复现这些正式输出，确定是有效采样域混入透明边缘，而非截图背景差。

最小修法：仅 N 左窗口避开不完整的 x28/x29 边缘列，或登记完全有效的实体源采样域；保持 16px 周期、2px/帧、后向反流、原源和固定框/侧甲/支点。禁止通过搬 Alpha 删除目标实体或重绘整帧掩盖问题。重新封 N 八帧、atlas、TRES及相应 catalog/QA；原 v001 保留，其余方向和旧 S/SE 16 帧冻结。

正式依据 `enemy_heavy_eight_moves_v014_v001_2026-10-06.zip`：SHA256 `dbad34a8845cce2a648d904790f5abd34fd64abbb5762f50d458f595e648c9ae`，3,906,157 bytes，160条目=159载荷+manifest。独立 CRC、集合、159项SHA/字节数及活动160文件全同字节；自有冷工程从此固定包安全解开，初始无 `.godot`。来源8PNG与 SOURCE_RECEIPT、已过 static_preflight_v001 冻结 catalog 和原工程PNG全部同字节。高分母稿、prompt、registration 与原工程及冻结登记同字节。旧 down 对 v012 固定包、旧 down_right 对 HCv001 固定包，分别 8帧+atlas 全同字节。

六个 F00、qa/bind 和各方向静态源全 RGBA 差 0。固定 ownership 对实体点唯一分配，无漏/重复；周期窗口互不重叠。独立逐像素重建固定 tracks + body 在 F02/F06 下沉1px + 限制窗内原 RGB 循环。W、NW、N 各8帧重建全 RGBA 差0；SW/NE仅F02/F06各1点、E仅F02/F06各11点，合计26点 RGB 差，**所有方向 Alpha差0**。

上述 **26点与白块 P2 分开**：全在升降帧的精确多边形边界上。SW/NE为目标 `(46,81)`，E为 `(74,71)` 及 `(79,73)`→`(88,82)` 斜边；对应升降源像素中心恰在线段上。PNG 的 RGB 可精确追到同一原图当前行或升降后的前一行，没有重绘、无源颜色或轮廓断裂。自有 headless Geometry2D mask 与理想 CPU 在这些点仍未复现原 GPU 的 body/track 覆盖选择，故**没有宣称全部 CPU/GPU 全 RGBA0**；具体源行、边段、RGBA及这项限制均记录在 `cpu_26_polygon_edge_classification`。本轮不扩 GPU 实验，也不把合法层叠边界选择升级为第二个 P2。

实际纹理流向按目标特征位移验证，而非混淆取样坐标方向：SW 两端面向下2px/帧，NW/N/NE向上2px/帧；W上段向左、下段向右；E上段向右、下段向左。周期均16，phase=2f，F07→F00继续2px并模16闭环。侧向轮盖和侧甲位于固定 track ownership，窗仅上下窄条，未登记轮盖旋转；履带框/支点不随 body 下沉。只有 N 左窗有33个采到透明源的实体目标，其余五向无此项。实际动作可读性以视觉报告为准。

64PNG与8atlas全 RGBA差0，全部128×128、Alpha0/255、无画布边界实体裁切。TRES内8个Image原始字节逐一对应8atlas，64 region/duration、8动作8FPS/loop绑定；冷加载进一步实际确认每条动画所关联的内嵌 atlas，不仅检查其数量。catalog SHA `4322e0313b81881cebd8de296790c2dcbca3878a0f391d8b1b9882f5bf47f6aa`，rig/TRES/各atlas及64帧SHA相符。32张黑白1×/4×联系图、6张共同履带ROI独立复合全 RGBA差0。

作者记录另列：96组仅为48新帧×黑白底的 live rig/PNG 与 TRES 对照；16旧帧记录只有 TRES/PNG。全部与本 catalog/manifest 绑定，不能将其说成64帧live rig重跑。16播放器组8FPS/1FPS见全八帧并完整循环、8切向记录PASS，仅复核记录，非TA本轮全套重跑。外置 `cold_receipt_v001.json` SHA与固定包SHA/159载荷对应；当前制作方冷目录159项中158同字节，唯一 `qa/runtime.json` 仅 elapsed_ms 9373→9346，catalog/循环/切向等字段均同。回执“110核心保持”没有成员清单，报告不伪造其集合；本轮独立比较提供更明确的158+运行时间字段边界。

TA实际最小冷验证：Godot 4.7.2-stable Steam、headless，冷导入5.318s，资源/场景/定点属性及 Geometry2D 探针1.483s，**95/95 PASS**，均exit0/stderr0。包含8动作属性、8实际内嵌atlas RGBA、64region/duration、独立打开场景、Nearest、SE/NE保留F03+0.375相位以及六方向CPU归属mask证据；159原载荷导入后SHA全保持。**没有GPU framebuffer、自然循环、作者96GPU/16播放器/8转向全套复跑。** 冷加载成功不撤销已经确认的白块P2。

本地6106服务目录 `heavy-eight-moves-v014-v001` 的 index/catalog/N atlas 与固定包对应项同字节（只读本地文件绑定，无网络请求）。正式运行可从冷包独立打开，不依赖上游 build_spec.py。返修后需新的固定包与定点证据。

证据位于本目录：`binding.json`、`verify_binding.py`、`finalize_binding.py`、六张 ownership8×图、`up_left_tread_sampling_8x.png`、`cold-probe.json`、`cold-receipt.json`、自有探针/运行脚本、Godot归属mask及stdout/stderr。生产只读。根TA已收到明确P2坐标。
