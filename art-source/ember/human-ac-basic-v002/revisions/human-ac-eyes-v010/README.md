# A 右下行走 v010：眼神修订

针对 v009 “眼睛好诡异”的反馈。使用内置 imagegen，以原头部为编辑目标重新整理眼部和邻近眉眼表情。目标是收敛亮色眼白，解除缩小后横向亮带与僵硬凝视感。发型、白额发、右下朝向和角色身份作为保留约束。

这是生成模型返回的一张完整头片，不能声称眼睛以外的头部像素逐字节不变。其余11张身体分件、全部8帧姿态、身体起伏、腿部轨迹及播放时序与v009保持。

- 编辑提示词：`prompts/eyes-edit.txt`。
- 内置生成结果：`exec-449f7d91-0219-4edf-8e8b-6d2f2117671a.png`，已复制到项目 `source/head-eyes-edit.png`，绑定片为 `parts/head.png`。
- 原角色分件板 `source/A-parts.png` 仍用于其他11片。`parts.json` 标出头片替代源，重新执行裁片脚本也会保留这次头片。
- `qa/eyes-before-after.png`：从实际输出序列裁出的旧、新面部放大图；审查以游戏尺寸和放大对照一起为准。
- `qa/eye-edit-check.json`：11身体分件字节相同，姿态记录相同，实际图集y≥35的身体区域RGBA相同。
- `qa/export-check.json`：64×96固定格、8唯一帧、二值alpha、固定色板内；8×120ms正向循环。

预览：`http://127.0.0.1:8158/revisions/human-ac-eyes-v010/preview.html`，含v009同帧同速对照、慢放和逐帧。

状态为待用户审阅的眼部修订候选，`production_ready=false`；未将此轮当作完整自然度、远臂遮挡或Godot验收通过。旧v009保留。
