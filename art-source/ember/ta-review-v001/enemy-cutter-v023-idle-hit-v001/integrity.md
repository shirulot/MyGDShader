# 切割机 C23 v001 idle/hit 技术独立审查

2026-10-07。**固定包、来源、56 个候选姿态约束及最小冷加载通过。** body 横移后出现的局部背景缝已追溯原因，实际播放是否自然由根视觉裁决；技术一致性不自动放行缝隙观感。

范围：七新向 × idle/hit =14 clips/56 新帧，加保留 S 两条/8 帧，最终 16 clips/64 帧。idle 4@4FPS 循环，hit 4@12FPS 单次；128×128/root=(64,104)/Nearest。

## 固定交付绑定

| 项目 | 独立结果 |
|---|---|
| ZIP | `enemy_cutter_idle_hit_v023_v001_2026-10-07.zip`；2,864,441 B；SHA-256 `ec2c8806c16271f55ee584749abe0166ac80e00985816150feb2b2369e934973` |
| 清单 | 219 载荷 + manifest =220 文件；CRC、字节数、全部 SHA 及固定目录逐字节相同。 |
| manifest SHA | `3372241dd56a2a0f34bfc265b56593712a811877967db0d3cada6089caff19c5` |
| catalog SHA | `940b855cafd4c427e98ab2e0e3080ded092c4dd0cdd03c36e01a06aa224662ad` |
| rig SHA | `f931faa3a9838a3a4a23a41835a8c3fc3cf1793067bfe0b7302af04a4b2094af` |
| TRES SHA | `60561c7e049f35888aa761cbcc33b008fba0b9dd5d1da958c21409123f586577` |

ZIP 完整解至两个 TA 副本，固定包和生产目录未改。见 [technical-zip-binding.json](technical-zip-binding.json)。

## 来源与 SE 特殊基准

六新向 source、部件/安装座 config 与 C22 固定候选逐字节/逐字段相同，`move_rig.json` 与 C22 的 `rig.json` 同字节；move_rig 代码仅把配置文件名改为 `move_rig.json`。因此本批使用已核的固定原片和 2×2 原蓝灰纹理，没有新增逐帧生成来源。

**SE 正确对回已通过 HC 的实际 `rig_neutral_down_right.png`，SHA `79e56cd5438f5b78d4dad555e9a364c359635b8cb8b58c6b1790cc166679b462`。** 它不等于早期遮挡不全的静态 SE 母图。C23 的 `source/down_right.png`、输出中性图及首帧均与这个实际绑定相同。

SE cutter spec、原 registered PNG、原闭合前腿母稿与已通过 HC ZIP `5db52757c74fc537b3f45d87abdbab8c58e5d8fcd3cf6366153f7b32ef98b9ef` 同字节/字段。pilot_rig 只将 canonical 与腿原图两处纹理加载改为 `Image.load_from_file` 后创建纹理，几何、源区域、掩膜和统一登记比例未改。两条前腿的 0.04 基底是已通过的固定登记，所有动作帧保持，不是动作中的缩放。

六向原实体归属各唯一；SE 沿用原 HC 的 40 个登记重叠实体点，属于已通过后腿/body 的安装覆盖。本报告没有把 SE 写成“原点全局唯一”，也没有将这套继承重叠混同为 P20 曾出现的未批准双腿串源。

原 S idle/hit 的 8 PNG 与两个 atlas，对原 v012 ZIP `42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe` 逐字节不变。

## 56 帧姿态和实际像素

独立重算 body 轨迹：idle `(0,0)/(0,-1)/(0,0)/(0,1)`；hit `(0,0)/(-1,1)/(1,0)/(0,0)`。所有非 body 部件的 position/basis 均保持中性登记，supports 与首帧相同；工具属于 body 的原片跟随同一轨迹，原相对位置与颜色保持。

七向中性 F00 均与其注册源完整 RGBA 一致；idle F02、hit F03 与 F00 完全相同。64 PNG、16 atlas、登记 SHA、图集每格 RGBA 和 TRES 参数全部匹配；没有把 idle 最后一帧当成恢复帧，idle 循环仍为 F03→F00。

