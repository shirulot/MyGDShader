# 重装机右下移动首样：独立逐帧视觉审查

结论：**PASS_FRAME_REVIEW**。本次实际查看 `move_down_right` 全部八帧原生/4×深浅底联系图、两个履带共同 ROI 的 8×原样像素，以及 F06/F07→F00/F01 和正向同相位对照。未发现需要返修的具体身份、履带接缝或悬挂承接问题。此结论限定重装机这一条动作的逐帧视觉；未独立观看正常速度连续播放，不替代根代理播放审核，不扩展其它单位/方向/动作。

审查对象从固定 ZIP 独立提取到 `heavy-evidence/package/`，不使用活动目录图像：

- ZIP：`art-source/ember/deliveries/enemy_eight_directions_v013_pilot_hc_v001_2026-10-06.zip`，SHA-256 `5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef`。
- 实际所看图集：`output/enemy_tracked_heavy/move_down_right.png`，SHA-256 `3d2342aa3049cbf3ddc381971cd73b6f49f8a7b06e2cb13b2f4b80c80c2677e6`。
- 方向母版/中性 F00：SHA-256 `7812398344d56901cc0f3673bf724b5eb1a22c229dc30231c437c65e0ebdf073`，保留此前重装八向静态批准的右下造型。
- 正向对照图集：包内 `reference/enemy_tracked_heavy/move_down.png`，SHA-256 `5315a7af9c59ba1aa74702de8dc3318609724c6dab0bc5d9eb395c7a728276a2`。正向既有批准范围不变。
- 八帧 PNG 与 catalog 的 SHA 均一致；每帧与上述图集对应格 RGBA 相同。仅作为所看对象绑定，不用这些检查证明美术通过。

| 检查点 | 实际视觉依据 | 结论 |
|---|---|---|
| 近履带纹理与边界 | F00–F07，原生近履带 ROI `[36,76,61,107)`；窗口约 x43–54、斜切上沿 y81–84。原有灰色横纹/暗槽逐帧移过胎面，外侧胶边、黄铜轮轴、下部轮廓固定。F03/F04 的暗槽变化仍读作胎面纹理，未见横贯整个窗口的额外亮边或纹理越出胶边。 | PASS |
| 远履带纹理与边界 | F00–F07，远履带 ROI `[83,64,108,95)`；窗口约 x90–101、斜切上沿 y69–72。较窄、位置较高符合该方向透视，横纹继续处于原胶框内，没有重复轮轴或窗口变形。 | PASS |
| F07→F00 | 同位置并排 F06、F07、F00、F01。两个窗口末首仍保持同一框与纹理尺度，未见可定位的断带、反向一跳或突然出现一整行异色。8 帧采样相位 0、2…14 是辅助说明，结论依据实际图像，不以整除周期代替目视。 | PASS_FRAME_REVIEW |
| 塔身 1px 悬挂 | F02/F06 塔身略下沉，下一帧恢复；炮口、圆顶、红槽、浅甲板和双履带仍为同一结构。塔身下沿与两侧底座/轴罩区域（约 x54–91、y62–91）仍有可读承接，没有露出背景横缝、悬空炮座或叠出第二安装座。履带外轮廓不随塔身下沉。 | PASS |
| 正向↔右下同相位 | 实际并排 F00/F02/F06/F07。短炮/圆顶/红槽/双履带身份一致；右下近履带侧面与远履带遮挡改变合理，体量没有独立缩放感。两个方向在 F02/F06 都是轻微压缩悬挂，F07 回中性，没有切向后突然转换为另一套重量节奏。斜向外框更深作为已批准投影保留，不按 bbox 宽高机械否定。 | PASS_FRAME_REVIEW |
| 材料与轮廓 | 全八帧浅旧甲、蓝灰内架、少量黄铜和暗红传感槽保持一致；深浅底均未见轮廓断裂、工具漂移或新悬浮像素。胎面细节在原生尺寸较克制，属于当前源造型的低对比表现，未发现因此产生的具体返修项。 | PASS |

证据均保留共同原生位置，透明图叠深浅底后仅 nearest 放大；未改色、补缝或移动生产像素：

- `heavy-evidence/package/qa/enemy_tracked_heavy_move_{white,black}_{1x,4x}.png`：包内原联系图，全部八帧。
- `heavy-evidence/near_track_all_{white,dark}.png`、`far_track_all_{white,dark}.png`：两个履带全八帧同 ROI 8×。
- `heavy-evidence/body_0_3_dark.png`、`body_4_7_white.png`：全部塔身/工具/底座 4×。
- `heavy-evidence/loop_6_7_0_1_{white,dark}.png`：末首同位置对照。
- `heavy-evidence/down_se_phase_{white,dark}.png`：正向/右下同相位上下排 4×。
- `heavy-evidence/image-binding.json`：ZIP 成员与独立副本 SHA；`viewed-frame-binding.json`：实际图集/八帧/catalog 绑定；`roi-binding.json`：诊断图 SHA、源 ROI、帧序、nearest 倍数及背景。

没有以作者单连通、PNG/GPU 零差或骨长验证替代上述外观判断。未修改生产文件、未运行浏览器或新 GPU 验证。
