# 机器人 v011 阶段 B2 rc01：左右侧面行走

2026-10-07。本批新增 W/E 各8帧，八向行走共64帧；另有8张固定身份参考，不能计为最终idle。**W/E为待独立美术复审候选。** 前批B1 rc02已获TA PASS，六向48帧与8张母版逐文件保持，共56个原样文件。最终任务仍是八向idle2/walk8/collect4，共24段112帧；最终idle与collect尚未完成。

## 查看入口

- `walk-review.html`：八向行走切换，8FPS正常与2FPS慢放、1×/4×、浅/深/棋盘底、逐帧与自动轮换。
- `previews/walk_left_light_4x_v011.png`、`walk_right_light_4x_v011.png`：两侧各八帧联系图；同目录含透明/深底与原生版本。
- `previews/walk_<direction>_<normal|slow>_<1x|4x>_v011.webp` 和 `.gif`：八向无损透明动图，正常每圈1000ms、慢放4000ms。
- `godot-walk-review/project.godot`：独立 Godot 工程。WASD选向，Tab切pose/walk，空格暂停，暂停时左右键逐帧，B切底。
- `qa/side_walk_evidence_v011.md/json`：W/E源片登记、工具侧、八帧肩肘腕/髋膝踝、F00/F04步相以及前批原字节保持清单。

## 固定来源与连接处理

`source/side_hidden_parts_raw_v011.png` 是按已经通过的W/E身份图生成的一张六部件固定源：每侧近腿、远腿、远臂。`build_side_walk_v011.cjs` 对这些单部件只进行一次裁切、像素尺寸与坐标登记，所有八帧共享同一登记，不逐帧按包围盒缩放、重心对齐或齐脚底。

隐藏源登记到64×96后，原母版可见像素覆盖其上；近腿不会抢占原本可见的远腿像素。每方向11片，静态实拼与已通过母版RGBA零差。登记裁区、缩放后尺寸、坐标、遮挡裁切数量与哈希均保存在 `source/fixed-rig-pilot/<direction>/rig_and_poses.json`。这说明隐藏源的处理方式，不声称AI原图自带正确的64×96注册。

W/E分别排姿，禁止镜像。两段骨骼定长，靴子独立刚性变换。F00/F04的同侧腕/踝沿朝向投影异号。W近侧是带工具的解剖左臂，E工具在远侧左臂；两向右前臂均无黄铜工具色。原生侧面很窄，肢体交错时遮挡重叠较多，仍需结合正常与慢速视觉判断。

两侧独立imagegen局部编辑在 `source/walk_<left|right>_joint_edit_raw_v011.png`，提示在 `prompts/`，当时实际输入单独保存在 `source/side_edit_inputs_b2_rc01/`。`composite_remaining_joints_v011.cjs` 只装回肩肘、髋膝踝区域，保护身体、刚性甲片、前臂/手/工具、靴子和透明轮廓，保留已有不透明关节内芯。W每帧14–34像素、E每帧16–41像素修补；保护区和掩膜外实际差均为0。

## 验证与边界

`qa/export_validation_walk_batch.json`：72张PNG（64walk+8pose）与64个动图通过，全部64×96、原11色、二值alpha；动图解码RGBA与源帧一致。前批56文件原字节保持。新两侧16帧无独立alpha碎点。

`qa/godot_walk_batch_v011.json`：本批重新执行144个实际GPU样本（72图×1×/4×），八段各自然两圈；`qa/godot_walk_transitions_v011.json`：完整八组相邻45°方向、每组八步相，共64次换向，全部通过。图集SHA `d048f38b527ed137c4fa6be137c74ca7ff482acf6c965daea5790a4a04d83cea`。技术通过不替代美术步态、遮挡与连接验收。

制作侧查看W/E八帧联系图、正常浅底、慢速深底与F07→F00，并操作八向自动轮换；浏览器记录 `qa/browser/phase_b2_rc01_*` 是离散截图。旧B1截图只作历史记录。

game-character-sprites动作审计使用左右各16px透明补边的96×96诊断格，不改变原素材像素或发布尺寸。错误0；SW/W/N/E/SE有小步幅/近似帧警告。保留完整报告 `qa/skill_motion_audit_walk_batch.json`，没有为清除统计警告擅改已通过帧。

阶段A及B1 rc02回执保留在 `qa/ta-receipt-*`，B1返修证据在 `qa/arm_phase_revision_evidence.*`。B1 rc02 PASS仅覆盖此前32新帧，不自动覆盖W/E或未来动作。主项目未接入，旧冻结目录与ZIP未回写；双帧待机、四帧采集及完整112帧交付仍待后续批次。
