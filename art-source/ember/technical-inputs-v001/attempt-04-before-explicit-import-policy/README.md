# 修正导入策略前的候选证据

本目录保留第一次 v004 候选包的验收记录，不代表当前最终导入策略。当时像素读回、GPU 灯光和包哈希检查已通过，但 `compress/normal_map=0` 实际是 Detect，编辑器后续可能自动启用丢弃蓝通道的法线压缩。

最终策略明确为 `compress/normal_map=2`、`roughness/mode=1`、`detect_3d/compress_to=0`，并重新执行全部 Godot 验证。当前结果见上级目录的最终验收；候选 ZIP 保存在 `art-source/ember/deliveries/candidates/`，未覆盖任何 v001～v003 历史交付。
