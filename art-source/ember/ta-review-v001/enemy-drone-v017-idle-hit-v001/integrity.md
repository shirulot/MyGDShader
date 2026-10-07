# 侦察机 idle/hit v017-v001 独立技术审查

日期：2026-10-07（Asia/Irkutsk）。结论：**FIXED_SOURCE_EXPORT_AND_MINIMAL_COLD_PASS**。本技术范围未发现 P1/P2。七个新方向各 idle/hit 共14条56帧的来源、局部风口绑定、刚性位姿、导出及冷资源加载通过；旧 down 两条8帧保持。视觉与最终 TA 综合验收分别记录，不扩张到移动、攻击、死亡或主玩法集成。

## 固定包与来源

- ZIP：`art-source/ember/deliveries/enemy_drone_idle_hit_v017_v001_2026-10-07.zip`。
- SHA256：`19b3ba844e5df945292953520fa17a3c5a8a0c8bbf7a852a8fdd56d8e3773d05`；1,899,538 bytes、212条目/211清单载荷。ZIP CRC、清单集合/字节数/hash，以及活动 review 目录全部212文件与ZIP同字节，均独立核验。
- s004 静态固定包 SHA256 `3a6dc8a5ab9c16dc5e71d083568768ff3cabefae2675d5385e552149acb79342`：七张新向机壳 source 与各已通过 neutral 同字节；包内 s004 manifest/registration provenance 也与原包同字节。
- v011 转子固定包 SHA256 `13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e`：`source/rotor_well_master.png` SHA256 `8824eeff102796d523fa8fab1f17f90c5716b7f34097987c0d5ea8151c2a3a94`，图与原提示词均同字节；不使用 v011-r1 探头实验。
- v012 正向固定包 SHA256 `42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe`：idle_down/hit_down 的8 PNG、2 atlas及2 reference atlas逐字节保持。source/down.png保留已过 idle F00；八张 output neutral也均与本包各自 source 同字节。
- SOURCE_RECEIPT 中 s004/v012/v011/SE pilot 四来源包hash、八机壳和转子源hash都核对。正式画布128²/root(64,104)；rig.json动作参数仅在 actions.idle/hit 内，无顶层 frames/FPS/loop/移动遗留定义。

## 中性绑定及刚性动作

七向各两风口用固定中心、radius(6.5,4.5)、相反 spin(+1/−1)登记。独立按像素中心计算两椭圆，共178位置；N中性实际改变177，其余每向178，**两风口以外源RGBA变化0**。idle/hit首帧同中性，包内 qa/bind 与实际两动作F00一致。177不是漏点要求：范围内有一处原RGBA与绑定结果相同。

动作清单与每条catalog逐项一致：idle4帧@4FPS循环，Y=[0,−1,0,+1]、roll全0、转子角[0,22.5,45,67.5]；hit4帧@12FPS非循环，body_y全0，绕(64,67)整机roll=[0,−6,+3,0]、转子角[0,15,8,0]。固定机壳Sprite包含风筒、杆和探头，它们共同受唯一body变换；无逐帧重新取源、每舱缩放或支杆变形。

独立复算56姿态的body矩阵、旋转中心/原点和两风口世界轴。与序列化的Godot float元数据最大差 `1.076e−5`；双轴距离保持、body为单位正交旋转，没有轴向缩放。转子世界基底按 **body R × 椭圆 S × 自身平面 Rspin** 组成，旋转发生在投影前，井底不继承转子角。两舱解剖归属和正反旋转登记不随帧换位。

28张新增idle帧，以及hit F00/F03，机壳区域按声明变换与理想源采样全RGBA一致；倾转hit F01/F02的最近邻边界差单列在下一节。八向hit F03与F00实际全RGBA一致；七新向hit F00与idle F00也全RGBA一致。

## 实际PNG、内嵌资源与CPU差异边界

