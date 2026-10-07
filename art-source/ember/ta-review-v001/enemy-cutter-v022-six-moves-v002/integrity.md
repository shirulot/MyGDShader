# 切割机 C22 v002 技术完整性审查

2026-10-07。**固定包、既有来源、原片刚性运动、导出及最小独立冷加载通过；动作和安装座自然度由根与视觉专项裁定。** 本次直接审 v002；v001 未送审，不赋予其任何先前批准。申请六新向 48 帧，加已通过 S/SE 16 帧，八条移动共 64 帧。

## 固定绑定

| 对象 | 独立结果 |
|---|---|
| ZIP | `enemy_cutter_six_moves_v022_v002_2026-10-07.zip`；2,549,668 B；SHA-256 `3b1619b3cc5a32f11dbe699716b88a9b4a1b8874da55526d6d8c61f6e7d3377e` |
| 清单 | 178 载荷 + manifest =179 文件，CRC、字节数、全部 SHA 及固定目录逐字节相同。 |
| manifest SHA | `de3df38fb098572efcb76082bd86eb4d8145e4fef290d801d53addb940e9bf59` |
| catalog SHA | `4bf5dfb6cdaec70a47b0cd4ea5e0fcb4bc5954b9ae57872fd6beebc8cf98e121` |
| rig SHA | `b0038db5ca4c0fe991712b214b40b5f93e3861ddb2de4cb3b332dde8d9df39be` |
| TRES SHA | `25ebf766257b6e71f4c9a1a3b69fb6310e9061c743c20b5e4b6fc7d920432e1e` |

完整 ZIP 分别解至 TA 分析和冷加载副本，没有修改冻结包或运行生产导出脚本。记录见 [technical-zip-binding.json](technical-zip-binding.json)。

## 已批准母图与原片归属

八张 `source` 及八向输出中性图均与真实静态预检的 `ta-review-v001/enemy-eight-directions-v013-preflight/bound/output/enemy_cutter/neutral_*.png` 同字节；注册文件也与该固定预检登记完全相同。切割者静态通过的适用范围据原回执核实。

旧 S 的 8 PNG/atlas 对原 v012 ZIP `42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe` 同字节；旧 SE 的 8 PNG/atlas 对 pilot HC ZIP `5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef` 同字节。

六新向独立解析原片多边形与 body 保护区后，**原实体像素无重复归属、无遗漏**；六个中性 bind 与原母图完整 RGBA 零差。48 帧的 body 及原腿片只按登记整数平移，基底恒等，无逐帧缩放、旋转、裁剪/齐脚。逐片按真实层次重拼后，原片覆盖的全部实体 RGBA 与实际 PNG 零差；body 原实体全部保持。安装座是另一个明确登记的重复纹理来源，不混写成原片所有权零重复。

## 四足相位与脚底测量边界

独立重算四足相位：front_left/rear_right 为 0，front_right/rear_left 为 4；depth=`[2,1,0,-1,-2,-1,0,1]`、lift=`[0,0,0,0,0,1,2,1]`，body y=`[0,0,-1,0,0,0,-1,0]`。各向 heading 按公式投影并取整数，与 48 个登记 pose、support、安装座端点四边形一致。support=true 且有 sole 时，登记 sole=ground；抬脚量另存于 pose。

可量测 sole 原位置来自该腿选区最底部不透明行的下一条像素边，所取 x 对应本腿原实体；不是用整角色 bbox 或工具最下沿代替。W/E 两条远侧腿和 NW/NE 指定远前腿按源遮挡不新增实例；NW 只露上半部的 front_right 明确 sole=null，不计脚底量测。

视觉线另核 N 全八帧：front_left/right 的登记 sole 属于圆锯/夹爪下方独立承重足端，武器没有当作足。N 没有额外 protected_body polygon，技术依据是整个 body 原像素保持，工具/足的语义归属由该实际视觉检查补足。

17 个已登记 sole 共 136 次输出检查中，129 次其上方实体像素由本腿顶层直接显露，Alpha=255；**另 7 次该位置被 body 覆盖，不能用其 Alpha255 证明本腿脚底实际可见**：SW rear_right F02/F04；N front_right F00/F06、front_left F02/F04；NE front_left F00。这 7 次仅确认登记运动/遮挡，未算作可见脚底量测。此边界不自动构成断腿或步态缺陷，仍需视觉判断。

## 18 个安装座的独立来源和像素核对

