# v013 首阶段：重装机与工蜂右下移动小样

待 TA 动态复审。范围仅 2 条 `move_down_right`、各 8 帧 / 8 FPS / 循环，共 16 新帧。原正向作同相位对照。本包不宣称四款首阶段或八向全动作通过。

两款方向母版已有独立 STATIC_MASTER_PASS，回执为 `ta-review-v001/enemy-eight-directions-v013-preflight/review-static-preflight-v001.md`。包内另两款方向稿仅是冻结上下文，仍在独立校准；`pilot_rigs.json.enabled_pilot_units` 只允许 heavy/cutter 导出。

重装机保留原方向母版刚体轮廓，只在两个固定投影胎面窗口循环原纹理，炮塔悬挂最大 1px。工蜂原有后腿装甲、壳体、工具源像素保留；仅在两个声明的前腿区域补全隐藏行走腿。绑定中性帧相对原方向稿变化 83 个像素，均位于这两个区域。四支撑腿与两个工具臂独立登记，前后对角配对。

交付资源：`output/enemy_tracked_heavy_pilot_v013.tres`、`output/enemy_cutter_pilot_v013.tres`，对应逐帧 PNG 和横排图集在各单位目录。原 PNG、源格归属、rig、提示及图集都绑定在 manifest 中。画布128²，根点(64,104)，Nearest，无逐帧包围盒校准。

作者验证：16 帧 atlas/PNG 全 RGBA 一致、二值 Alpha、无边缘裁切、单连通；32 次深浅底 live rig/PNG GPU 比较及保存的 SpriteFrames/PNG 比较均为0差；8个 normal/1FPS 实例均遍历八帧且回环；16次方向选择中，已有 move 保留第3帧与0.375子帧，未做方向只显示中性图。这些是作者验证，不代表TA美术批准。

打开 `project.godot` 运行审阅器，可选单位、方向、1×/4×、深浅底、正常/1FPS与单帧。命令行脚本 `verify_pilots.gd` 检查原生资源回放，`capture_pilots.gd` 运行实际播放和换向检查。`export_pilots.gd` 可从固定 source+rig 重建，但冻结包不应覆盖；需要重建时复制到单独工作目录。

运行证据：`qa/pilot_runtime.json`、`qa/pilot_gpu_roundtrip.json`、`qa/pilot_pixel_audit.json`；深浅底1×/4×全画布联系图以单位命名。玩法世界速度、碰撞、伤害与其余动作不在本批。
