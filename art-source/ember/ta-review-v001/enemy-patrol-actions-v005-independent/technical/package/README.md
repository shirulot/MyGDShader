# 巡逻兵待机 / 受击 v005 候选

本包仅包含 `idle_down`（4帧、4 FPS、循环）和 `hit_down`（4帧、12 FPS、不循环），等待技术美术总监逐条放行。已通过的 `move_down v004_r1` 固定包不变，本包不借用它的PASS。

同一 canonical、11个固定UV区域、左右工具与二值实体材质沿用已通过基准。128×128画布、root(64,104)。`fixed_rig.gd`/`rig.json`保留来源；`action_rig.gd`仅添加本批屏幕空间关节姿态，没有另生角色或逐帧绘改母稿。

待机四相位：中性→上浮1px→中性及夹爪3度轻动→下沉1px。双脚不动，膝/胫跟随小幅躯干起伏。受击：中性→朝画面左短促侧倾5度、位移(-2,+1)→反向3度收稳→精确恢复中性。双足在整个动作中保持支撑；没有根位移、闪白和额外特效。

`output/patrol_actions_v005.tres`直接供AnimatedSprite2D使用，资源内受击不循环。Godot `preview.tscn`和`preview.html`的受击重播是审阅播放器行为：单次播完保持0.5秒再演示一次，不能误当资源循环。导出使用原生128像素Viewport，PNG与atlas采用一致的straight-alpha表示。

证据：

- `qa/{idle_down,hit_down}_{black,white}_{1x,4x}.png`：一致观察区域的完整联系图；不改注册。
- `qa/roundtrip_*`：8帧×黑白底，共16张rig/实际PNG左右对照。全部RGBA通道差异0。
- `qa/verification.json`：按导出矩阵复算32处骨端；固定双足ROI差异0；受击末帧与待机中性全帧差异0。角度会引起正常的nearest重新采样，不能要求旋转的头胸仍与未旋转PNG逐像素相等。
- `qa/gpu_playback.json/.png`：实际SpriteFrames播放8.6秒，正常和1 FPS均覆盖四帧；待机正常8圈，受击正常10次完成，慢速2次完成。仅证明运行时遍历，不代替视觉通过。
- `output/catalog_v005.json`：源SHA、图集SHA、部件实际矩阵、关节、支撑点、实体Alpha和边界检查。

复验：先Godot `--headless --path <本目录> --editor --import`，然后在兼容渲染器执行 `--path <本目录> --script res://verify.gd`，实际播放 `--script res://capture.gd`。`export.gd`会重导帧；送审固定包应独立解压复验，不覆盖源交付。

待TA确认：待机轻动是否自然、受击是否有足够可读的冲击与回稳、关节/肩臂/髋部的旋转遮挡和像素轮廓。攻击、死亡及其他三种敌人没有因本包完成而获得通过。
