# 旧 collect 膝盖用户反馈：独立视觉预检

2026-10-07。**反馈可复现，旧 collect F01/F02 的膝部姿态需要重新修正和验收。** 问题主要是屈曲方向及上下腿的体积/朝向不协调；肢体保持连接、脚点稳定或两帧复用相近姿态，都不能抵消这种异常观感。此处不对在制 v012 作 PASS 或正式候选结论。

## 旧帧绑定与目视范围

仅读已冻结 C2 rc02 ZIP `robot_eight_way_v011_phase_c2_rc02_2026-10-07.zip`，SHA256 `64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b`。核了八向 collect 共 32 张 PNG 的 metadata SHA 与当前固定目录字节。原画布为 64×96。

直接复用旧 TA C2 rc01 的现成联系图：七向原生浅深底、七向完整浅底 4×、含 SW 的浅深 4×比较，以及 S/N/NW/SE 的关节浅底 8×。旧证据的每张 collect PNG 在腿部 ROI `[12,56,50,82)` 与 rc02 完整 RGBA 相同，因此下面引用的是当前冻结旧帧的腿部现象，不是已修掉的 SE 肘部暗边问题。绑定明细见 [triage-binding.json](triage-binding.json)，核验脚本 [triage-bind.py](triage-bind.py)。没有读取或评审在制 `revisions/collect-knee-v012`。

## 可定位现象

表中坐标是原画布的复查 ROI，描述可见轮廓位置，不把 ROI 内每一像素都登记为错误。

| 方向／帧 | 目视事实与复查位置 |
| --- | --- |
| **S / down F01、F02** | 相对 F00，身体仅轻微下移，左右膝区却明显横向偏斜；大腿/膝甲的斜面向外展开，小腿斜面再折回靴位。两条腿出现较急的相反折向，难读成同一个膝轴上的自然下蹲。重点 `x17..46,y58..75`。 |
| **N / up F01、F02** | 背面原来较连贯的上下腿方向变成膝区外摆、小腿再向内折回，浅甲边缘像从直列中拧出一角。两膝下方的横向突出尤其显眼，重点 `x17..45,y58..75`。 |
| **NW / up_left F01、F02** | 画面左腿最明显：大块膝/大腿甲转成斜向展开的面，下方窄暗接续与小腿方向相反，整体像关节折过去；画面右小腿也明显斜折。重点左腿 `x16..32,y57..75`，右腿 `x33..45,y60..76`。 |
| **SE / down_right F01、F02** | 画面左侧膝甲斜向翻转，向下的小腿甲折回固定靴体；右侧膝到踝也出现急折，左右甲面朝向与上腿不协调。重点 `x16..47,y58..76`。与此前外肘 `(14,52..54)` 修复是不同问题。 |
| W / left F01、F02 | 侧面原来较直的膝—小腿轮廓被压成方向相反的短斜段，在靴上方呈钩状折返；与手部重叠使体积更难分辨。重点 `x21..35,y60..77`。本预检不在遮挡不足的条件下断言具体哪根骨轴反转。 |
| E / right F01、F02 | 与 W 类似，膝区外轮廓伸出，小腿再折回靴上；局部锯齿和夹角使其读作压皱/拧折，而非明确的膝关节屈曲。重点 `x27..43,y60..77`。 |
| SW / down_left F01、F02 | 原已过 C1 的采集样例也有同类轮廓：膝区斜甲与胫段在靴上方形成急折，不能作为豁免其他方向的动作范本。重点 `x17..43,y58..76`，手与工具遮挡区域需在修正版继续独立看。 |
| NE / up_right F01、F02 | 膝下斜面和靴上连接相对 F00 出现横向偏折，画面右腿尤其有斜甲与下腿转向不一致的读感。强度低于 NW/SE，但属于本次应随八向一起复查的姿态问题。重点 `x20..44,y58..76`。 |

最强定位证据为 S/N/NW/SE；W/E、SW/NE 的遮挡不同，不把八向机械地视为同一幅度、同一骨段的扭转。F01、F02 都出现同类不自然姿态，此表不声称它们全图或整个下半身逐像素相同：手、工具和局部重叠有差异，绑定 JSON 保留了包含这些区域的差异坐标。当前主问题也不应仅描述成随机“AI 闪帧”——即使每次稳定复用这个姿态，膝部动作设计仍然不自然。

## 现成证据

- [七向原生浅底](../robot-v011-phase-c2-rc01-independent/visual-new42-native-light-1x.png)、[原生深底](../robot-v011-phase-c2-rc01-independent/visual-new42-native-dark-1x.png)。列 I00/I01/C00/C01/C02/C03，本次重点 C00→C01/C02。
- [SW 与 S/N/W/E 采集浅底 4×](../robot-v011-phase-c2-rc01-independent/visual-c1-sw-new-collect-comparison-light-4x.png)、[深底 4×](../robot-v011-phase-c2-rc01-independent/visual-c1-sw-new-collect-comparison-dark-4x.png)。
- [S 关节 8×](../robot-v011-phase-c2-rc01-independent/visual-joints-down-light-8x.png)、[N 关节 8×](../robot-v011-phase-c2-rc01-independent/visual-joints-up-light-8x.png)、[NW 关节 8×](../robot-v011-phase-c2-rc01-independent/visual-joints-up_left-light-8x.png)、[SE 关节 8×](../robot-v011-phase-c2-rc01-independent/visual-joints-down_right-light-8x.png)。
- [NW 完整 4×](../robot-v011-phase-c2-rc01-independent/visual-full-up_left-light-4x.png)、[NE 完整 4×](../robot-v011-phase-c2-rc01-independent/visual-full-up_right-light-4x.png)、[SE 完整 4×](../robot-v011-phase-c2-rc01-independent/visual-full-down_right-light-4x.png)。

## 归因与后续验收边界

制作方反馈的“平面两骨 IK、锁脚、下压时外推膝甲”是主 TA 转交的排查线索。本预检没有读取或验证求解器代码，因此不将该机制写成独立证实的根因，也不以此确定唯一修法。

修正版应首先证明：F00→F01 的膝部屈曲方向与该朝向的髋/踝投影协调，膝甲有稳定的前后面和合理体积，小腿接续没有突然反向拧折；F01/F02 保持时不能靠手或工具遮住问题。原生、4×及正常/慢速播放都应核看，而不是只复验连通、足点、像素差或引擎读回。

这是对既有通过范围的用户反馈复审记录，说明此前对膝轴与上下腿朝向的动作观感把关不足。旧的技术通过与肘部修复仍是历史证据，不能继续作为采集膝盖自然度已通过的依据。正式状态调整、修正版冻结要求和生产通知由主 TA 处理。
