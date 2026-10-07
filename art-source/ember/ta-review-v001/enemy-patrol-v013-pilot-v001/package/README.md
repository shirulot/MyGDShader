# 巡逻兵右下移动小样 v001

本固定包仅申请巡逻兵 move_down_right 一条八帧动作验收。其七向静态母版已通过 s002；本动作状态仍为 PENDING_TA_REVIEW。原 v012 down 保留。

128×128 / root(64,104) / Nearest / 8 frames / 8 FPS / loop。原生方向源与 s002/c002 SE 字节一致；中性绑定全 RGBA 零差。膝甲与完整靴为刚体平移，短暗色连接轴使用关节端点映射；相位取自已通过 v008 down。遮罩分区已排除邻近夹爪，并把完整靴缘归回正确脚。所有帧使用同一源图与注册，无逐帧生成或 bbox 归一化。

Godot 打开 project.godot 可直接运行。选择各方向会保留已存在移动的 frame/frame_progress；其余六个新方向只显示已过静态母版且明确写未制作。正常/1FPS、原生/4×与深浅底供审阅；八帧腿部共同ROI附 qa/patrol_se_eight_legs_8x.png。

qa 中作者自检绑定当前 catalog：PNG/atlas/嵌入 SpriteFrames 一致；黑白两底共16次 live rig/PNG GPU 对照零差；四播放器覆盖八帧及循环；八方向切换检查。上述技术结果不替代 TA 视觉通过。

pilot_rigs.json 保留公共管线的其他单位定义，但 enabled_pilot_units 只有 patrol；本包不包含或申请其它单位的新动画。生成元数据脚本依赖历史 v008，因此未作为独立入口打包；本包实际运行和导出只读取已冻结的 pilot_rigs.json。