独立按源片、真实层次及整数 body 位移重拼：六向 48 帧的原实体覆盖 RGBA 零差；SE 8 帧的原 body 颜色始终零差，其固定前腿登记/后腿遮罩通过下述实际读回绑定。六向运动中新增 socket Alpha **53 像素次**，每点处于注册四边形内并取原 2×2 纹理颜色，实际显示点的独立 UV 采样也全部相同。没有新 imagegen/新颜色，不等于没有新增输出像素。

独立完整 CPU 模型仍保留 **6 个 Alpha 覆盖残差**，均预测不透明而成品透明，没有 RGB 差：SW idle F01 `(83,83)`；SW idle F03 `(51,71),(52,71)`；SW hit F01 `(51,71)`；N hit F02 `(51,82)`；SE idle F01 `(47,89)`。最后一项涉及既有 SE 固定登记/遮罩边缘，原 body 不受影响。没有为追零差修改模型或素材，全部坐标及预期/实际值见 [technical-integrity.json](technical-integrity.json)。

## 背景缝的独立原因定位

按视觉线给出的精确位置验证：

| 姿态 | 实际透明列 |
|---|---|
| NW hit F01 | x75，y88–93，共 6 点 |
| NE hit F02 | x50，y83–89，共 7 点；x45，y75–79，共 5 点 |
| E hit F02 | x50，y87–93，共 7 点 |

共 25 点在中性时均属于 body。受击横移后，body 的逆映射源点不再属于该 body 实体，固定腿也没有覆盖这些位置；注册 socket 四边形全部不覆盖这些点。因此它们是 body 轮廓离开固定腿后露出的负空间，未发现新 AI 改型、腿片被删像素或输出丢失。**该原因解释不能单独证明背景缝看起来合理。** 视觉线已按实际局部区分它们与腿甲/膝踝切断；根随后完成实际入口及单步观察，确认细缝上方仍成块连接，本轮无新增视觉 P2。见 [technical-seam-trace.json](technical-seam-trace.json)、[visual-review.md](visual-review.md) 及根实际观察记录。

## 脚底测量限制

168 次非 null sole 检查中，163 次上方不透明点的实际顶层归属为本腿；5 次被 body 遮挡：SW rear_right idle F01/hit F01；N front_left/front_right idle F01；SE front_left hit F01。这 5 次仅确认登记落点和遮挡，未将 body 的 Alpha255 当作实际可见脚底量测。隐藏足和 NW 原 null sole 保持既有范围，没有伪造接地点。

## 最小完整冷加载与作者记录

完整 ZIP 解至初始无 `.godot` 的副本，保留全部交付导入设置。Godot 4.7.2 headless 导入 5.330s、探针 3.814s，均 exit 0/stderr 0，**PASS**。219 原载荷导入后 SHA 全保持：

- 实际加载 16 clips/64 个 atlas 单元，完整 RGBA 与原 PNG 一致，FPS/loop/region/duration 正确。
- 实例化实际预览两个 nearest/centered=false 节点；本项目直接使用 16 条 SpriteFrames，没有额外中性缓存计数。
- 实际读回七套 56 个 pose，与独立登记对齐；27 张 ownership mask 与独立解析逐像素零差。
- SE 两张实际 AtlasTexture 裁图与 HC 原腿源各自登记区域完整 RGBA 一致，固定前腿原纹理加载正确。

见 [technical-minimal-cold-load.json](technical-minimal-cold-load.json)、[technical-cold-receipt.json](technical-cold-receipt.json)、[technical-cold-probe.gd](technical-cold-probe.gd)。本轮没有独立重跑完整 GPU、正常/慢速播放器或切向矩阵。

作者 GPU120 条、32 个播放器和 16 次切向均绑定当前 catalog；播放器记录完整见 `[0,1,2,3]` 并各报 passed。GPU QA SHA `a26c0175503811cab0333f40b1dd72a6a96bccd33ca9bdeaacac2914184bdfde`，runtime SHA `9717e8470655acc1f3445aab8a69f6bb5a1852e0587f1bbb4b1a2bc9d89e5e55`。这些是作者记录绑定，不能替代根对上述背景缝和整段动作的独立美术裁决。
