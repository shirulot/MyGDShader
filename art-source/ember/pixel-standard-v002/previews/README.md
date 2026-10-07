# 美术规范 v2 场景效果候选

2026-10-06。用户要求按已制定规范生成一张大致效果图。本次使用内置 `image_gen`，不改主游戏或正式素材。

- 输出：[scene_preview_v001.png](scene_preview_v001.png)。
- 完整提示词：[scene_preview_v001.prompt.txt](scene_preview_v001.prompt.txt)。
- 依据：[美术规范 v2](../../../../docs/shader-learning/art-style-standard-v002.md)与[自动铺刷规范 v2](../../../../docs/shader-learning/autotile-production-standard-v002.md)。
- 原始工具输出：`C:/Users/shiru/.codex/generated_images/01a10cd5-c2d4-7a01-8740-0c3b355f7465/exec-d4dae90c-4b6b-49ed-9e0b-0c3e4b61be0b.png`，原文件保留，副本无缩放或像素处理。
- 参考方法：观察原生比例板后将角色、设备、配色与尺度描述写入提示词；工具调用为文字生图，未将旧地板作为图像参考输入。
- 状态：`USER_ACCEPTED_FOR_VISUAL_DIRECTION`，2026-10-06用户评价“效果相当不错”，并要求基于该图制作可实际自动补全的地板。只认可整体视觉方向，不是可裁切atlas，不证明32px原生整理、47／16型完整覆盖或Godot自动铺刷通过。

自审：俯视正交轴向、浅装甲设备家族、连续低对比地面和通畅桥接已在概念图中呈现。水纹密度仍高于规范所述的稀疏方向；机器人相对采能站偏小，正式资源制作需按固定原生尺寸复核。图中外周平台立面用于场景示意，不直接定义单格地板切边尺寸。
