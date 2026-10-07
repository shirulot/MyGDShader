# 巡逻兵 attack/death v006 独立动作意图审查

**结论：主动作意图成立，但有两处实际可见的局部 P2，需修订后重新核验；不能以同源/矩阵一致直接放行。**

固定 ZIP SHA256 `1bae7e4fa6932b2479274abecabe247c7efa7efbd7a8b50bbd49b864eea15295`，本目录独立解包 73 文件。逐张检查攻击 6 帧与死亡 8 帧，实际 PNG SHA 与 catalog 的 14 个帧记录逐一匹配；同时看完整黑白底与完整画布，未控制共享浏览器，未编辑生产资源。

依据：[敌人序列帧生产规范](E:/dev/shader/godot-shader/godot-shader-simple/docs/shader-learning/ember-enemy-animation-standard-v001.md)中南向/工具不换侧、短臂枪后坐、准备—蓄势—释放—回收，以及失去支撑—塌落—稳定残骸要求。制作 README 和 phase 名称用于核对提交声明，不作为动作成立的证据。

## [P2] 攻击时夹爪旁出现误收源像素黑条

位置：[attack f02](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/package/output/attack_down/f02.png) `(76,88–90)`；[attack f03](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/package/output/attack_down/f03.png) `(76,87–89)`。这些像素 Alpha=255，确实属于可见轮廓。

在白底逐帧或 10× 最近邻图看画面右侧夹爪，该孤立黑条在 f02/f03 与主体隔透明缝，呈现类似夹爪尖脱开的观感，f01/f04 没有相同孤立显示。这影响工具旁边轮廓的连续性，并非只凭连通分量数量判断。独立逆映射已确认黑条实际属于 left_knee_cap 的误收 UV，并非合法夹爪指段真的断开。

证据：[f01–f04 夹爪旁实际 PNG 局部](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/attack_down_localized_edges_10x.png)与[独立源区归属](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/technical/pixel-ownership.json)。建议一次修正 left_knee_cap UV mask，排除误收的非膝甲源像素 `(76,87–89)` 后重导出；保留合法夹爪形状与现有后坐轨迹，不加连接线、不改夹爪动作。

## [P2] 同一误收 UV 在死亡中形成腿下悬空点/底条

位置：[death f04](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/package/output/death_down/f04.png) `(72,97)/(71,98)`；[death f05](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/package/output/death_down/f05.png) `(66–68,102)`；[death f06](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/package/output/death_down/f06.png) 与 [f07](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/package/output/death_down/f07.png) `(63–65,102)`。

实际白底图中，这些黑点/短条与腿鞋主体之间有透明空间；尤其末两帧仍有一条黑条悬在完整残骸下。独立逆映射确认它们仍是 left_knee_cap 中误收的同三个非膝甲源像素，随膝甲运动到了残骸下方，不是合法腿鞋脱落，也不是登记的碎片动作。

证据：[f04–f07 腿下实际 PNG 局部](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/death_down_localized_edges_10x.png)与[独立源区归属](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/technical/pixel-ownership.json)。同一次膝甲 UV-mask 修正即可处理两种显示问题；保持倒地轨迹和肩侧接地，不改脚部动作、不加连接线或逐帧 bbox 齐底。

## 主动作与接入契约

攻击六帧可读为中性、抬臂、压身蓄势、短促后坐、回收、中性恢复。枪保持角色右臂（画面左），枪轴始终屏幕 +Y；f02→f03 固定枪口标记 `(46,87)→(46,85)`，沿反发射方向移动 2 px，f04 回到 `(46,88)`，f05 回到 `(47,89)`。后坐方向成立；幅度克制，不据此制造更大动作的需求。

f03 的 `attack_release_visual` 是规范要求的视觉登记事件，对应 10 FPS 下约 0.3 秒；事件画布坐标 `(46,85)` 减 root `(64,104)` 后为 Sprite 本地 `(-18,-19)`。当前事件只是 metadata，不是已接好的伤害/子弹信号；规范明确视觉事件只登记，这不是缺陷。南向接入应使用 +Y 方向并应用演员节点变换，不能把 128 画布坐标直接当世界点。没有烘焙枪口光或弹丸符合规范。

死亡 f00–f02 双足支撑且脚底保持，f03 开始失衡，之后转为肩侧接触。f06/f07 肩缘标记约 `(83.12,103.70)`，实际可见边缘到 y=104，残骸整体不悬浮；同一头胸、枪、夹爪随身侧倒，未看到复制第二只工具或第二份残骸。主侧倒、支撑转换和接地可成立；上述腿下断片仍须单独修复。

death 资源 loop=false，f07 的 `corpse_hold_visual` 与末两帧稳定意图一致。预览 0.5 秒后重播是展示行为，实际接入应保持末帧；当前交付并未声称完整物理、AI 或伤害系统。

## 证据

- [结构化动作结论/像素样本](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/action-review-result.json)
- [完整 14 帧 SHA / 枪口及接地记录](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/frame-action-observations.json)
- [攻击完整画布 3×（辅助接地线）](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/attack_down_full_frames_3x_guide.png)
- [死亡完整画布 3×（辅助接地线）](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/death_down_full_frames_3x_guide.png)
- [f02/f03/f04 枪口后坐局部](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-patrol-actions-v006-independent/action-audit/attack_f02_f03_f04_muzzle_detail_10x.png)

本报告不复跑同源技术矩阵，不以它们的 PASS 代替上述实际轮廓判断；无需为已确认的局部 PNG 问题另起 Godot。
