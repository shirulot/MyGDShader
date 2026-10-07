# 像素角色 skill 筛选

检索时间：2026-10-06。检查了本地 skill 正文和脚本，并用 skills.sh / `npx skills find pixel-art` 找到外部候选。

| Skill | 实际用途 | 本次采用情况 |
| --- | --- | --- |
| 本地 `game-character-sprites` | 像素角色序列帧、参考图锁定、单动作生成、切格与审计 | 主流程。保留项目 64×96 / 8 帧 / 8 FPS，覆盖通用默认值。只读审计适配矩形格；不使用逐帧 bbox 装配。 |
| [pixel-art-sprites](https://github.com/omer-metin/skills-for-antigravity/blob/main/skills/pixel-art-sprites/SKILL.md) | 像素轮廓、像素簇、色板与动画制作指导 | 读取正文、patterns / sharp_edges / validations，采用原生轮廓和连续承接检查。没有全局安装。 |
| [Pixel Art Animator](https://github.com/willibrandon/pixel-plugin/blob/main/skills/pixel-art-animator/SKILL.md) | Aseprite 中逐帧修形、linked cels、时间设置 | 本机未找到 Aseprite，也没有对应 MCP 工具，未使用。 |
| [Scenario Sprite Animation](https://github.com/scenario-labs/skills/blob/main/skills/scenario-sprite-animation/SKILL.md) | 使用图像参考生成像素动画的服务流程 | 当前没有 Scenario MCP/服务连接，未使用。 |

本地 `agent-sprite-forge-2d-game-assets`、`generate2dsprite` 较偏通用流水线；`pixel-art-style` 偏 Blender 风格；`sprite-animation` 偏网页 CSS 动画。它们不直接解决当前机器人的关节分层问题。

这次实际绘画来源是 imagegen 局部编辑。专用 skill 用于约束工序和复核，不能将“用了 skill”当成动画必然正确的证据。

本地入口：`C:/Users/shiru/.codex/skills/character-animation-creator-skill/SKILL.md`。
