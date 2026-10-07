# 巡逻兵五动作 v008 独立技术增量复审

结论：**TECHNICAL_INCREMENT_PASS，v006 膝甲重复归属 P2 已关闭。** 五动作 30 帧只删除对应错误像素，合法可见像素、RGB、动作参数及此前通过项保持。此结论是该局部返修的技术闭环；美术通过仍需 TA 视觉裁决。

审核对象为固定 ZIP `enemy_patrol_actions_v008_2026-10-06.zip`，独立 SHA256 `4a3ab26e04abb5816c505fb0c0f851b8042886d8ea3d2b8516b1923360af74b4`，1098713 bytes，147 项 / 146 清单载荷。独立解包至本目录 `package/`。CRC、全部长度/SHA、解包 SHA、当前同名载荷 SHA 均通过，无重复路径；唯一未列清单项为 `file_hashes.json` 本身。生产文件未修改，没有启动 Godot。

## 根因修补和 30 帧回归

相对 v006，rig 的唯一部件变化是 `left_knee_cap` 多边形：

`(65,85),(77,85),(77,87),(76,87),(76,90),(77,90),(77,94),(65,94)`。

独立在原生像素中心重算区域覆盖，恰好排除 canonical `(76,87)`、`(76,88)`、`(76,89)`，没有新增源像素；这三点仍归属原 `left_arm_claw`。其余 11 部件、pivot/z、rig phases/projection 都保持。rig 其他变化只有版本号和修补说明。canonical SHA `6e2c4eb57d214de69778291bcbdc4b40dfb4a5b4881fcb33338bb5f4474f348c`、中立绑定 PNG、fixed_rig 和材质与 v006 字节相同。

全部 30 帧逐像素对照原固定包，共 491520 像素；全 RGBA 只有 **32 处变化**。它们全部是原可见像素转为既有导出透明表示，无可见 RGB 替换、无新增可见像素、无其他合法部件变化。每个删除点以旧实际矩阵逆映射回上述膝甲三源像素，原 RGB 与 canonical 相同；新多边形已排除该点，其他合法部件也不在该输出位置。逐点 UV/RGBA 证据保留在 `evidence.json`。

| 动作 | 原固定包 | 各帧 RGBA 删除数 |
|---|---|---|
| idle | v005 | `0,0,0,0` |
| move | v004_r1 | `1,1,1,0,0,1,0,1` |
| hit | v005 | `0,0,1,0` |
| attack | v006 | `0,3,3,3,3,0` |
| death | v006 | `0,0,1,2,2,3,3,3` |

v006 报告列出的 attack f02/f03 夹爪内侧条，以及 death f04–f07 腿下点/底条均已消失；修补也清除了该同源问题在其他帧中的显露。通过一次源区域凹口解决，没有逐帧抹点或调整脚/枪。

旧 3 动作统一采用既有 v006 上臂/前臂拆分，但仍施加旧整臂同一刚性变换。独立比较源 pivot 映射最大差 `4.76e-6 px`，basis 差 0；其他共同矩阵差 0。待机/受击及攻击/死亡的运行 CLIPS 参数分别与 v005/v006 相同，move 的 phases/projection 同 v004_r1。30 帧共同姿态参数相同，attack/death 的完整姿态登记字典均与 v006 完全相同，传感器功率、最终肩缘落点和支撑登记未改。

## 来源与资源绑定

- `references/` 的五张旧图集独立绑定上述原 ZIP，字节完全相同，没有以重新生成的旧图充当参考。对应旧 ZIP SHA 保持已有固定值。
- 30 张正式单帧与五图集裁区全 RGBA 零差，catalog 单帧/源/rig/atlas 哈希对应正确。实际 `.tres` 的五动画、30 个嵌入帧/裁区均与图集全 RGBA 零差。画布 128×128、root `(64,104)`，二值 Alpha，无画布边截断。
- idle 4 帧@4 FPS/loop；move 8 帧@8 FPS/loop；hit 4 帧@12 FPS/nonloop；attack 6 帧@10 FPS/nonloop；death 8 帧@10 FPS/nonloop；所有 duration=1。
- attack f03 的 `attack_release_visual` 保持源枪口 `(47,89)` → `(46,85)`，death f07 的 `corpse_hold_visual` 保持。攻击/受击末帧、非 move 中立首帧同认可 bind RGBA 零差；death f06/f07 零差。需要支撑的原地动作脚 ROI `[50,98,29,7]` 零差。
- 重算 150 个实际骨段端点，最大误差 `9.56e-6 px`。这是实际登记端点核对，没有以长度、骨架自报或连通数替代美术判断。
- 60 张包内黑/白底 rig/PNG 对照独立解码：左右全 RGBA 零差，两侧又分别与正式帧直接合成、共同 ROI `(32,32,88,80)`、4× nearest 放大零差。没有隐藏有色底差异。制作方验证报告与本 catalog SHA 绑定。

## 冷证据与预览

外置冷回执 SHA `e00b906726c4afb3a7086d033ffd5c77a3ceccf23db0ec57f865b86646842d44` 已独立核实。它绑定固定 ZIP、`enemy-patrol-actions-v008-coldcheck` 中 13 个核心源/资源及 30 张冻结单帧；对应 SHA 均与本独立解包相同。冷 GPU 报告 SHA `09511b30c3def57f1b1a6d28c9ca433529b67c5e819c27fdf453e69f02a0455c`、回执内嵌报告和 catalog SHA 相同；import/capture exit=0，4 日志的长度/SHA 均吻合，两个 stderr 均 0 bytes。

冷报告记录正常速度/1 FPS 共 10 播放器遍历全部帧：idle/move 有循环而没有 finished，其他三动作有 finished 而没有 loop，约 9.2036 秒。该回执整理的是作者既有冷运行记录，**不是本轮 TA 独立新跑**。单次动作在审阅播放器中停留 0.5 秒重播，不改变实际资源 nonloop。

6106 本地服务根登记及 `patrol-actions-v008/index.html` → 包内 `preview.html` SHA 已验证；catalog、5 atlas、动态切换使用的 10 张黑/白 4× 联系图都与固定包 SHA 相同。运行引用的主场景、预览脚本、SpriteFrames、rig/材质均在包内。页面是辅助观察入口，正式依据仍为固定包原帧。

证据为本目录 `verify.py`、`evidence.json`、`bound-cold-receipt.json`、`bound-cold-playback.json` 和独立解包。保持既有硬 Alpha/原生像素精修限制，不扩大此次返修通过范围到未审敌人或动作；五动作是否最终美术通过由根 TA 结合视觉审查决定。
