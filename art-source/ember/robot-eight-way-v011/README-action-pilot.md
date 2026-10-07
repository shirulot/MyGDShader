# 机器人 v011 C1 rc01：南西待机与采集

2026-10-07。本批是 SW / down_left 的 idle2、collect4 六张新动作帧，等待独立美术审查。八向 walk 共64帧已由 B2 rc01 回执通过，本批逐文件保持64帧与8张身份母版。最终24段112帧尚未完成，本包也未接入主项目。

## 查看

- `action-review.html`：原生64×96与最近邻4倍并列，可选正常/四分之一速度、深浅底、逐帧与采集结束回待机。
- `previews/idle_down_left_light_4x_v011.png`、`previews/collect_down_left_light_4x_v011.png`：新动作联系图；同目录有深底/透明版和原生版。
- `previews/<idle|collect>_down_left_<normal|slow>_<1|4>x_v011.webp` 和 `.gif`：16个无损动画预览。采集为单次播放，待机循环。
- `godot-action-review/project.godot`：独立 Godot 工程。1待机、2采集、3行走，空格暂停；实际采集完成信号切到待机首帧。

## 动作和来源

64×96画布，root (32,80)，11色、二值alpha；idle2 @2FPS循环，collect4 @6FPS非循环。采集顺序是准备、下探、保持、回位。解剖左腕工具保持原侧，双靴固定。待机仅上身与肩臂上移1px，采集下压2px，四帧使用相同刚性部件。

`build_action_pilot_v011.cjs` 使用已通过SW母版的原source片；原body拆分为body/pelvis，源行54–55重叠承接，中性实拼与母版RGBA零差。没有逐帧包围盒适配、缩放、居中或齐脚。`source/action-rig-pilot/`保存所有坐标/变换与未修接缝排姿；`source/action-fixed-parts/`保存12片。

`composite_action_pilot_v011.cjs` 只合成两张imagegen局部编辑源的接缝：待机F00锁定，F01只修腰；采集F00只修双臂，F01/F02修关节，F03锁定为idle F00。身体、骨盆、甲片轮廓、前臂工具和靴子均保护。F01/F02相同排姿的身体/腿/远臂复用同一接缝像素；近侧工具臂略有移动。

待机改动0/10像素，采集改动5/80/71/0像素；保护区与掩膜外改动均0。原始imagegen采集初稿改变了姿态，已登记 `REJECTED_NOT_USED`，没有使用。第二稿仍有背景伪影，最终仅采纳关节掩膜内、保护区外的合法像素，并限制新增为暗色内芯；原始图不是最终可用透明素材。原图、确切输入、提示词与哈希见 `run-manifest.json`、`qa/action_pilot_provenance.json`。

## 验证

`qa/export_validation_action_pilot.json`：15张图（6新动作+8原SW walk+1身份）与16个动画导出通过；图集/源帧/透明/色板/动图解码一致。idle F00与身份相同，collect F03与idle F00相同；待机y64以下下半身固定、采集y77以下鞋底固定；6新帧各为单一alpha连通体。

`qa/godot_action_pilot_v011.json`：30个实际GPU样本与源RGBA相同；idle与原walk各自然两圈；collect 0→1→2→3，恰好一次结束事件发生在F03，切回idle F00且图像相同。技术检查不代替动作可读性与关节美术验收。

`qa/skill_motion_audit_idle_pilot.json` 和 `qa/skill_motion_audit_collect_pilot.json`：skill审计错误0、警告0。96方格只给原64×96左右各加16px透明诊断边，不是新的发布尺寸。视觉检查记录在 `qa/visual-review-c1-rc01.json`；浏览器截图是离散帧，非完整连续录像。

## 重现

先在副本中运行 `node build_action_pilot_v011.cjs`、`node composite_action_pilot_v011.cjs idle collect`、`node export_action_pilot_v011.cjs`、`node validate_action_pilot_v011.cjs`。Node脚本使用本机已配置的sharp，换机器需调整模块路径。先导入独立Godot工程，再以实际GPU执行 `--script res://verify_action_pilot.gd`。冷包可加 `-- --output-root=<包外绝对目录>`，将检查输出放在包外，保留固定载荷。

冻结目录不回写。新的美术修订使用新的rc编号，不能覆盖本包。SW小样通过后再补其余方向；S现有F02只是身份参考，最终待机需要单独建立中性双脚支撑姿态。