64 PNG均128²、二值Alpha且可见范围在画布内，与16个512×128 atlas对应区域全RGBA一致，文件hash/FPS/loop/帧数与catalog一致。TRES内嵌16张Image的实际RGBA与16atlas一致，无外部资源；64张黑/白底1×/4×联系图独立从atlas复合和Nearest放大，均全RGBA 0差。本轮不以连通域、像素数量或自动检查替代动作视觉判断。

CPU独立采用双精度逆变换、母图Nearest取样与两层固定转子/井底取样，和56张新增PNG总计有 **1321 次帧内像素RGBA差**；这是跨帧累加，不是1321个独立画布坐标。分项为716次覆盖RGB最多相差1码值，603次可由近邻源texel解释，2次风口遮罩阈值Alpha边界；603次近邻中的2次也涉及Alpha，所以Alpha差共4次。逐点记录均已保存，没有未归因条目。

- 每新向idle F00…F03差数32/25/24/25，均在风口内，Alpha差0。七向hit F00/F03各32次风口差，实际首末PNG完全恢复。
- 倾转帧的其余差进入逐点源定位。整体风口外共29次：25次RGB与4次Alpha，均在hit F01/F02；不同方向的若干RGB点共用输出(68,61)、(58,62)、(39,63)或(66,57)、(62,76)，逆映射贴近源整数纹素边界。
- Alpha差具体为 W/E hit F01输出(69,80)：源y=81.000952，实际读到邻行不透明源像素；NW/SE hit F02输出(75,62)：位于风口遮罩的接近阈值位置，实际PNG透明。它们是理想CPU与已提交渲染的边界差，不代表正式PNG出现连续Alpha。
- 能解释实际覆盖RGB的最近相邻源texel距离最大 `0.0697471 texel`。1码值/邻源/遮罩边界分类是基于实际差点的诊断，不是另跑GPU的结果，也不将CPU标为0差；最终是否产生可见闪变由独立视觉播放裁定。

## 制作方证据与独立冷验证

catalog SHA256 `0bbf66dda8347f2535b116f21718a2dde4d85d96bf210674445e45295377161b`。四QA（gpu_roundtrip/runtime/pixel_audit/pose_audit）hash及各自catalog引用已绑定固定包。

制作方GPU报告为112个新帧×黑白底记录，live rig/PNG及TRES/PNG皆0差，另8个旧down记录仅TRES/PNG对照。记录集合/每方向帧序已核对；32个正常/1FPS播放器和16个frame2/progress.375切向记录也绑定当前catalog。**包内没有这112次独立逐帧framebuffer原图，本轮只核报告和正式联系图，不称保存112张GPU图片，也未重跑作者完整套件。**

包外作者冷回执的ZIP绑定相同，记录120核心源保持。独立对照其当前cold目录与本ZIP的211载荷，210同字节；唯一qa/runtime.json仅elapsed_ms从5242变5243，其余字段一致。120核心名单未在回执逐项枚举，因此不伪称按该名单独立重跑120项。作者cold日志字节/hash保存在技术绑定数据中，与本轮自有日志分开。

TA本人从固定ZIP独立解出 `technical-cold-project`，初始无.godot缓存，实际使用Godot 4.7.2-stable Steam headless导入并运行自有探针：**25/25 PASS**。范围为内嵌资源加载/16 clips/无外依赖3项，16条各自FPS/loop/四切片/实际内嵌atlas全RGBA关联16项，场景/Nearest2项，idle/hit两次NE暂停frame2/.375切换2项，rig源依赖/实际hit旋转支点2项。导入5.415s、探针1.384s，两调用exit0、stderr0B；冷导入后211原载荷hash全保持。

本轮冷验证没有GPU framebuffer、自然循环、32播放器或16切向全套复跑。独立证据为 `technical-binding.json`、`technical-cpu-boundaries.json`、`technical-cold-receipt.json`、`technical-cold-probe.json`、`technical-verify.py`、`technical-cpu-explain.py`、`technical-probe.gd`、`technical-cold.py` 和 technical-import/probe stdout/stderr。生产脚本未执行，生产素材、缓存及历史回执未修改；浏览器未操作。
