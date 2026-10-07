# C24 v001 攻击／死亡独立技术复审

2026-10-07。结论：**RETURN_P2_VISIBLE_BLADE_PATCH_SPIN**。ZIP、原源、归属、动作数学、PNG/atlas/TRES 和最小完整冷载通过；**NW 锯盘把原遮挡缺口带着自转，形成开口弯钩，不能凭“与当前 rig 配方一致”放行**。本技术线支持该 P2；最终视觉回执由主 TA 合并。E 平切边作为同机制附例，NE 远前脚没有以点数或连通计数直接判退。

## P2：可见锯片裁片不能当完整转盘自转

`rig.gd` 的 `owner()` 把当前源图中工具的可见像素分配给 `saw` / `saw_blade`；111–115 行再将这个固定可见片绕 hub 做投影自转。既没有一次性补齐原被遮挡的盘体，也没有把静态遮挡层从盘体上分离。其遮挡缺口和裁片边界随片转入自由外轮廓。

NW blade 实际只有 94 个源不透明像素。独立查看 source 与 attack F03／death F07，F03 盘顶开口并读成弯钩。四个明确的透明缺口位置逆映射如下：

| NW attack F03 输出透明位置 | blade 逆映射源位置 | 原源实际归属 |
| --- | --- | --- |
| `(87,75)` | `(83,78)` | saw 柄 |
| `(88,75)` | `(83,77)` | saw 柄 |
| `(85,76)` | `(83,80)` | saw 柄 |
| `(86,76)` | `(83,79)` | saw 柄 |

源中这些位置有实色，却不属 blade；其余开口点逆映射到源的透明区域。说明当前 blade 是已经裁去遮挡区的局部片，不能作为完整盘体做自由自转。E 的 blade 有 141 源像素，F03 左下边读成平直切边，也应随同复核。`technical-defect-trace.json` 中声明椭圆内的透明计数仅用来定位，**不是完整盘体真实缺失像素数，也不规定新画一个椭圆盘**。

最小修复方向：保留角色和工具原身份，先建立一次性的完整盘体与独立遮挡/轴柄关系，或采用适合当前可见片、不会旋转遮挡缺口的动作表达；固定源后重导相应帧。不要逐帧补边、硬画新线或靠调参数掩盖开口。复审应重点看 NW F01–F03 与死亡末帧、E 同机制边缘及工具遮挡。

证据：`technical-blade-source-frame-8x.png`、`technical-defect-trace.json`，以及视觉线完整 98 帧证据。

## 包体、固定源及旧动作

- ZIP `enemy_cutter_attack_death_v024_v001_2026-10-07.zip`，3,802,515 B，SHA256 `c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c`。
- **326 payload + manifest = 327 文件**；CRC、成员集合、路径边界、逐项大小/SHA、冻结目录字节绑定通过。catalog SHA256 `444e71fa6255dc25e5eb824a882c58bb07f94ba444364df20eac1039b1e99a7c`。
- 六方向源 PNG 与已过 C22 固定源逐字节一致；SE 与 HC 原 ZIP `output/enemy_cutter/rig_neutral_down_right.png` 逐字节一致，SHA256 `79e56cd5438f5b78d4dad555e9a364c359635b8cb8b58c6b1790cc166679b462`，也等于本包 `provenance/approved_hc_neutral.png`。SE 是过审的实际装配图，不能称未装配原设计稿。共同 provenance 文件另与 C22 比对。
- 旧 S 攻击/死亡 **14 PNG + 2 atlas** 与 v012 原 ZIP 字节相同。
- 新七向各 attack 6 帧、death 8 帧，14 clips / 98 帧；含旧 S 后 **16 clips / 112 帧**。128×128，root `[64,104]`，10 FPS，单次播放。全部 PNG/hash/atlas格RGBA/binaryAlpha通过。attack F00=F05，death F05=F06=F07；新帧最高不透明下界均不超过 y104，旧 S 攻击保留原 y108 工具前伸边界。

## 独立节点、归属、轨迹和冷载

完整 ZIP 新解压后使用 Godot 4.7.2 headless import，实际加载两个 preview actor、SpriteFrames 的 16 clips / 112 格，逐格嵌入纹理 RGBA 与 PNG atlas 核对。随后实例化七个原 rig，读回 **66 个 actual ownership mask、24 组连接 UV、98 poses、pivot/z/Nearest/sensor power**。独立数学模型与实际节点、catalog 一致。导入 6.203 s，probe 3.727 s；退出码 0，stderr 0 B；原 326 payload SHA 全部未变。

