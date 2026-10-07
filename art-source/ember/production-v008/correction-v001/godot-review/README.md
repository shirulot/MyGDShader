# 本轮像素候选独立诊断项目

用Godot独立打开本目录`project.godot`并运行`review.tscn`。最终纹理128px、逻辑32世界格、层缩放0.25；放大图的父节点倍率只用于检查。

此项目显示中心重复、北边接中心、旧端头接窄条、外角接北边、北直岸重复和拒收凹角。图集和`pilot_diagnostic_tileset.tres`包含拒收样稿、旧端头和水底对照，不能作为完成的正式瓦片库直接接入。

运行`run_review.ps1`完成无损导入、语法检查与真实GPU截图，结果为`validation.json`。实际艺术判定见上一级`review-results.json`与`delivery.md`。本项目不配置完整47型Terrain，也不宣称自动铺刷或池岸闭环完成。
