# 重装机八向待机与受击 v015 / review v001

本批申请七个新方向×待机、受击两类，共14条56帧。另有idle_down/hit_down两条8帧从已通过v012原样复制。移动、攻击、死亡不在本批申请内。

128×128 / root(64,104) / Nearest。idle四帧4FPS循环；hit四帧12FPS单次。动作数据沿用已通过v007正向：idle机身[0,0]/[0,-1]/[0,0]/[0,1]；hit机身[0,0]/[-2,1]/[1,0]/[0,0]，表示屏幕左侧受击回弹，履带支撑固定、相位为0。所有方向均使用已通过的固定静态母版，没有逐帧生图、精灵镜像或按bbox缩放。

受击位移比移动大。已修正部件切线，避免把顶部壳体的一小列分给固定履带；安装处使用原纹理的隐藏重叠区（x半径3/y半径1，y60..98），覆盖在移动壳体之后。只定义源区域归属，不补画RGB；所有中性绑定与源图RGBA零差。修后64帧均单连通、无孤立条纹，安装区共同ROI见qa/mount_*_6x.png。此批安装座修订不改变先前固定移动提交。

打开project.godot运行实际AnimatedSprite2D；idle循环，hit触发一次并保持恢复帧。方向切换保留frame/frame_progress。浏览器与Godot均提供正常/1FPS、1倍/4倍、深浅底、单步及重播。本包输出的SpriteFrames包含16条动作，已通过正向可同相位对照。

作者技术自检：64帧PNG/atlas/内嵌SpriteFrames一致；56新帧在黑白两底共112次live rig/PNG GPU零差；32个实际播放器覆盖全四帧，idle至少一圈，hit恰一次finished且停第4帧，16次方向切换保持相位。技术自检不代表TA艺术通过，当前PENDING_TA_REVIEW。

独立导出入口export.gd读取本包rig.json与source即可复现。七向来源登记和源稿位于provenance；既有正向及初始SE移动门槛版本哈希记于SOURCE_RECEIPT.json，SE移动不作为本批动画载荷。
