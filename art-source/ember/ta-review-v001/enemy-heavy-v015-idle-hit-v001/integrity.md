# Heavy v015 idle/hit review v001 — 独立技术审计

结论：**TECHNICAL_INTEGRITY_PASS，未发现本项P2。** 固定包来源、源像素归属、隐藏重叠、56张新帧的独立CPU重建及16条SpriteFrames资源加载通过。这里只核技术与来源，不由同源、连通或资源加载推成关节外观/重量感/动作播放通过；最终视觉与动态回执另审。本批只申请七新向×idle/hit的14条56帧，旧down两条8帧保持；move/attack/death不属于本次新批准范围。

审查日期：2026-10-07。只读固定ZIP，解至本TA目录 `package/`；没有修改生产目录或冻结包。额外 `cold-load/` 是TA独占测试副本。

## 固定绑定

|对象|实际SHA-256 / 数量|
|---|---|
|`art-source/ember/deliveries/enemy_heavy_idle_hit_v015_v001_2026-10-07.zip`|`3ebf1f1fdb7bb820cdb09258b76df2e087c29f0f8dea1b4bbc0e76adce4bd29f`；4,280,548 B；209文件条目|
|`manifest.json`|`c778c028a28e33af89ed001f1ae862d08f64a34342e7e0a3c560802e3ef711fb`；208载荷；缺失/额外/哈希或字节数错误0|
|`output/catalog.json`|`24cf20d4677e1e77ada77f1a6197da429e81e98531ed7341e79c94f8e6509cd8`|
|`rig.json`|`2021d7424cb684f9bf9398ce78ab4189f5e3fef7e3b76bd51104b34583f59bfa`|
|`output/enemy_tracked_heavy_idle_hit_v015.tres`|`b7c094bbf1a0ef30db9f30148643966274b5ea5729b170d60969dedde15cbe00`|

64张128×128 PNG与16张512×128 atlas逐格RGBA零差，frame/atlas SHA与catalog一致；64帧Alpha均为0/255。catalog的rig/TRES哈希正确，登记canvas128×128/root(64,104)。

## 固定母稿与旧down

八张 `source/{direction}.png` 的字节哈希均与 `enemy-eight-directions-v013/static_preflight_v001/master_catalog_v013.json` 的heavy登记相同，也与当前 `SOURCE_RECEIPT.json` 相同。七新向没有换源、镜像、按帧bbox缩放或逐帧生成变体。母版catalog的旧PENDING文字属于当时快照；本次来源绑定采用其实际SHA及既有heavy静态TA批准边界，不把作者状态字段当作通过依据。

`provenance/registration.json` 与静态预检快照逐字节相同；保留原八向提示词及原turnaround，PNG SHA为 `2cc4b365554c3eb1604e6c2b9360f8ea629adddbc0653e74bcd735b2df32e0e1`。本次只绑定保留下来的来源，不独立证明历史生成服务调用。

从旧固定 `enemy_sequences_v012_2026-10-06.zip`（SHA `42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe`）直接读取对照：`idle_down` / `hit_down` 的8帧PNG、2张atlas全部逐字节相同。没有以当前活动目录代替旧包基线。

## 源归属和隐藏重叠

TA独立以像素中心射线奇偶法重算七向 `track_polygons`。基础履带和机壳是互补分区；固定履带mask随后只在 **y60…98，x半径3/y半径1** 内由基础mask扩展。扩展从同一源图、同一源坐标复制原RGBA，不绘制RGB、替换材质、生成新安装座，也不镜像。实际层序是固定tracks在后，`body.z_index=1`机壳在前；中性位置完全遮住这些重复源像素。

独立重算相对已冻结v014-v002 move rig的切线变化（仅源归属对照，不给v014动作通过）：四向polygon数组不同，但实体像素只有 **NW 21px** 从基础履带归回移动机壳，位于 **(44,49)及x43…44/y50…59**；RGB及源坐标不变。SW/N/NE的polygon改变只影响透明位置，W/E实体归属不变。SE切线与初始已过SE pilot一致。`prior-move-cutline-comparison.json` 已绑定v014-v002 ZIP实际SHA `74ce3153d2389e9d170fbc5ccf0ea92dcf0a14dd671822d3479a5feaa1d00db9`；初始SE另在独立像素审计中对照。之前固定move包没有被修改。

各方向扩展mask里有166…213枚原图实体像素。它们在neutral全部隐藏；位移时部分原纹理露出，逐帧仍可追到同一源图坐标，没有无依据新增像素。下面列实际顶层可见的重叠像素数，作为几何/外观审查定位，不把数量当成通过或返修阈值。