来源/归属模型独立复算了 overrides → tools → protected body → leg/foot 的优先级；每个源像素恰有一个部件 owner，与实际 mask 一致，实际 `qa/parts` 的所有可见 RGBA 均为对应源像素。七张 bind 和每个新动作 F00 与各自固定源全 RGBA 零差。

attack 机身 y 为 `[0,-1,-1,1,0,0]`，挥动权重 `[0,-0.35,-0.6,1,0.3,0]`，F03 最大挥动，F05复位。death 机身下沉 `[0,1,2,4,6,7,7,7]`，腿壳围绕注册踝轴按 `[0,5,12,25,42,55,55,55]` 和固定方向系数折叠；脚节点始终 identity。盔甲、柄和腿壳保持正交单位基；blade 使用声明的固定投影椭圆度量旋转，det=1，但屏幕基并非始终正交，不能把它写成“全部部件纯屏幕刚性旋转”。

SW/SE 的传感器区域按 death power `[1,0.6,0.2,0,0,0,0,0]` 变暗，是明确的 shader 效果，不能宣称所有动作 RGB 永远不变。N 的 tools 列表为空，只表现机身预备和回位；没有凭空补出被遮挡的锯盘，不能声称 N 具有可见挥锯。

证据：`technical-prepare.py`、`technical-audit.py`、`technical-zip-binding.json`、`technical-minimal-cold-load.json`、`technical-cold-receipt.json`、`technical-integrity.json`。

## 保留的数值与接地边界

独立 CPU 最近邻/Polygon2D 模型共保留 **84 个 RGBA 像素事件残差，其中 21 个 Alpha**。NW death F05–F07 每帧 18 点为同一末姿态重复，主要在 45° 采样边界；没有抹平或修改输出追到 CPU 零差。17 个 CPU 刚体底图外的实际像素不符合连接原色/四边形，保留为采样残差，未冒称新增连接。另有 **243 个事件**落在注册连接四边形内且命中其原 2×2 色源；这是相对 CPU 刚体底图的连接来源核查，不是“没有新输出像素”。完整坐标及 CPU/实际 RGBA 均留档。

24 组连接中，23 组 2×2 色源有 4 个不透明像素；**SE front_left `[77,86,2,2]` 仅 1 个褐色 `(161,146,131,255)`，其余 3 个透明**。这组在全部 14 新帧的刚体层外独立暴露统计为 0，视觉线也未见拉条；属于来源/措辞边界，不能统称全部都是实心蓝灰暗轴。首次沿用“全部源均4不透明”的审查假设触发断言，现已按真实源记录，未改生产源。

21 个名义非空 sole ×14 帧 =294 处登记探针：262 处 CPU 顶层为对应脚，32 处不是对应脚；不能声称 294 处都看见脚掌。尤其 SE 两前脚的名义 sole 本身并未落在 actual foot 上：`front_right [52,94]` 上方 `(52,93)` 原 owner 为 `saw_blade`；`front_left [81,91]` 上方 `(81,90)` 原 owner 为 `claw`。实际两脚 mask 分别为 8 / 6 像素，bbox `[48,90,51,94)` / `[78,87,80,91)`。SE rear_left 实际脚最低 y80，也不是名义 sole y79 的最低行。建议随返修修正/区分名义登记与可见探针；该数字仅用于登记且变换固定，不能拿锯片/夹爪颜色当承重脚证据。

NE death F04–F07 的左上暗/黄铜小块已溯源为固定 `front_left_foot`，源/输出约 `(41..44,77..80)`。F04 脚 `(44,78)/(44,79)` 分别与下降 body `(45,78)/(45,79)` 直接4邻接；F05–F07仍保留 `(44,79)`→`(45,79)`，两端 RGBA 来源均核实。当前不以这块小、在画布上偏高就判浮腿；视觉判断另行合并。

## 作者证据及回执范围

作者 **210 GPU记录、32 player、16 switch** 的 JSON 与当前 catalog SHA 绑定，状态/条目数/单次结束、末帧停留记录一致；本线未独立重跑整矩阵，未把作者结论代称本线验证。最小冷载通过不能覆盖上述 NW 工具形状 P2。

本次冻结包、生产目录均保持未改；返修及正式通知由主 TA 汇总。工具可见片修复前，C24 保持未通过。
