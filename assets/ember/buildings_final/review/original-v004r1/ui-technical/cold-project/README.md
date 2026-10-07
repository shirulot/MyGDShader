# 建筑 v004r1

保留v004已通过技术美术视觉检查的三栋完整造型，仅修复正式实体Alpha格式与演示提示越界。原始母图位于`art-source/ember/building-assets-v004/masters`，提示词及来源记录同批保留；本轮没有重新生图。

打开本包根`project.godot`运行交互演示。WASD移动；靠近门按E开关人门、G开关仓库卷帘；I切换窗玻璃亮暗；靠近面板按P切换供电、L锁门、X设故障；C打开检修盖、R维修；F5/F9保存及恢复。所有操作说明和反馈现在显示在800高视口内。

主资源在`assets/ember/building_assets_v004r1/complete`，同源可选功能层在`functional`。`scenes/ember/building_assets_v004r1`提供3交互、3静态预制体与demo。仍以完整建筑为结构载体，只在必要交互区域变化；门洞、脚印、锚点、缩放和碰撞登记均与v004一致。

生产覆盖规则：每栋母图Alpha>=128作为统一覆盖，实体255/透空0，覆盖内RGB原样保留。全部功能层继承同一覆盖；完整母图、生产覆盖图分别保留。没有逐部件修形、加粗轮廓或新增圆角。

先看`previews/gpu_demo_ui_v004r1.png`的真实锁门反馈与按键提示；`gpu_intact_closed_v004r1.png`、`gpu_intact_open_v004r1.png`为实际场景；三个`*_coverage_edges_4x_v004r1.png`为两侧檐角在深/浅底上、源母图与正式覆盖的实际GPU4倍对照。

`previews/validation_v004r1.json`记录94/94制作方检查；正式交付结论仍等待技术美术定点复审。v004外观PASS不外推为r1技术已经获审。

当前边界不变：进入占地后整壳淡出；开门/开盖显示深暗洞口，没有完整室内、机械内腔或楼层分区；屋顶格栅为固定外壳；亮灯表现为灯面/玻璃颜色和亮度变化，未增加周围地面的动态照明。

复验：冷导入后执行`--script res://tools/validate_capture_buildings_v004r1.gd`（需要真实GPU，勿用headless运行截图测试）。重新生产先运行`build_building_coverage_v004r1.gd`，再运行`export_building_parts_v004r1.gd`，导入生产PNG后执行验证。原稿与旧冻结包不改。
