# 机器人 collect 膝部 v012 rc01 根实际入口复核

2026-10-07。固定ZIP SHA `4dc7298a4b1f3782635bd461eca6dc2be1179e79b35dc4ecfa7ac04a6030f209`，实际入口 `http://127.0.0.1:8141/revisions/collect-knee-v012/compare.html`。

八向均在实际网页以前后同步、原生与4×并列查看关键采集姿态：S/SW/W/NE/SE为F01，NW/E为F02，N另逐步核F00/F01/F02。N用深底，其余主截图浅底。取消循环后实启N四分之一速度、N正常6FPS与W正常6FPS，核开始/动作状态到F03回位已完成。没有用等待时间猜结束，也没有将离散截图称为连续录像。

## 实际观察

旧S/N/NW/SE在前探／保持时的膝甲向两侧翻出、胫段折回固定靴，在新姿态中明显消失。W/E从旧曲折小腿恢复稳定靴与膝甲承接；SW/NE同样保持支撑。当前动作可读为站立操作：上身轻微压低、腕部和工具向前工作，随后收回，不再用大幅屈膝表现下探。

特别比较N F00→F01→F02，中央腰部由中性小阶梯变为较方的深浅横条，但仍夹接于下压胸体与两髋之间。实际原生／4×未读成独立新腰板闪现、悬腰或胸腹压扁，不另判P2。SE髋部高光没有使同一腿换形。腿固定只是方案选择；本判断来自姿态与连接的实际观感。

本线支持新采集姿态视觉通过，需合并完整32新帧深浅专项与技术报告后正式放行。不将这次修复外推为蹲下采集、主游戏目标高度或交互距离已经验证；独立Godot运行结果由技术线另核。

## 实际截图

- `root-se-f01-light.png`、`root-s-f01-light.png`、`root-sw-f01-light.png`
- `root-w-f01-light.png`、`root-nw-f02-light.png`、`root-e-f02-light.png`、`root-ne-f01-light.png`
- `root-n-f00-dark.png`、`root-n-f01-dark.png`、`root-n-f02-dark.png`
- `root-n-slow-finished-dark.png`、`root-n-normal-finished-dark.png`、`root-w-normal-finished-light.png`

页面中的四帧strip和骨点为辅助；本次未把打开页面等同于全32实际逐帧浏览，全32范围由独立视觉报告明确覆盖。旧C2视觉漏审记录继续保留，新姿态根据当前冻结候选重新判断。
