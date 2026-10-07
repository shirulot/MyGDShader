# 机器人 v011 C2 rc02：八向完整动作

2026-10-07。完整24段、112帧已制作：每方向待机2帧、行走8帧、采集4帧。此前通过的64张walk与6张SW动作原样保留；本批新增七方向14段42帧，以及S正面双脚支撑中性姿态，等待独立TA美术验收。8张身份母版保持原字节。此包提供独立预览与Godot SpriteFrames，主游戏接入另行处理。

## 查看和使用

- `action-batch-review.html`：八方向、三动作，可选正常/四分之一速度、深浅底、逐帧；原生64×96与4×最近邻同时显示，采集结束可自动回待机。请通过本地HTTP服务打开。
- `qa/c2_<front_back|sides|diagonals>_<light|dark>_4x.png`：本批42帧联系图。每行依次为idle F00/F01、collect F00/F01/F02/F03。
- `previews/full/`：全部24段的1×/4×、正常/慢速WebP和GIF，共192个文件；idle/walk循环，collect单次。
- `full-action-metadata.json`：每帧路径、哈希、图集矩形、方向、动作速度和通过状态。
- `robot_eight_way_actions_atlas_v011.png`：512×2304图集，8列×24行，每格64×96；每方向按idle、walk、collect排列，不使用的格子透明。
- `godot-full-review/project.godot`：独立Godot工程，Q/E换向，1待机、2行走、3采集，空格暂停。采集播放期间锁定方向，完成后回到同方向idle首帧。
- `godot-full-review/robot_eight_way_v011.tres`：可用的24段SpriteFrames。移入其他工程时连同`assets/`纹理一起迁移并调整资源引用。AnimatedSprite2D采用nearest、centered=false、offset=(-32,-80)，位置就是脚底root。

## 固定规范与来源

画布64×96，root=(32,80)，11色、二值alpha，屏幕左上光。解剖左腕工具保持左右身份，禁止水平镜像替代另一个方向。idle2@2FPS循环，walk8@8FPS循环，collect4@6FPS非循环。collect为准备、下探、保持、回位，F03与同向idle F00完整RGBA相同。

S旧walk F02仍然只是原身份参考。新的中性站姿将该图右侧解剖小腿/靴固定像素向下移1个栅格像素，再使用已保存imagegen源中5个膝内芯像素收接；原身份图和原8张S walk不改。比较见`qa/down_neutral_source_rig_final_8x.png`，源、变换和局部编辑记录见`source/down-neutral-candidate/`。

每方向用同一套12个固定源片。body/pelvis在两行原像素上重叠，源图中性实拼RGBA零差。idle仅头胸肩臂上移1px，骨盆与腿靴不动。collect双靴固定、定长双骨屈膝；S/N下压1px，其他方向2px，正背向使用各自纵向前探投影。没有逐帧bbox裁切、拉伸、缩放或齐脚。

14张新增imagegen关节编辑源的原始图、确切输入、提示词与SHA保存在`run-manifest.json`。最终只采纳关节掩膜内、固定甲片保护区外的像素。生成图可能带有比例偏移或背景光晕，这些部分未装回最终帧；它们不是发布素材。F01/F02相同变换的身体、腿和远臂共用接缝像素，避免保持帧抖动。E idle曾出现两个额外暗色孤点；新增像素必须接触原始不透明轮廓的过滤规则将其排除，没有画线把孤点粘回角色。

## 验证与证据边界

`qa/export_validation_full_actions.json`：112张PNG、192个动画解码、每个图集区域通过；11色、binary alpha、64×96、每帧单一alpha连通体；已通过70张动作与8张身份图逐文件hash不变。各向idle腿变换固定、采集鞋底固定、末帧回位一致。连通体检查只能找浮点，不能替代关节视觉判断。

`qa/godot_full_actions_v011.json`：Godot4.7.2 Compatibility实际GPU，112帧×1/4倍共224图与源RGBA相同；16条循环动作各自然播放两圈；8条采集均0→1→2→3、恰好一次完成后回idle F00；136次同相位换向或同方向动作切换通过，root不变。工程实际实例化验证通过。

`qa/skill_motion_audit_full_idle.json`与`qa/skill_motion_audit_full_collect.json`均错误0、警告0。诊断图仅左右各补16px透明边到96方格，发布素材尺寸保持64×96。

制作方看过深浅联系图，以及网页中的原生/4倍、慢速采集关节、正常回待机。`qa/visual-review-c2-rc02.json`与`qa/browser/phase_c2_rc01_*`记录离散观察，不作为连续录像。技术PASS不代表独立美术已通过；42张新增帧和S中性姿态仍以TA回执为准。

## 在工作副本中重现

下列命令以本目录为工作目录。Node脚本使用已配置的本机sharp路径，换机器需要安装sharp并调整require路径。不要在冻结目录内重新生成。

```powershell
# 七方向的固定登记、imagegen源和SW已通过帧已包含于包内。
node build_remaining_actions_v011.cjs down left up_left up up_right right down_right
node composite_remaining_actions_v011.cjs down left up_left up up_right right down_right
node export_full_actions_v011.cjs
node validate_full_actions_v011.cjs
```

实际GPU验证：先导入`godot-full-review/project.godot`，再执行Godot的`--path <独立工程绝对路径> --script res://verify_full_actions.gd -- --output-root=<包外绝对目录>`。图片和JSON写包外；导入缓存只写独立副本。冷解压后的新检查回执另存于制作目录`qa/cold_delivery_validation_c2_rc02.json`，产生在封包之后，不回写原冻结包。

历史阶段A/B/C1文件只是来源和已通过证据，不让后续未审帧自动继承通过。旧冻结版和ZIP保持只读，新修订使用新rc编号。

## rc02 肘部轮廓修复

TA复审在SE collect F01/F02确认局部P2：接缝补丁将原有暗色外轮廓覆盖为与浅底相同的亮甲色，造成暗点/短线的悬空读感。两帧仅恢复(x14,y52/53/54)三个原rig像素，共6点；同姿势采用一致保护。其余110帧、8身份母版、新S中性、固定源片、骨点、步相、靴子和工具不变。源/修前/修后深浅16倍及整帧4倍比较见qa/se_elbow_rc02_*。本轮实际224GPU、136切换和8条采集恢复再次通过；美术关闭以TA新回执为准。
