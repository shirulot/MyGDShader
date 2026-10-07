# 机器人 v011 Phase B2 rc01 独立技术审查

日期：2026-10-07（Asia/Irkutsk）。结论：**FIXED_SOURCE_EXPORT_AND_MINIMAL_COLD_PASS**。本范围未发现技术 P1/P2；W/E 的动作观感与关节形状由根 TA 和视觉审查另行裁定。此结论涵盖新增两条 walk 的来源、登记、补丁保护、导出和资源可加载性，不扩张到 idle/collect 或主项目接入。

## 固定交付与历史保护

- 固定 ZIP：`art-source/ember/deliveries/robot_eight_way_v011_phase_b2_rc01_2026-10-07.zip`；SHA256 `538d7bb49eb2e4480046eee50306a232b7a3f130219564e1618dbfbfff19164c`，16,594,983 bytes。
- 独立核验 883 ZIP 条目、882 清单载荷，条目集合/大小/SHA256/ZIP CRC 全部匹配，活动 review 目录的 882 载荷与固定包逐字节一致。校验过程从 ZIP 读取正式像素，活动目录仅用于对应核对。
- B1 rc02 固定 ZIP SHA256 `b301fdea0e3f634d02a0da4eac437e1ce890515b582216daadc82c82211b4aaf`。逐项比较其六向 48 张 walk 与八向 8 张身份母版，**56/56 原文件字节保持**。已通过的 S/SW/NW/N/NE/SE 不重新开视觉验收。
- 总图集 SHA256 `d048f38b527ed137c4fa6be137c74ca7ff482acf6c965daea5790a4a04d83cea`，与 `godot-walk-review/assets/robot_walk_batch_atlas_v011.png` 同字节。metadata 的 72 PNG（64 walk +8 单张身份参考）与 atlas 对应区域逐像素全 RGBA 一致；尺寸均 64×96，Alpha 仅 0/255，覆盖 RGB 全在 11 色表，透明 RGB 也为 0。

## 隐藏部件与固定源片

固定生成原稿 `source/side_hidden_parts_raw_v011.png` 的 SHA256 为 `ae7f2b70c61c4d5306d34ed5cebfcb2b02f0054d91bec3613df9062568ac8f51`，1254²。包内来源账本、prompt、原稿以及两张实际关节编辑输入均核对 hash 与文件存在；这是保存来源的核验，不自行证明生成工具的运行次数。

独立从 3×2 原稿行列取得 Alpha≥160 的 bbox，复算固定高度/宽度、Nearest 缩放与最近 11 色量化，再按母版轮廓及近腿不能占原可见远腿的规则登记。未运行生产生成脚本，图像库仅用于复算规定的缩放。六块登记 PNG 全 RGBA **0差**：

|方向 / 部件|固定尺寸|母版落点|轮廓外剔除|近腿覆盖远腿剔除|
|---|---:|---:|---:|---:|
|W leg_left|12×26|(23,54)|10|2|
|W leg_right|12×26|(26,54)|32|0|
|W arm_right|8×20|(23,44)|0|0|
|E leg_right|12×26|(25,54)|16|17|
|E leg_left|12×26|(22,54)|23|0|
|E arm_left|9×20|(30,44)|16|0|

依登记归属覆盖原母版可见像素后，独立复算 W/E 各 11 个部件，**22/22 源片全 RGBA 0差**。关节处上下段的同源重叠是登记的承接区，不按唯一像素所有权误拒。中性按原遮挡顺序复装与各自已通过母版全 RGBA 0差，两方向 body 源片 y≥55 均无不透明残肢。

工具保持解剖左腕：W 左前臂 13 个黄铜像素、E 远侧左前臂 3 个；两方向右前臂均 0。远臂隐藏源在固定母版轮廓内，原可见母版像素覆盖隐藏源，不靠镜像交换工具侧别。

## 排姿、保护区与关节局部编辑