|新方向|重叠源实体数|idle F01/F03露出|hit F01/F02露出|
|---|---:|---:|---:|
|SW|197|21 / 1|47 / 32|
|W|166|51 / 3|67 / 14|
|NW|188|21 / 4|52 / 33|
|N|213|6 / 0|71 / 38|
|NE|191|21 / 1|49 / 29|
|E|168|51 / 4|20 / 46|
|SE|198|21 / 4|62 / 39|

来源坐标完整保存在 `independent-pixel-integrity.json` 的 `added_overlap_opaque_xy`、逐帧 `exposed_overlap_xy`；7张 `ownership_*_4x.png` 为保持原位置的TA诊断图：蓝=机壳、绿=基础履带、黄铜色=追加的原纹理重叠。诊断色不是生产素材。

## 56帧独立重建

不调用作者 `rig.gd`、`export.gd` 或GPU，TA在CPU从固定源像素重建：先放固定扩展履带，再放按声明整数偏移移动的原机壳。履带采样phase为0，shader的窗口取样在该phase回到原源坐标。`idle`四帧偏移依次(0,0)/(0,−1)/(0,0)/(0,1)；`hit`依次(0,0)/(−2,1)/(1,0)/(0,0)。

**全部56张新PNG与CPU重建全RGBA零差**：每张的不明来源实体像素0、源RGBA改变0、catalog pose位移/phase/root与声明一致；七方向idle/hit F00及全部 `qa/bind_{direction}.png` 与原母版全RGBA零差。neutral/frame恢复没有偷偷改变造型。

Alpha0的隐藏RGB统一为(255,255,255,0)，这也是实测Godot `Color.TRANSPARENT` 值；重建采用同一透明值，避免把透明背景RGB差误当实体改画。实体都是二值Alpha，隐藏RGB不作为新增可见颜色。

以上证明这批PNG确实来自同一固定母稿及声明位移。露出的原纹理是否像合理安装结构、受击方向/力度及重量感是否成立，仍需要独立视觉判断，不能由重建零差或单连通推定。

## 最小冷加载与证据边界

**独立实测 PASS**：从固定包复制41个必要入口/源/atlas/TRES载荷到TA `cold-load/`，Godot4.7.2 headless冷导入，加载并实例化 `preview.tscn`。TRES实际含16 clips/64格，内嵌ImageTexture逐格RGBA与16张PNG atlas零差，AtlasTexture region为128×128、每帧duration=1；idle各4帧4FPS loop，hit各4帧12FPS非loop。canvas/root登记正确，两个实际预览sprite为nearest、centered=false；预览采用完整canvas左上角布局，root保留在catalog/pose中。没有执行GPU、32播放器或16方向切换矩阵。

初始TA探针将JSON浮点Array与整数字面Array直接比较，产生一条root/canvas类型误报；已改为明确数值Vector2比较并复跑PASS。初始结果另存 `minimal-cold-load-initial-array-check.json`，不是生产登记错误。

**作者结果仅绑定，NOT_RUN_BY_TA**：`qa/gpu_roundtrip.json` 有112条新帧×黑白底记录，加8条旧down记录；JSON里新记录声明live rig/PNG/TRES零差。固定包没有逐次GPU结果PNG存档，不能把这112条记录称为TA看过112张GPU截图。`qa/runtime.json` 的32播放器及16切向记录、`qa/pixel_audit.json` 都与固定manifest哈希及当前catalog `24cf20…` 相符。作者执行内容和次数按其记录绑定，本代理没有重跑或连续观看这些测试。

## 非阻塞清理建议

`rig.json` 顶部仍保留旧move的 `frame_count=8`、`fps=8`、`loop=true`、8项 `body_y`。本批导出/rig/player使用 `actions.idle/hit`，当前16 clips正确，故不列P2。后续打包可将这些遗留move字段移入明确的参考对象或删除冗余字段，避免外部接入误把它们当idle/hit统一时序；不要改当前已冻结包。

## 证据

- `zip-file-binding.json`：209成员/固定ZIP绑定。
- `independent-pixel-integrity.json`、`audit_integrity.py`：源稿、归属、隐藏重叠、56帧独立重建、64帧atlas和旧包字节比较。
- `prior-move-cutline-comparison.json`：前一固定move包仅源归属增量。
- `ownership_*_4x.png`：保持原源位置的mask诊断。
- `minimal-cold-load.json`、`cold-load/ta_minimal_load.gd`：本代理实际最小冷加载。
- `author-evidence-binding.json`：作者112GPU记录、32players、16turn的绑定边界。

冷验证后再次核208载荷SHA保持。可交综合TA审查；本报告不提前批准该队列的艺术播放结论。
