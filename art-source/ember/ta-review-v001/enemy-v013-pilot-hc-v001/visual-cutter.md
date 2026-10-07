# 工蜂右下移动首样：独立视觉第二意见

结论：**PASS_FRAME_REVIEW**。实际查看固定 ZIP 的全部八帧 1×/4×深浅底、共同 ROI、原方向稿/新增中性绑定/零件源图、末首及正向同相位。未发现具体需要返修的身份、工具安装、暴露关节裂口或悬浮脚块。仅此工蜂 `move_down_right` 八帧的逐帧视觉结论；正常与慢速节奏由根代理播放复审，不扩展未审方向/动作。

固定 ZIP SHA-256：`5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef`。独立副本在 `cutter-evidence/package/`，不使用活动生产目录：

- 实际所看图集 `output/enemy_cutter/move_down_right.png`：`e263656e96b15dd7f44bf54bbbe0c59d4d6c46a0f6bfd0ac187987660193898d`。
- 原已过右下静态稿 `source/registered/enemy_cutter_down_right.png`：`ea8a624f5e7cb7a7453afd7ee3b9e5d76b7362fa23c6c9105bc290ea56d35819`。
- 声明补两前腿后的 `output/enemy_cutter/rig_neutral_down_right.png`：`79e56cd5438f5b78d4dad555e9a364c359635b8cb8b58c6b1790cc166679b462`。
- 包内正向同相位图集 `reference/enemy_cutter/move_down.png`：`a89c3d7ef8941d009f5ea8e042ab8a4ffea2249585acd85138cb5af7f3a43772`。
- 所看八帧文件 SHA 均与 catalog 相符，RGBA 与实际图集各格相同。此处只绑定审查对象，不用同源/连通/GPU结果代替形体判断。

| 检查点 | 实际观察与位置 | 结论 |
|---|---|---|
| 四腿与两工具区分 | `pilot_rigs.json` 明确后右/后左为原方向稿独立腿区，前右/前左使用一次补件；两工具仍在 body 区。圆锯位于画面左下、夹爪位于右下，没有把工具当第五/第六只脚，也没有换边。后腿甲片分处壳体左侧和右后上方；新前脚小暗块露在圆锯/夹爪后方。斜向遮挡使四脚不同时完整露出，符合此视角，不据此判缺腿。 | PASS |
| 新增前腿静态身份 | 实际并排原方向稿、新中性、F00，并查看 `source/parts/cutter_down_right_legs_v001.png` 和其完整 prompt。新增是短蓝灰支撑腿、浅膝甲、少量黄铜、块状脚；中性声明约83px修改主要改变工具后方的局部支撑块，圆壳/蓝灰顶件/暗红槽/圆锯轮毂/夹爪轮廓仍是原机。没有长人形腿、额外工具或更亮的新材质。允许此已声明的中性局部补画，不以与旧 canonical 不全等退回。 | PASS |
| 前腿安装点与遮挡 | 全八帧重点 ROI `[43,75,88,100)`。前右可见部分约 x47–54/y89–94，前左约 x76–81/y84–91，上端藏在壳下内架和工具臂后；只移动1–2px时没有露出一条背景横缝、独立漂浮脚块或重复髋帽。F06/F07 前左被夹爪遮得更深，仍可定位为后方短支撑块；不把夹爪本身当足。仅从成品斜向不能读清每根腿的全部髋膝结构，本批接受合理遮挡，若以后放大行程需重新审隐藏结构。 | PASS |
| 后腿承接 | 后右安装点约 `(49,77)`，后左约 `(78,75)`；F02/F06壳体上浮1px、后腿各自平移时，甲片下方暗内架仍承接到壳侧。F03/F04右后上方甲片与圆壳的上缘间有轮廓留空，下部暗腿仍连接；这是独立附肢侧边空间，不是整块甲片脱落。未见新悬浮像素或从关节截断的亮甲面。 | PASS |
| 对角支撑与抬脚 | F01–F03为后右+前左支撑、后左+前右抬升；F05–F07反向配对，F00/F04为交替过渡。实际短脚块/后腿位置变化与这一分组相符，F02/F06身体轻上浮、另一对脚抬至经过步，没有工具臂承担落地。脚片以短程刚体平移完成，当前遮挡与幅度没有造成可见漂移断接；不因动画方法偏好拒绝。 | PASS_FRAME_REVIEW |
| F07→F00 | 共同 ROI 并排 F06/F07/F00/F01。脚块身份、甲片厚度、工具轮廓不变，前左/后右从抬升回落时有约2px落脚变化；F03→F04存在对应半周期落脚。静态未见换形、意外闪出另一只脚或安装点突然开缝，正常速度是否显得顿挫仍由根播放审。 | PASS_FRAME_REVIEW |
| down↔SE同相位 | 实际并排 F00/F02/F04/F06。圆壳、工具顺序、材料和小体量保持；SE近圆锯更遮挡前右腿、远夹爪遮挡前左腿，后腿高低/侧面变化符合投影，未发现方向切换时工具变成脚或身体独立缩放。两方向的对角组和F02/F06轻上浮节奏相容；不要求所有足底在两个视角同画面坐标。 | PASS_FRAME_REVIEW |

证据：

- `cutter-evidence/package/qa/enemy_cutter_move_{white,black}_{1x,4x}.png`：原包全八帧联系图。
- `cutter-evidence/package/qa/enemy_cutter_rig_bind_white_8x.png`、原 `source/parts/` PNG 与 prompt：实际查看的静态绑定与补件。
- `cutter-evidence/original_bind_f0_{white,dark}.png`：同 ROI 原方向稿/新中性/F00；`front_mounts_all_{white,dark}.png`：八帧前腿与工具遮挡；`full_all_{white,dark}.png`：全部附肢与壳体。
- `cutter-evidence/loop_6_7_0_1_{white,dark}.png`、`down_se_phase_{white,dark}.png`：末首与同相位对照。
- `cutter-evidence/part_owner_diagnostic_6x.png`：按声明源区/变换制作的结构辨识辅助图，灰=壳体与工具、青=后右、橙=后左、绿=前右、紫=前左。它是诊断标色，**不是实际PNG分割或GPU等价验证**；外观判断使用原RGBA图。位置与图 SHA在 `part-owner-diagnostic.json`。
- `cutter-evidence/image-binding.json`、`viewed-frame-binding.json`、`roi-binding.json`：ZIP/原图/逐帧/诊断图的SHA和共同ROI、nearest倍数。

未修改生产文件，未运行浏览器或新GPU验证。
