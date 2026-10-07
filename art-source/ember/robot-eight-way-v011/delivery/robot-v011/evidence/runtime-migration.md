# 已审源包到正式运行包的迁移核对

来源：phase-c2-rc02；该固定源包全部1723载荷逐项校验通过。

112张帧PNG、同一张atlas和192个动画文件逐字节相同。SpriteFrames、预览脚本、场景、project.godot仅做已声明路径替换。每帧图集矩形、播放速度、循环参数和root均保持。

atlas导入设置保持，包含fix_alpha_border=false和mipmaps=false；Godot只根据新路径改写源路径及缓存路径。metadata和网页仅改变通过标签、证据绑定及资源链接。frames/previews/evidence通过.gdignore排除编辑器自动导入，verify_import仍从原PNG读取对照。

新工程入口已实际GPU运行：idle/walk自然循环、同相位换向、采集期间方向锁定、四帧单次完成后双显示节点回idle F00，1×/4×可见像素一致。完整旧源包224 GPU画面和全部方向矩阵的记录作为源包既有证据；此处新入口仅重跑迁移所需行为。

逐文件来源映射和哈希见runtime-migration-validation.json；新入口见runtime-entry-validation.json和runtime-entry-collect.png。本报告为制作方验证，独立迁移复审回执另行绑定最终ZIP。