按固定 sourcePivot/targetPivot/radians 和最近邻反向采样独立重建 16 张原 rig 帧，全部全 RGBA 0差。64 组肢体链（128 骨段）的端点映射误差最大 `1.42e-14 px`，长度误差最大 `1.07e-14 px`；实际 body 只沿 y 按 `[0.7,1,0.6,0.4,0.7,1,0.6,0.4]` 平移，无缩放。两侧靴独立刚性、旋转为 0；足目标、支撑状态和 `[0,0,0,0,0,0.5,1.1,0.7]` 抬脚序列与登记一致，未出现 IK 超长/缩腿告警。

独立按肩肘旋转公式重算全 16 状态，最大误差 `3.56e-15 px`。F00→F04 沿本方向投影，解剖左腕 `+5.233848 px`、同侧脚 `−4 px`；右腕 `−5.233848 px`、同侧脚 `+4 px`。两方向都为反相，E 方向正确反转了摆臂符号；没有 B1 rc01 已修正的同侧腕脚同向问题。

关节修形使用每方向一张整表统一缩放/量化，未按单帧 bbox 重新配准。独立重算刚性 body、肢体甲片、前臂工具、靴及各自透明轮廓保护矩形，再生成肩肘/髋膝踝椭圆掩膜，16 张 mask 与包内一致。保留原不透明关节 core 的合成规则也逐像素重算，16 张最终帧与预期全 RGBA **0差**：

|方向|F00…F07 的实际修改点数|合计|保护区变化|mask 外变化|
|---|---|---:|---:|---:|
|W|34,17,14,21,18,24,20,21|169|0|0|
|E|16,16,16,41,24,18,16,40|187|0|0|

这些数值确认局部编辑的归属和保护边界；不会以 0差或 IK 可达性代替关节厚度、承重和循环观感的视觉判断。

## 制作方证据与本轮独立冷验证

制作方 `qa/godot_walk_batch_v011.json` SHA256 `a4c7c3731f169d4f5c37c4ea6e0e2e710f817313361d6da056a4667a1cc55f36`。其保存的 **144 张 GPU PNG**（72 图各 1×/4×）与对应正式 PNG/Nearest 放大全 RGBA 静态复比 0差；八向各两圈记录与当前 atlas hash 绑定。`qa/godot_walk_transitions_v011.json` SHA256 `4488cec442f695852b10167bf7a43514e1f4976e3362977f58252c0434e41245`，64 条整数帧切向记录绑定同 atlas。上述运行是制作方证据，TA 本轮没有重跑 144 GPU、自然两圈或 64 切向。

TA 自己从固定 ZIP 创建无 `.godot` 缓存的隔离工程，使用 Godot 4.7.2-stable Steam **实际 headless 冷导入**并运行自有探针：**96/96 PASS**。具体为 SpriteFrames/16 clips/外置 atlas 依赖 3 项、16 clip 的 FPS/loop/帧数、72 图集切片导入后 CPU `get_image()` 全 RGBA、场景可加载、root/Nearest、1×/4×节点和 W↔E 暂停 F03 2 项。导入 3.918s、探针 0.481s，两次 exit=0、stderr=0B；冷导入后包内 882 原载荷 hash 仍全相同。

正式 TRES 的 atlas 是包内 `res://assets/...` 外置依赖，独立冷包可加载，没有运行依赖断链。生成脚本中作者机器的 Sharp 模块路径和历史生成参考是制作过程依赖，不冒称无需配置即可在别机重新生成。此探针不采集 GPU framebuffer、不测自然循环，也不声称保留任意小数帧进度；定点实际验证的是暂停的整数 F03。

独立证据：`binding.json`、`verify_binding.py`、`resample.cjs`、`resample-requests.json`、`cold-receipt.json`、`cold-probe.json`、`probe_cold.gd`、`run_cold.py` 以及 import/probe 的 stdout/stderr。原生产素材、脚本及历史回执均未改。

最终边界：本包使八向 walk 的技术载荷齐备；八张 pose 是身份参考，不能算每向 2 帧 idle。每向 4 帧 collect、完整 24 clips /112 frames、最终主项目整合仍不在本次通过范围。
