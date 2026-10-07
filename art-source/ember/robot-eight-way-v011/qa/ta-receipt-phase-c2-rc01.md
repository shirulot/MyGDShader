# 机器人 v011 C2 rc01 TA 正式回执

**NEEDS_REVISION，2026-10-07。** 余下七方向 idle2 / collect4 共14段42新帧未整体通过，仅确认 SE 采集 F01/F02 外肘轮廓一项局部 P2。正南新双脚中性来源与六帧腿部专项通过；八向walk64帧、C1 SW idle/collect6帧仍保持原有通过。当前正式通过范围仍为10段70帧，不能将候选24段112帧写成全部验收完成。

## 固定交付

| 对象 | 绑定值 |
| --- | --- |
| ZIP | `art-source/ember/deliveries/robot_eight_way_v011_phase_c2_rc01_2026-10-07.zip` |
| SHA256 | `e0a5fe91bcd62509d0f342e45334ce34cf374ebea1ac0203162d9b90f79b5643` |
| 大小／成员 | 35,015,025 bytes；1702载荷＋manifest＝1703文件 |
| manifest SHA256 | `27b6448dbb0de738fc87b45dc17924dafedec3af8dee47f4512f256a4f02ba4d` |
| action metadata SHA256 | `8072ce3ef444d8c2d3c13cf072380c7398385997b008c01269d0bb3c6d210b6e` |
| atlas SHA256 | `c9963cd1f9c1db11a932164c57eefde0ed80e2de692f0d3700338d7bddba6cc1` |
| 格式 | 64×96、root(32,80)；idle2@2FPS循环，walk8@8FPS循环，collect4@6FPS非循环 |

## 必修 P2：SE 采集外肘暗轮廓被接缝补丁改亮

文件为 `frames/collect/down_right/robot_collect_down_right_f01_v011.png` 与 `robot_collect_down_right_f02_v011.png`。坐标是原PNG的零基坐标：屏幕左侧、解剖右肘 `(14,52)`、`(14,53)`、`(14,54)` 原rig暗色 `(16,24,32,255)` 被替成 `(236,233,216,255)`，而 `(14,51)` 和 `(14,55..56)` 保持暗色。

浅底下中间亮段与背景混在一起，使同一条外肘边变成上方孤点和下方短线；深底显示中间仍不透明。缺陷是动作中外轮廓／材质边界突变，不是真实Alpha断肢、body残边或新生成黑点。F02继承F01同姿态远臂接缝，所以两帧一致地保留了缺陷；保持段不抖动、图像单连通、来源可追溯都不能代替美术通过。

**最小整改**：在新rc中保护／恢复上述已有同源三像素暗轮廓，F01/F02共用同一修复。保留母版、原骨点／相位、双靴、头胸、工具及其他方向／帧；不删暗点掩盖、不另画细连接线、不改背景。若确需扩大范围，逐像素说明。同步PNG、atlas、预览、清单并另冻新包，不覆盖rc01。

证据：[全部新帧视觉](visual-review.md)、[实际网页深浅底与回位](root-preview.md)、[源/rig/补丁追溯](technical-se-elbow.md)、[共同ROI](technical-se-elbow-crop-8x.png)。

## 已完成检查及边界

42新帧全部做原生深浅、完整4×及关节8×逐帧检查；肩肘腕工具、腰髋膝踝、双靴、F01/F02保持与F03回位均已覆盖。其余新帧未确认第二个P1/P2，但此回执不将其他方向拆成独立正式放行。根实际网页检查七方向关键姿态、SE问题前后帧、S与E idle末首，并操作S慢速／NW正常采集回idle；没有将离散截图当连续录像。

[正南专项](neutral-review.md)独立复现67像素次同源小腿／靴下移与5个膝暗芯局部像素，遮罩外和浅甲／外轮廓保护区不变。12源片、六帧raw rig、定长腿与固定双靴复现；collect F01/F02鞋口两点是原小腿遮住靴的正常变化，未错写成最终整片鞋区全零差。S中性不是用旧walk F02直接冒充。旧64walk、SW六帧、八身份图共78图逐文件保持。

[技术报告](integrity.md)核1702载荷、14个新增局部生成源／输入／提示、遮罩保护和排姿合成、全部112PNG/atlas/TRES。七新方向collect F03与idle F00全RGBA相同。技术与来源检查不能抵消上面的轮廓P2。

独立完整ZIP隔离冷解包、无Godot缓存导入，通过24段112格RGBA资源加载、nearest与根锚配置，以及S/N/E真实collect 0→1→2→3、一次finished后回同向idle的最小行为检查，1702原载荷未改。[cold回执](technical-cold-r1-receipt.json)、[具体结果](technical-minimal-cold-load-r1.json)。此前TA选择性拷贝漏带`.png.import`，自动启用了不同的`fix_alpha_border`，造成112格RGBA比较失败；原失败JSON/log保留，完整解包按交付导入配置复验关闭此检查方法问题，不算素材缺陷。

作者224张GPU及完整播放／切换记录仅做绑定，本轮TA未重跑完整GPU／所有循环／136切换矩阵，不声称已验证游戏业务场景集成。

已先行通知基础资源chat具体P2。新rc复审以两帧局部修复、其他内容保持、新包完整绑定和必要最小冷载为重点；不要求重生其余已检查资源。收到的巡逻兵P20 v002、P21 v001保持后续队列，不覆盖本项。
