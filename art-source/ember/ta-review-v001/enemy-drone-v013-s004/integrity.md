# 无人机 v013 s004 静态来源与完整性独立复核

结论：**STATIC_PACKAGE_SOURCE_AND_RIGID_ASSEMBLY_PASS**。本轮未确认来源、切分、复合或审阅入口的 P1/P2。通过范围限于固定包的静态来源、旧图保护、注册及 W/E 近舱刚体组装；造型/方向视觉由独立视觉报告与根 TA 裁决。本结论不代表任何新方向动画完成。

正式依据为 `enemy_drone_seven_directions_v013_s004_2026-10-06.zip`，SHA256 `3a6dc8a5ab9c16dc5e71d083568768ff3cabefae2675d5385e552149acb79342`，2,157,905 bytes。独立读取 ZIP：40 条目、39 manifest 载荷，CRC、逐项 SHA/字节数及集合均通过；40 个活动文件与固定包同字节。catalog SHA `2081e1835f5c3db4f65a43f5c889c0f3725c8b140dfc2415fbb708f0ab6963db`，正式登记 SHA `5c47a91721624f701c0bf16eb7fb5ebc82b96d7ef8bb8f03cfe3e4d1b2acd2a2`。

旧 `neutral_down`、`generated_front` 分别对固定 c002 包的 approved_down/front，SW/SE 对固定 c003 包的两斜前图，**4/4 同字节**，并与当前 copy_path 原件同字节。包内 20 项母稿、原生预装 PNG、登记、脚本、shader 与 prompt 的 SHA 均对 `source_provenance.json` 及原工程文件一致。预装两侧原件通过其 catalog/登记/SHA 绑定：共用 profiles_v006，两个 887 方形源区采用同一各向同性缩放 `26/244×724/887`。包内保留前代高分母稿作为来源，不将其认作正式九张输出。

W/E 逐行重新建立 ownership，x 终点采用实际导出器 `range(x0,x1)` 的半开规则。每侧 16 行、同一 128×128 原生来源，body 为补集，近舱为登记区；不是每舱重新生成或单独拉伸。

|方向|原生实体点|body 点|近舱点|近舱位移|全体注册|近舱遮挡 body 的目的点|独立复合全 RGBA 差|
|---|---:|---:|---:|---|---|---:|---:|
|W|588|350|238|(-3,-4)|(2,2)|86|0|
|E|586|364|222|(3,-4)|(-1,2)|85|0|

两侧源点唯一归属，缺漏/重复源归属 0、画布裁切 0、旧近舱源点遗留在 body 层 0。近舱 RGB 与 Alpha 从原生来源直接整数平移，per-pod scale=1；body/远舱仅受整图注册。近舱在前层覆盖 body 是登记的合法遮挡，不能把源点消失数量误判为缺件。自有 source/ownership/final 8×诊断图确认切区包含近舱顶口、壳壁和下缘；旁侧安装柱仍归机体，未确认误留旧近舱壳片。轴心用 `assembled_axes+全体注册` 重算，与 catalog 相符（浮点输出误差 <1e-5）。

NW/N 由固定高分源与登记的理想 Nearest 逆映射复核：覆盖及实体 RGB 差均 0。NE 的**理想 CPU floor** 与 PNG 有 1 覆盖点、73 实体 RGB 点差；没有将这些写成 CPU/GPU 零差。49 个差点对应边界邻侧源 texel，最大距理想边界 0.0059698153 源像素，余 25 个实体 RGB 点只差 1 个码值。例如输出 `(40,57)` 的源 y=359.999130057，PNG 对应 y=360；`(40,59)` 的 y=382.994030185 对应 y=383；`(87,79)` 的 x=778.003812691 对应 x=777，后者也解释覆盖差。所有差点均找到符合原源的邻侧覆盖/RGB（RGB 最大残差 1），未发现无来源样本。此结果与导出器固定缩放/Nearest 采样相容；本轮没有复跑 GPU 来确定具体驱动取样路径，不将近边界量化差扩展为重绘或造型问题。catalog 对 JSON 的尺度末位及 source_anchor 末位重新序列化差 <1e-12，未改变注册几何。

9 张正式输出全部 128×128、Alpha 仅 0/255，SHA 与 catalog/QA 一致；透明区含隐藏白 RGB，不能误述为所有透空 RGBA0。深/浅底 1×/4×四张九格联系图独立重新合成，全 RGBA 差均 0。共同 ROI `[48,45,34,45]` 的左右两幅 16×观察图也独立复合 0 差，包含 W/E 全部实体范围，没有以裁切掩盖边缘。

本轮不运行 Godot、GPU 或生产生成脚本，也不触碰生产文件。证据为同目录 `binding.json`、`verify_binding.py`、`neutral_left_source_ownership_final_8x.png`、`neutral_right_source_ownership_final_8x.png`；binding 保存 39 清单验证、20 原来源、4 旧包复制、逐行 ownership、遮挡坐标及 NE 具体邻侧采样点，可复算。
