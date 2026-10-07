# 机器人八向 v011 — 阶段 A 小样

2026-10-06。**当前为待审小样，不是八向完整动作包。** 最终已授权范围为八向 idle 2帧/2FPS/循环、walk 8帧/8FPS/循环、collect 4帧/6FPS/非循环，共24段112帧。当前保留 v010 朝下行走8帧，新增八向静态母版候选及左下行走8帧。

## 查看

- `review.html`：正常/慢放、1×/4×、深浅底、逐帧、八向固定造型切换。
- `previews/idle_directions_light_4x_v011.png`：S/SW/W/NW，第二行N/NE/E/SE。
- `previews/walk_down_left_normal_4x_v011.webp`、`walk_down_left_slow_4x_v011.webp`：8 FPS和2 FPS。
- `godot-review/project.godot`：独立Godot工程，WASD选向、Tab切换pose/walk、空格暂停、暂停后左右逐帧、B换底。未制作方向明确显示静态候选，不冒充完成动画。
- `gpu-playback/down_to_down_left_same_phase_4x.png`：真实Godot同一步相S/SW对照。

## 来源与做法

画布64×96，root(32,80)，生产像素1:1；方向不镜像，左上固定光向。左腕工具指解剖学左侧：S在画面右、N在画面左，W靠近相机、E在远侧遮挡。

七个新增朝向来自 `source/eight_direction_idle_master_raw_v011.png`。源板1448×1086，以统一50×75采样及每方向一次足底登记组成64×96格；这属于源板转换，不宣称AI直接输出了原生格。每个方向之后保持这一母版注册，不逐帧按bbox缩放或齐底。正面静态候选直接复用已通过v010的F02，仍需重新判断其作为idle的支撑姿态；正面行走八帧则保持原文件字节。

左下小样采用同一母版11个固定部件，两段腿骨、独立刚性靴子和反相摆臂。可编辑分区/支点/排姿在 `build_fixed_rig_v011.cjs`，源片在 `source/fixed-parts/down_left/`。静止实拼与母图RGBA完全一致。AI整条步态参考仅供看姿态，未直接成为成品帧。

固定部件膝/踝边缘有明显拼接感，因此使用imagegen做局部关节修形，并通过 `composite_joint_repair_v011.cjs` 装回原帧。整板仅做一个共同采样变换；头胸、手、左腕工具、靴子及其外缘透明区受保护。最终局部变化和掩膜见 `qa/down_left_joint_patch_v011.json`。这一步仍必须审查关节跨帧形状，不能仅凭掩膜或固定部件流程认定通过。

单正面编辑失败稿保存在source及drafts中，标记REJECTED_NOT_USED，未用于当前图集。母版和小样由内置imagegen生成/编辑；全部提示保存在 `prompts/`。

## 当前验证与边界

`phase-a-metadata.json` 明确登记10个审查clip：2个walk、8个单帧pose。pose不计入最终双帧idle。`qa/export_validation_phase_a.json` 核对PNG尺寸、色板、二值Alpha、v010字节保真、GIF/WebP逐像素保真与时长。

`qa/godot_phase_a_v011.json` 为实际GPU导入/播放记录：24张图各1×/4×共48例，按登记AtlasTexture区域读取原图；两段walk分别自然播放两次循环。GPU截图与信号记录是真实引擎输出，不等于完整动态视觉通过。浏览器逐帧截图也不冒充连续视频。

静态母版比例、工具侧、关节承接；SW正常/慢速步态、脚掌接地、F07→F00；S/SW同相位及八向相邻45°切换，均列入独立TA审查。其他方向walk、双帧idle、四帧collect待阶段A通过后分批生产。未替换主工程资源，未改v008/v009/v010冻结包。
