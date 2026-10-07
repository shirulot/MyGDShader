# v013 · 恢复膝关节弯曲的采集候选

用户要求：机器人已有明显膝关节，需要正确地使用关节，不能靠锁住双腿取消下蹲来处理旧版扭曲。v012 的历史回执保留，但不代表这次动作需求已经满足。

- [同步对照](compare.html)：v012 锁腿与 v013 弯膝；八方向、1×/4×、慢放、逐帧、骨点。
- [完整动作预览](runtime/preview.html)；[Godot 独立工程](runtime/project.godot)。
- [网络参考及采用规则](references/README.md)。公开参考素材只留在分析目录，不随运行素材包分发。
- [实际提示词](prompts/)；[八次内置 imagegen 来源记录](source/imagegen-ledger.json)。源部件先做朝向投影，imagegen 仅编辑关节区域；不采用生成稿的头身重画与背景。`actual_imagegen_input_4x.png` 重建了生成时的原始输入；后续组合保留 v012 已修好的上身像素。

动作仍为 4 帧、6 FPS、单次；画布 64×96，锚点 (32,80)。F1/F2 恢复浅蹲，髋后移并下降，膝在角色自身前后平面朝脚尖方向屈曲，脚底保持原位置。正面、背面通过投影缩短与遮挡表达，不做横向外翻。未增加动作数；待机、行走、采集首尾共 96 帧原字节保留，16 帧改变。

验证：`qa/validation.json` 检查 112 帧尺寸/哈希/调色板、32 采集帧的 alpha 连通、落地鞋底以及膝角和骨长。`runtime/evidence/runtime-import-validation.json` 是实际 Godot 导入和 24 段/112 帧核对。图形 Godot 进程启动被自动审批以 `blocked by policy` 拒绝，本轮没有新 GPU 播放验证，也没有独立 TA 通过回执。当前状态为 **待用户视觉反馈的候选**，尚未接入主游戏。
