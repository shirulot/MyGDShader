# 机器人 v011 phase B1 rc01：固定包、来源与步相增量审计

最终结论：**NEEDS_REVISION**。制作方主动报告并撤回本批放行：NE/SE沿用SW摆臂角度符号，方向横投影反转后，同侧腕与足步变为同向；N也计划改为明确纵向反相。本审随后独立核对固定代码与骨点，证实NE/SE问题。以下封包、来源和像素复现通过只说明候选可追溯，不构成动作美术通过。

根代理负责播放/视觉；本审未操作浏览器。收到撤回后未开始冷加载，不等待rc02，不回写冻结包。

## 固定对象与范围

- ZIP `art-source/ember/deliveries/robot_eight_way_v011_phase_b1_rc01_2026-10-06.zip`，独立读出 **10,860,493 bytes**，SHA-256 `6b082c9f3db5e4138a828257e4a1555a18da0e6b6dbe9bc73eb2a96502ebd8ad`。
- 577条目＝1目录项＋576文件；575个载荷＋`sha256-manifest.json`自身。575清单项全部唯一、字节数/SHA吻合，无漏项或额外载荷。
- `sha256-manifest.json` SHA-256为 `c319f53a4c0e0f5eccf3015972dc209bc7b1145a1e5cdbfac613dc474c1a1b23`；`walk-batch-metadata.json`另为 `bc8cda346f5e99d1fac8ef2ae10b2ea2d05cbf27401c35f8a0b18b0b3b000d1e`。作者将前者称为catalog存在命名歧义，本审明确按实际文件绑定，不把manifest SHA套给walk metadata。
- 图集 SHA-256 `6d1bfe2cc93cfd17dfe404ba18db0ae87e8e33db3665b1d5df716a291991e9cc`，512×672、每格64×96、root `(32,80)`。
- 新增NW/N/NE/SE各8帧共32；旧S/SW各8；另8张pose身份参考。共56张审阅PNG，八张pose不能计为最终idle2。W/E walk、全部最终idle/collect、主工程接入仍不在已完成范围。

## 独立来源与交付检查

| 项目 | 结果与证据 |
|---|---|
| 旧S/SW与八向身份 | 独立读原phase A rc02 ZIP，SHA `df9884f9668dc89b8c74cf746dbd975a87e9a5b566b6783b5582cb2c78b4d521`；16 walk＋8身份PNG共24张与本包逐字节相同。包内`source/approved-phase-a-rc02-metadata.json`也与原包metadata逐字节相同。原批准范围保留。 |
| 每方向11固定源片 | 四方向44张源片decoded RGBA raw SHA匹配ledger；每个不透明源像素与该方向身份母版原坐标RGBA相同。依照登记绘制顺序独立中性复装，四张母版均0像素差。body在y≥64未夹带下肢源像素。 |
| 固定rig原帧 | Python独立按像素中心、逆刚体变换、nearest与登记层序重算32张raw rig帧，全部0 RGBA差；没有调用制作方`render()`函数，也没有运行会回写输出的builder。 |
| AI连接编辑来源 | 四张原始连接编辑PNG、对应完整prompt及量化源均在固定清单中。原图SHA匹配每向patch报告。独立调用声明的Sharp/Vips nearest API，并按11色与Alpha160阈值归一化，四张raw→量化源均0 RGBA差。未将Pillow与Vips不同nearest注册约定误报为生产差异。 |
| 补丁保护/区域 | 独立从11固定源片重建身体、刚甲区、前臂/工具与完整靴的保护掩膜；从ledger骨点独立重建髋/膝/踝/肩/肘椭圆区域和y≥45限制。32张最终帧由固定rig＋固定网格量化补丁复算，全部0 RGBA差；32张登记mask也全部0差。保护区改变0、区域外改变0、原不透明连接内芯被擦透明0。 |
| 补丁实际幅度 | NW每帧61–93px，N62–85px，NE64–87px，SE75–101px，均为本审decoded RGBA计数。保护的含义是登记刚甲/末端范围；关节环内可编辑浅色连接面仍须由视觉审查确认体量与承接，不能把mask通过当作全关节造型通过。 |
| 未使用W/E补件 | 当前32帧已精确复现为四方向母版固定片＋各自连接编辑图；不依赖side-hidden准备图。侧向准备材料存在不等于侧向walk完成。 |
| atlas | 56张PNG的字节SHA、64×96格与atlas对应区域均正确，RGBA0差；根图集与Godot工程assets副本、两份walk metadata均逐字节相同。56张PNG实体Alpha为0/255、所有可见像素在11色表内。 |
| TRES静态解析 | 独立解析56个AtlasTexture与14个动作：6个walk各8帧/8FPS/loop=true，8个pose各1帧/1FPS/loop=false；duration均1，区域、帧序、FPS/loop与metadata一致。未把pose命名成最终idle。 |
| 当前审阅入口 | `walk-review.html`读取当前walk metadata，9条实际静态链接有效。`review.html`是旧phase A模板，仍读旧metadata名称；不用于本批动作或完整性放行。 |

