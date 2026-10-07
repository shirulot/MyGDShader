# C2 rc01 根浏览器与关键姿态复核

2026-10-07，绑定固定 `review/phase-c2-rc01`，网页 `http://127.0.0.1:8141/review/phase-c2-rc01/action-batch-review.html`。本记录包含中断前已完成的实看和恢复后的补查；离散截图不称为连续录像，也不替代完整帧检查或 Godot 验证。

根已查看作者的前后、两侧、三个对角方向联系图（共42新帧）及 S 原源/rig/新中性8×对照。浏览器原生1×与最近邻4×并列，实际单步看过 S idle F00/F01、S/N/W/E collect F01、E/SE/NE/NW collect F02、NW F03、E idle F00/F01。S 四分之一速度采集、NW 正常速度重播后，界面实际返回相同方向 idle F00；没有据此声称逐时刻全程录像。保存的原检查截图见本目录 `root-browser-s-collect-f01.png`、`root-browser-e-collect-f02.png`、`root-browser-se-collect-f02.png`。

恢复后补看 SE collect F01/F02 深浅底和 F03 回位。F01/F02 屏幕左侧、角色解剖右肘外边在浅底明显读成上方暗孤点与下段暗短线；深底能看见中间是亮甲色，因此不是透明断肢。对照源图/idle/未编辑rig/最终图的共同ROI，原连续暗轮廓被局部补丁改亮；F03 恢复原来的暗轮廓。判定局部轮廓/材质边界破坏 P2，不能用像素连通或来源可追溯抵消视觉问题。

- [SE F01 浅底实际网页](root-browser-se-collect-f01-light.png)
- [SE F01 深底实际网页](root-browser-se-collect-f01-dark.png)
- [SE F02 深底实际网页](root-browser-se-collect-f02-dark.png)
- [SE F03 浅底回位](root-browser-se-collect-f03-light.png)
- [源 / idle / raw / final 共同ROI](technical-se-elbow-crop-8x.png)

已向基础资源chat发送先行P2通知，要求新rc仅保护/恢复同源外肘轮廓、F01/F02共用一致修复，原母版/骨点/鞋/工具和其他帧保持。正式整批结论由完整视觉、来源与冷载检查共同形成；本文件不单独授予其他方向通过。
