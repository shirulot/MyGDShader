# 机器人 walk_down v010 独立技术审核

结论：**TECHNICAL_INCREMENT_PASS；动画美术验收保持独立。** 本轮没有发现固定包、来源保护、局部合成或运行资源的新技术异常。此版是烘焙逐帧关节修形候选，不能因原骨架、像素连通或导出通过就声称关节观感通过。

正式对象为 `robot_joint_repair_v010_walk_down_candidate_2026-10-06.zip`，独立计算 SHA256 `97eac4dd8914da78da5543ee0b2641c2045b5e7eb4cfc5452560d74b4f605241`，1543749 bytes，113 项。从此 ZIP 解至本报告目录 `package/`；生产目录仅用于只读 SHA 比较，没有替代固定包，也未修改生产素材。

## 来源、合成与保护

- ZIP CRC 通过，113 路径无重复、无 `.godot` 缓存；全部解包载荷 SHA 与 ZIP 一致，当前生产目录同名 113 载荷也都一致。本包没有另外的全载荷 `file_hashes.json`，审核方在 `evidence.json` 登记了全项长度和 SHA；固定 ZIP SHA、run-manifest 的帧/atlas 冻结登记和冷回执共同绑定本次交付。
- 从既定 v009 固定 ZIP 独立比对 25 项来源：8 原帧、8 owner maps、8 poses、1 rig 字节完全相同。HTML 对照用的另一组 8 原帧也与该来源相同。
- 生成原稿 SHA `94567bbfb8d485b9163c613911219ad35c602b7f2c36c25e7a4b2d06534109c2` 与账本、manifest 相同。原稿 1448×1086 → 256×192 联系板，两轴均为 `0.1767955801`，没有轴向拉伸或按帧 bbox 对齐。独立执行声明的 Sharp nearest 采样，再以 Python 实现 Alpha 阈值 160 与原 11 色 Euclidean 量化，和交付量化板全 RGBA 零差。原 v009 帧不参与重采样。
- 从原 pose 重新构建每帧 12 个关节椭圆，共 96 处登记；逐像素重算保护部件、肩/髋/腕的中间调规则及肘/膝/踝的整盖重画规则。8 张预期遮罩与包内遮罩 RGBA 零差，8 张独立合成与正式帧 RGBA 零差。
- 8 帧改动数依次为 `325,328,306,308,294,293,317,286`，合计 **2457**。账本所有坐标、原/新 RGBA、关节区域归属完全匹配实际改动，没有重复账本坐标。清除旧不透明像素依次 `3,2,2,1,3,0,0,0`，均在已登记编辑区域内。
- 全部 49152 格像素参与比较；**编辑遮罩外全 RGBA 改动 0**，包含透明像素的 RGB。原 owner map 中头、胸壳、左腕工具与双手合计 **6014 个部件归属像素改动 0**；8 帧上部行 0–43 全 RGBA 零差。这里保护的是原图实际部件像素，不以简单矩形范围代替归属。
- 所有正式帧二值 Alpha、透明 RGB 为零、可见颜色均来自既定 11 色。4/8 连通诊断均为单一组件；该结果仅是碎片诊断，不代表关节已可读。
- 当前 87 项正式角色资源与 v007 历史基线 SHA 全部一致，v008/v009 的 16 冻结帧、2 旧 ZIP 同各自保护登记一致。没有将旧版本的关节 NEEDS_REVISION 改写为通过。

## 帧、预览和 Godot 绑定

- 8 帧均为完整透明 64×96 整格，与 `qa/export_validation_v010.json`、run-manifest、合成账本 SHA 一致；图集逐格全 RGBA 零差。frame-set SHA `3ee1b794757491fc96745a1441507d2f85f445f41714feedc0060403268d2b99`，atlas SHA `80c26370261cf0c4a803a140c005a55a6aa883589ae2b178774323913870ca63`，图集 512×96，Godot assets 副本字节相同。
- 实际 `.tres` 为单一 walk_down，8 帧按 `Frame_0..7` 排列，Rect2 依次 `(64*i,0,64,96)`，duration 全 1.0，8 FPS、loop=true。预览场景 nearest、centered=false、offset=(-32,-80)、整数 4 倍；完整格坐标与 root `(32,80)` 保持一致。
- 独立解码深浅底 1×/4× 共 4 个 GIF 的 **32 个页面**，同原帧直接合成和 nearest 放大全 RGBA 零差。每轮 1000 ms，delay 130/120 ms 交替是 GIF 的 10 ms 精度补偿；Godot 动作为均匀 8 FPS。
- 包内 16 张 GPU 1×/4× 图片逐一同正式帧完整 RGBA/nearest 放大零差。
- 冷包 sidecar SHA `5aaa710686503ef71f6d6b8f62a98f215c85f2d169867120274ede99295c0d23` 与 package receipt 一致，sidecar 的 ZIP/frame-set/atlas SHA 均与本固定包相同。实际冷报告 SHA、验证器 SHA、12 项源绑定均复核通过；作者原报告与冷报告源绑定相同。
- 独立读取冷工作区的实际 `.ctex`，解码其内嵌无损 WebP：完整 atlas 及 **8 个导入区全 RGBA 零差**。冷报告的 **16 张 GPU** 文件 SHA 有效，另逐一解码与固定包正式帧比较，完整 RGBA 零差。
- 冷报告两轮自然 AnimatedSprite2D 信号包含全部 0–7 帧，序列连续、时间单调，actual_loops=2。首个启动间隔 90 ms，后续约 121–129 ms，符合已登记的 125 ms 节拍量级。该项是绑定后审计的作者冷运行证据，**没有冒称本轮独立新跑的两轮播放**。

## 独立打开与限制

固定 ZIP 解压后可直接打开 `art-source/ember/robot-joint-repair-v010/godot-review/project.godot`。4 条运行依赖——主场景、预览脚本、SpriteFrames、atlas——全在 ZIP 且相对该独立工程根解析正确；HTML 所需两组 8 帧与辅助图也包含在包内。没有引用主项目才能运行的 runtime 依赖断链。`.import` 设置为 lossless、mipmaps=false、fix_alpha_border=false、premult_alpha=false；ZIP 不依赖旧 `.godot` 缓存。

制作重建脚本使用作者本机 Node/Sharp 路径，冻结保护脚本还会只读查询旧版本基线与旧包；这些是**重建/审计环境依赖**，不影响独立 Godot 预览。验证器需将 `--workspace` 指向保留上述解包目录结构的解包根。此审核未运行任何生产重建脚本。

本轮复用绑定有效的冷证据，没有重复启动 GPU。`verify.py`、`rebuild_patch_sample.cjs`、`evidence.json`、冷回执/报告快照、独立量化板与冷导入解码 atlas 均在本目录。技术增量通过仅支持来源保护、固定格合成与运行像素一致；新关节盖的厚度、暗色横断面和正常速度的连贯性仍由独立 TA 视觉结果裁决。此候选仅涵盖朝下行走，不能推定其他动作/朝向已修复，也不能宣称新像素轮廓仍严格绑定原 3D 骨端。