## P2：NE/SE同侧腕足投影同向

问题首先由**制作方主动发现并撤回**；以下代码和数值为本审独立证据。

`build_fixed_rig_v011.cjs:108` 为同解剖侧臂/腿使用相同 `k=(frame+(side==='left'?0:4))%8`。`:110` 腿目标的横向位移为 `forward.x * 2 * phase[k]`，但`:118–120` 始终用 `a=-phase[k]*0.25` 摆臂，不随视角横投影符号改变。新rig将NE、SE的`forward.x`都设为+1（`build_remaining_walk_v011.cjs:24/:30`），NW为−1（`:12`），所以不能直接继承SW分支的摆臂符号。

下表为固定ledger的**左腕/左踝骨点**及相对该方向中性端点的Δx，单位为纹理px。它们不是bbox、实体脚底或GPU实测坐标；body横位移为0，故足以定位本次投影方向错误。

| 方向/帧 | 左腕 `(x,y)`／Δx | 左踝 `(x,y)`／Δx | 关系 |
|---|---|---|---|
| NE F00 | `(20.8165,55.5954)`／`+1.8165` | `(26,70.49)`／`+2` | 同向，P2 |
| NE F04 | `(17.2194,55.4242)`／`−1.7806` | `(22,71.51)`／`−2` | 同向，P2 |
| SE F00 | `(45.9292,57.2492)`／`+1.9292` | `(39,71.51)`／`+2` | 同向，P2 |
| SE F04 | `(42.0086,57.7440)`／`−1.9914` | `(35,70.49)`／`−2` | 同向，P2 |
| NW F00（对照） | Δx `+2.2388` | Δx `−2` | 反向；不能据此外推视觉PASS |
| NW F04（对照） | Δx `−2.1766` | Δx `+2` | 反向 |

右侧也出现对应的同向符号，详细两侧数据在`phase-projection-independent.json`。本包像素来源/保护通过仍会精确导出这一错误步相，GPU与atlas相等不能发现它。

N的脚主要是y方向±0.6px，而腕仍主要横向约±2.2px；F00/F04左腕去body bob后的y变化分别约−0.1489/−0.3201，无法从此共用Z旋转分支证明明确纵向反相。作者已将N列入修正；本审记录这一映射限制，不仅凭小步幅分数给N判美术通过或退回。

最小修订：按方向投影登记臂摆的方向/相位，NE/SE修同侧反相；N明确纵向前后摆投影。以修正rig重新生成对应原帧、连接编辑/掩膜、最终PNG/atlas/TRES及新冻结rc02，复审关节承接与F07→F00；不能直接镜像工具、交换整帧或覆盖旧S/SW来修符号。旧八向身份与S/SW须继续字节保留。

## 作者证据与独立测试边界

作者112个GPU记录及全部112张对应PNG存在并绑定本固定清单、同一atlas；6段自然循环各2圈、32次相邻45°同相位切换的JSON及atlas SHA已绑定。48个GIF/WebP仅清单SHA绑定，未独立逐动画解码。**TA GPU、循环、转向、浏览器、冷导入/入口加载均为NOT_RUN；撤回后未追加引擎测试。** 只做上述CPU来源、decoded像素、清单和TRES静态核查。

skill报告无几何/边缘/色键错误，但保留三条`weak motion / near-duplicate frames`：SW `[0.0111,0.0104,0.0084,0.0094]`、N `[0.0086,0.0085,0.011,0.009]`、SE `[0.0096,0.0101,0.0099,0.0101]`。SW已批准且本包未改；N/SE要结合投影和播放判断。分数既不抵消本次P2，也不单独作为自动退回依据。

证据同目录：`zip-file-binding.json`、`independent-pixel-integrity.json`、`raw-quantized-source-binding.json`、`tres-static-binding.json`、`phase-projection-independent.json`、`author-evidence-binding.json`；独立脚本`audit_integrity.py`与`check_quantized_sources.cjs`仅写TA证据。`package/`是固定ZIP独立副本，原ZIP与活动生产文件未改。

本rc01整体维持NEEDS_REVISION；旧S/SW及已通过静态身份保持原批准边界。NW来源技术通过不自动成为新动作美术通过。
