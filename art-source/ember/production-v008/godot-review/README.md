# 官方范式独立试铺项目

从Godot项目管理器导入本目录project.godot，运行review.tscn。左侧v007官方47槽重排基线；右侧42旧+5新样的混合诊断。左画、右擦、滚轮缩放、中键平移、R重置。

纹理128、世界格32、TileMapLayer缩放0.25，Match Corners And Sides及padding开启。配置通过不能代表美术一致或无缝；当前仍有窄条宽度和板缝跳变。

validate.gd穷举邻域并真实GPU读回；capture_bank.gd显示独立水底与3岸稿，不配置完整池岸47型。run_validation.ps1仅修改独立项目的导入副本，隐藏启动GPU捕获并保存日志；run_bank_capture.ps1保存池岸证据。

生产状态和复现命令见上一级delivery.md。不要把混合诊断直接覆盖主游戏正式资源。
