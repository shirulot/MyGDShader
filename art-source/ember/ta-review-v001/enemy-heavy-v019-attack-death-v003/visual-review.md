# 重装机 H19 v003 视觉增量复审

结论：**INCREMENTAL_VISUAL_PASS，v002 两处 P2 均关闭**。SW 死亡悬挂细条已消除；E 攻击回坐时旧炮口外端固定亮边已消除。实际复看 SW／E 两方向攻击、死亡共 28 帧，未确认修订引入新的安装断接、轮廓残留或身份变化。

固定 ZIP：`enemy_heavy_attack_death_v019_v003_2026-10-07.zip`，SHA256 `18666a8a60b03a5d90ca96d0ae9e49db05f2384d4cf5e05b43fc27895c1935a4`，6,236,316 字节，275 文件成员／274 清单载荷。仅在本目录独立解包至 `visual-package/`；生产文件未改，未操作浏览器或 Godot。

## 实际覆盖

本线看完四张原生深浅联系图中的 28 帧、八张全身深浅 4×联系图、八张安装深浅 8×图，以及六张保持原坐标的 v002→v003 深浅 8×对照图，共 26 张独立诊断。全身统一 ROI `(16,24)—(112,108)` 外可见像素为 0，不按 bbox 重注册。

独立 ZIP／CRC／路径／274 清单 SHA 和字节绑定通过。SW／E 28 张 PNG 均为 128²、二值 Alpha；包内对应 16 张原生／4×黑白联系图与正式帧像素闭合。与已绑定 v002 对比，实际变化恰为 17 帧：SW attack F03/F04、death F01—F07；E attack F01/F03/F04、death F03—F07。其余 11 个本线复看帧字节和 RGBA 均保持。两方向静态源 PNG 字节不变。逐帧哈希、改动包围范围和诊断 SHA 见 [visual-binding.json](visual-binding.json)，实际所看列表、定点像素和外部证据 SHA 见 [visual-conclusion.json](visual-conclusion.json)。

其余六个方向本次没有重新逐帧视审，由技术线 [technical-summary.json](technical-summary.json) 的 95 个未变帧字节保持、源／姿态配置保持证据支撑沿用 v002 的审查结论。作者 GPU／运行数据本线仅绑定哈希，不冒称独立运行；根另完成实际浏览器正常／慢速和关键帧复核。

## SW 死亡 P2 关闭及攻击连带检查

v002 death F04/F06/F07 `(46,89)`／`(46,90)`，F05 `(46,88)`／`(46,89)` 的弱承接竖条已在成品中消失；F03→F04→F05→F06→F07 的炮盾下缘保持干净，回弹时没有旧细条相对炮盾上下跳。深浅原生、4×以及 [新旧浅底 8×](visual-compare-death_down_left-light-8x.png)／[深底 8×](visual-compare-death_down_left-dark-8x.png) 的实际图均确认这一点。

源 `(46,76)`／`(46,77)` 改归固定炮盾后，本线独立读到这两点在 SW 两动作所有 14 帧保持原源 RGBA。归属修订没有破坏原中性形状；attack F03/F04 接合没有新增孔洞、独立贴片或炮盾随塔体滑动的读感。短炮的准备、后坐、回收和塌落垂落仍保持原身份；固定下部与下沉塔体的遮挡能读成同一单位。证据：[SW 攻击浅底 8×](visual-detail-attack_down_left-light-8x.png)、[SW 死亡浅底 8×](visual-detail-death_down_left-light-8x.png)。

## E 攻击 P2 关闭及死亡连带检查

v002 attack F01/F03/F04 在旧炮口外端的固定浅灰／白色边消失，F03 后坐轮廓确实向内退让；未再读出第二个外端口缘。枪根仍与固定护板承接，F05 归位没有新断接。证据：[攻击新旧深底 8×](visual-compare-attack_right-dark-8x.png)、[完整枪根浅底 8×](visual-detail-attack_right-light-8x.png)。

socket 限制到枪根区域也改变 death F03—F07。本线逐帧看过垂落、回弹和保持：原先炮口外侧撤空区的内壁残留清除后，短炮与护板之间仍保持可信连接，未见新增透空断口、被削短的刚性炮管或外端重复轮廓。Nearest 垂落边阶保持连续，F04→F05→F06 的变化仍读成原来的沉降／回弹。证据：[死亡新旧浅底 8×](visual-compare-death_right-light-8x.png)、[死亡完整枪根深底 8×](visual-detail-death_right-dark-8x.png)。

SW／E 的攻击 F05 与 F00 全 RGBA 一致；死亡 F06=F07、F04=F06。F05 保留 1px 回弹，不能称“最后三帧完全静止”。根另以实际播放复核 SW death F04/F05/F06/F07、E attack F03、E death F03/F07，截图 `root-browser-death-sw-f04.png`、`root-browser-attack-e-f03.png`、`root-browser-death-e-f07.png` 已绑定，执行归属为根。

## 放行范围

本线支持关闭这两处局部 P2，并沿用 v002 未变方向的原视觉结论。已有背面三向攻击表现克制、旧 down 大投射器与新方向独立短炮运动不同的范围说明继续保留。

完整 `hidden_mount` 最终可见像素为 0，始终被其他结构遮住；实际可见的新来源内容只有 socket 局部内壁。本次通过不包含完整新安装座母稿或整座显露效果的视觉验收。通过依据是本轮实际成品接合与轮廓检查，未用连通、Alpha 或 GPU 零差替代美术判断。
