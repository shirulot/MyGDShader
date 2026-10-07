# 重装机八向移动 v014 / review v001

本批申请六个新方向移动共48帧。down与down_right两条/16帧保留既有通过文件，独立哈希验证不变。8向共64帧不是8条新增通过。其它idle/attack/hit/death不在本批申请内。

128×128、root(64,104)、Nearest、8帧8FPS loop。六方向均来自已过静态母版，每方向只使用一个固定源图。ownership遮罩将履带框和侧部装甲留在接地支架上；中央壳体只在F2/F6做1px悬挂升降。帧0绑定与各方向源图RGBA零差。

履带运动是受窗口限制的原图像素循环采样，周期16、每帧2px；外轮廓和Alpha不变。正侧面的上、下履带段相反流向，圆形轮盖保持固定；未制作轮盖旋转。后向的履带端面使用相反流向。rig.json明确列出每个方向的支撑点、遮罩和窗口。无逐帧生图、无整图镜像、无逐帧bbox缩放或居中。

打开project.godot运行实际AnimatedSprite2D；输出output/enemy_tracked_heavy_move_v014.tres含8条移动。预览方向切换保留frame与frame_progress；可暂停单步、8FPS/1FPS、1倍/4倍和深浅底。同画布正向对照为原通过帧。qa包含64帧像素检查、48新帧在两底共96次live rig/PNG GPU零差、64个嵌入帧一致、16个实际播放器完整循环，以及8次方向相位切换。履带共同ROI位于qa/treads_*_4x.png。

所有技术自检只验证固定资源与运行行为，最终动作视觉结论待技术美术总监审查。本包导出入口export.gd读取冻结rig.json即可运行；上游build_spec.py依赖历史包，因此不作为独立入口包含。