每个安装座取本方向原图登记的 2×2 区域，四源点均 Alpha255，RGB 为原暗蓝灰：通道范围 10–118，均 B≥G≥R。原片、浅甲及工具不参与这种纹理拉伸。独立构建的四边形由 body 端和随腿移动端决定，宽度按登记 2 或 3 px；固定 UV 四角为 source_rect 内侧 `.001` 到 `size-.001`，避免采到相邻颜色。

实际 Godot 读回确认 18 个 socket 的 z=-10、Nearest、固定 UV 和中性四边形与登记相符。中性状态下，18 个四边形的栅格覆盖都被原 body/腿实体遮住，新增可见 Alpha 为 0，六向零差 bind 成立。

**运动中确实有新增输出像素。** 48 帧中原片透明位置新增的安装座 Alpha 合计 **57 像素次**；每一个点均位于对应端点四边形内、RGBA 精确来自该向登记 2×2 区域，独立 UV 采样在所有实际显示点上也精确匹配。各方向单帧最多 SW 6、W 3、NW 4、N 4、NE 4、E 4 点。没有新增 imagegen 或新 RGB，不等于没有新增输出 Alpha；报告和交付说明应保持这个区分。

原片重建之外，CPU 对整个安装座矩形的完整栅格预测还有 **8 个 Alpha 覆盖差异**，均为预测有而实际透明：SW F00 `(80,77)`；F02 `(83,83)`；F05/F07 `(51,70),(52,70)`；F06 `(51,69),(52,69)`。实际新点颜色无差，原实体无差。这 8 点保留为 CPU 几何边缘覆盖模型残差，没有强行调整模型消成零，也未冒称所有差异已证明为某一种精度规则。

轻量邻接诊断另见 [technical-socket-contact.json](technical-socket-contact.json)：144 个 socket 姿态中，SW rear_right F05–F07 的四边形栅格位于本腿内，没有触及/邻接 body，但整个原腿片各有 15 个栅格点与 body 的 8 邻域承接。安装座专项已实际查看 F04→F07 浅/深底 8×，未见浮腿或断口，确认 socket 全隐藏无需为数值邻接额外添像素；该诊断闭合为非阻塞，详见 [hip-occlusion-review.md](hip-occlusion-review.md)。几何起点的部件归属与实际整片连接不可混为一谈。

完整来源、48 帧实际新像素坐标/颜色/UV、落点顶层归属和残差见 [technical-integrity.json](technical-integrity.json)，独立脚本 [technical-audit.py](technical-audit.py)。

## 导出与最小独立冷加载

64 张 PNG 与八个 atlas 逐格完整 RGBA 一致，登记 hash 一致、128×128、二值 Alpha，root=(64,104)。八条 move 均 8 帧/8FPS/loop。

从完整 ZIP 新建无 `.godot` 的隔离副本，保留所有交付设置，Godot 4.7.2 headless 冷验 **PASS**：导入 7.065s、探针 4.374s，exit 0/stderr 0；178 原载荷导入后 SHA 未变。八 clips/64 个实际 TRES atlas 格与原 PNG 全 RGBA 一致，两个 nearest/centered=false 预览节点可加载。预先读过实际代码，缓存数确为八 neutral+八 move=16，没有猜测沿用其他批次数量。

运行时读回六套共 24 张原片 ownership mask 与独立解析零差、48 组 pose 与登记一致；18 个 socket 的 UV、z、Nearest 和中性四边形也校验通过。证据：[technical-minimal-cold-load.json](technical-minimal-cold-load.json)、[technical-cold-receipt.json](technical-cold-receipt.json)、[technical-cold-probe.gd](technical-cold-probe.gd)。

## 作者证据及文档问题

作者 GPU112 条、16 个播放器和 8 次方向切换记录绑定当前 catalog。GPU QA SHA `5f461b5ddda3963d816f07fe5785623e70462d00422cbe6161a7730e17c342c3`；runtime SHA `9a0d9045fc87c32266b96133e0c2b04e5e7a852a90980289256c9371346a1359`。仅核作者证据，没有独立重跑完整 GPU、自然播放器或切向矩阵。

非美术阻断的文档修正：`SOURCE_RECEIPT.json` 的 static_review 写为不存在的 `ta-review-v002/...`，实际是 `ta-review-v001/enemy-eight-directions-v013-preflight/review-static-preflight-v001.md`。本轮已绕过错误链接，对真实冻结批准证据独立比对；不修改 v002 固定包。

最终是否放行六条新移动，以根回执及实际视觉为准；本报告不扩大到 idle/hit/attack/death 等尚未提交动作。
