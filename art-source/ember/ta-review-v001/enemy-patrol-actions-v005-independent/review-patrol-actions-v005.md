# 巡逻兵 idle_down / hit_down v005：TA 正式回执

本固定批次逐条结论：**idle_down PASS；hit_down PASS。** 只覆盖巡逻兵当前两条动作小样，不继承move通过，也不扩展到攻击、死亡及其他敌人。

ZIP `art-source/ember/deliveries/enemy_patrol_actions_v005_2026-10-06.zip`，SHA256 `6a3687783823cfd3e9db4b5c04d26b47c91a70df825ec74f8d195378b6c01468`，54条目/53载荷。idle atlas SHA `84a29c3af3b2f6dff3c0136a8bc4c1104814442725fa61ac0f5ab140b1197017`；hit atlas SHA `21625b527b143757e553d91591b5df5506ca2654ff0875497fdf62b137d5a64c`。

| 动作 | 实际判断 | 范围 |
| --- | --- | --- |
| idle_down | 四帧轻幅上下变化与夹爪微动保持同一头胸、武器侧和甲片；双足支撑稳定。原生/4倍、深浅底未见肩肘腕或髋膝踝被横切、靠细杆挂甲或无因体积跳变。末首保持中性联系。 | 4帧、4 FPS、循环 |
| hit_down | F01侧倾冲击、F02反向收稳、F03回中性可辨；倾斜时肩髋与腿的承接保持，工具随同结构运动。nearest旋转的边缘取舍有连续姿态依据，未见换件/换侧或新断缝。 | 4帧、12 FPS、单次；集成时另核伤害触发时序 |

根查看待机正常/1 FPS播放抽样及受击白底F01/F02/F03，核对最大侧倾、回稳和中性；独立视觉审查另看全部八个原帧、黑白原生/4倍联系和16张rig/PNG对照。浏览器观看是播放抽样与逐帧观察，不将作者播放计数写成根已连续观看的视频测量。

独立技术检查：同canonical、11UV、rig与材质继承的实际字节一致；八帧、atlas、内嵌SpriteFrames、区域和FPS/loop正确。32真实骨端最大误差1.238e-6px；固定足ROI八帧差0；hit末与idle首全RGBA差0。独立冷GPU重新执行16组黑白底rig/PNG核验及截图全部0差，stderr空；CPU边界采样的两处差异保留解释，没有虚报CPU全相同。6106本地页面、catalog与两atlas已绑定固定包。

通过依据包含实际关节和轮廓审查，来源/hash/足ROI或骨端数值不单独授予美术PASS。保留固定母稿、工具侧、128×128画布及root(64,104)，下一动作继续逐条送审。整套敌人production_ready不因本次两条通过自动变为true。

证据：[逐帧视觉](visual/review-visual.md)、[技术与冷GPU](technical/report.md)。
