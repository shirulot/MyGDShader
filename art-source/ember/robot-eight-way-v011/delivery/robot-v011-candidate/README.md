# 机器人 v011 · 八向完整动作

24段、112帧，候选已制作；已通过70帧，新增42帧等待C2 rc02正式复审。64×96原生画布，root (32,80)，11色透明像素图。

## 预览

打开本目录project.godot运行。Q/E切方向，1待机、2行走、3采集，空格暂停。网页preview.html须通过本地HTTP服务打开，提供原生/4倍、逐帧、深浅底和慢速。previews/full中另有WebP/GIF。

## 接入现有Godot工程

1. 将assets/ember/robot_v011整个目录复制到目标工程的同名路径。
2. 为AnimatedSprite2D指定robot_eight_way_v011.tres；将Texture Filter设为Nearest，centered=false，offset=(-32,-80)。节点位置就是脚底原点。
3. 播放动作名为idle_down、walk_down、collect_down等。八方向为down/down_left/left/up_left/up/up_right/right/down_right。
4. idle 2帧@2FPS循环，walk 8帧@8FPS循环，collect 4帧@6FPS单次；用animation_finished将采集切回同方向idle并设frame=0。示例代码见preview/preview_full_actions.gd。

所有方向工具均在解剖左腕，禁止用flip_h替代另一侧。主游戏尚未自动接入，本包只提供素材和独立预览。

## 交付依据

完整源包为robot_eight_way_v011_phase_c2_rc02_2026-10-07.zip，哈希见evidence/source-delivery.json；包含母版、固定源片、imagegen输入和提示词、变换、局部掩膜及完整审查证据。本精简包复用完全相同的112帧与atlas，未重新生成。evidence/previous-ta-c2-rc01.md为前序退回回执，当前局部修复仍待新回执，其内部相对证据链接属于原TA报告目录。

原源包通过实际Godot224个GPU画面、16条自然两圈、136次切换及8条采集回待机，冷解压复测一致。精简包只调整资源路径、预览文案和通过状态；verify_import.gd检查实际Godot导入、112区域及资源参数。PNG和SpriteFrames是可用素材，不含采集目标判定、发光或战斗逻辑。
