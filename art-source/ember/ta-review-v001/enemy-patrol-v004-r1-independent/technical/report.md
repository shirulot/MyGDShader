# 巡逻兵 move_down v004_r1 技术增量独立审核

结论：本次来源、注册、端点映射和 PNG 表示修复可通过技术增量审核。旧 v002 的近似端点与导出 RGB 变暗问题已关闭；膝甲独立固定体积的实现已确认。此结论不替代动作美术审核，也不把 0.5 硬覆盖视作原生像素精修或整套 production PASS。

## 固定对象与封包

只从 `art-source/ember/deliveries/enemy_patrol_move_v004_r1_2026-10-06.zip` 独立解压至本报告旁的 `package/` 审查。ZIP SHA256 为 `33792f03eb316f7dc82618e226da2eddb9491d504b6803636d04c9e3c7633608`，424291 bytes；109 文件条目、108 清单载荷，清单自身除外。无重复路径，CRC、108 载荷大小/SHA、解压后文件 SHA 全通过。44 个 `.png.import` 是冻结的导入设置，包内没有 `.godot` 缓存载荷。

canonical SHA 为 `6e2c4eb57d214de69778291bcbdc4b40dfb4a5b4881fcb33338bb5f4474f348c`，与旧审核认可母稿一致。catalog 的 source/rig/atlas SHA 均与实际文件一致；atlas SHA 为 `b4b3445e1ef6f5f5a0c74befb91c3ef0d2dab527db0dae36cf45ebf6e6e2c555`。11 个固定 UV 源区出自同一 canonical，没有 8 次独立生图。固定源可证明身份来源，不能单独证明各姿态视觉自然。

## 已关闭的缺陷

| 项目 | 独立结果 | 与 v002 的关系 |
|---|---|---|
| 真实骨段末端 | 从实际导出 basis、rest 向量计算 32 个映射端点，最大误差 `7.697e-7 px`；独立 restbasis 最大分量误差 `1.060e-7` | 旧约 `0.538 px` 的 rest 斜向误差关闭 |
| 膝甲体积 | 双膝甲共 16 个姿态均为恒等 basis、纯平移至登记膝点 | 膝甲不再跟随 shin 的轴向压缩；关闭该实现缺陷 |
| 源到 bind RGB | 独立按 Alpha≥128 覆盖获得 1137 像素，缺失 0、新增 0、可见 RGB 变化 0、可见 RGBA 差 0 | 旧 bind 可见 RGB 752 像素变暗的问题关闭 |
| PNG 表示 | 8 帧全部 Alpha 为 0/255，部分 Alpha 总数 0、边界可见像素 0；atlas 各帧与单 PNG 完全一致 | 当前输出关闭旧连续 Alpha/预乘表示差异；精修质量仍另审 |
| SpriteFrames | 8 个 128×128 region、8 FPS、loop、duration=1；内嵌 524288 RGBA bytes 与 atlas 完全一致 | 输出和运行时注册一致 |
| 预览对象 | `preview.gd` 读取实际 SpriteFrames，在 AnimatedSprite2D 显示正常速与 1 FPS | 旧只播放 rig 的运行证据不足已改正 |

画布 128×128、root (64,104) 保持一致。独立重算 world IK、投影与各部件 pose，并非只读取 producer 的 endpoint JSON。支撑脚实际登记 sole 与投影地面差 0；摆动脚仍有 -2/-4/-1 px 抬脚，不以 bbox 或所有脚都在 y104 替代接地语义。头胸核心 ROI 在补偿登记 body bob 后 8 帧像素差 0。

`entity_cutout.gdshader` 输出源 sampled RGB 和 `step(0.5, alpha)`。`export.gd` 保留 straight RGBA 转换，当前可见输出已全部不透明。因此源中 Alpha 253 的实体 texel 输出 Alpha255、RGB 保持原值，是声明覆盖规则的结果。透明位置使用 Godot 的 Color.TRANSPARENT（隐藏 RGB 为白），不把 alpha0 的 RGB 差计作可见颜色漂移。

## 源/rig/PNG 与黑白底同帧

独立 CPU 以包内源 UV、Polygon、实际矩阵、nearest 采样和 0.5 覆盖规则复算 bind 与 8 帧。bind 可见差 0；7 帧完全一致，f04 有唯一浮点采样边界差：画面 (56,95) 对应 double UV=(56.4999999703,93.9999996571)，转换 float32 后=(56.5,94.0)。实际 PNG 的 RGB=(123,145,156) 正是源 (56,94) 的 RGB，未出现新颜色；本项符合 GPU float32 纹素边界行为。证据中保留这 1 个差异，没有把 CPU double 简化模拟声明为完整 GPU 重跑。

固定包保存了 f01/f02/f05/f06 × 黑/白底共 8 张 roundtrip 左右对照图。独立逐字节核查左右差 0，且两侧分别与直接将正式 PNG 合成到同色底的 ROI 4× nearest 结果差 0；直接看过 `qa/move_detail_4x.png`。producer 的 `render_roundtrip.json` 声明 16 个 native 128 全帧组合差 0，脚本确实比较 rig 与 PNG，但其余 8 组没有独立实图。本次不将 producer 的 16 组或 GPU 冷导入报告冒充独立运行结果；本次独立证据是保存的 8 组实图和全部源到导出复算。

## 仍须保留的验收边界

1. 硬覆盖修好了当前数据表示，但 canonical 仍有 1219 个部分 Alpha 像素。阈值截取不是逐帧原生像素边缘、遮挡和体积精修；若总体规范要求原生精修，此项仍不能 production PASS。
2. 分离膝甲后，连接骨段仍按投影轴向缩放。32 段比例范围约 0.392–1.123，f01 右 shin、f05 左 shin 最短。膝甲恒定证明了该甲片稳定，不证明所有腿段是完整 3D 刚体；肢体衔接、遮挡和接触节奏由独立动作美术审核决定。
3. 封包 hash、端点闭合、源 RGB 保真不证明步态自然。报告只关闭已明确测得的技术缺陷，不扩展到其他动作、其他方向或全敌人包。

## 预览绑定与复验

包内 `preview.html` 直接引用 `output/move_down_v004.png`，上述 atlas SHA 已核。根代理在浏览器查看的 `6106/patrol-move-v004/index.html` 并非包内文件，本次尚未定位本地 server 路由；该页面仅作辅助预览，正式结论仍绑定 ZIP 原帧。

独立证据：本目录 `evidence.json`；可重复运行 `python -X utf8 art-source/ember/ta-review-v001/enemy-patrol-v004-r1-independent/technical/verify.py`。没有修改生产素材、rig、脚本或注册，也没有重复无关 Godot 导入。
