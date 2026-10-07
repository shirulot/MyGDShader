# 侦察机 SE 移动 pilot v001 独立技术复核

复核收口日期：2026-10-07（Asia/Irkutsk）。固定交付与起始证据为 2026-10-06，不追溯重写原证据时间。

结论：**FIXED_SOURCE_EXPORT_AND_COLD_RESOURCE_PASS**。本轮未确认来源、保护范围、投影顺序、资源或冷加载的 P1/P2。范围仅 `enemy_scout_drone/move_down_right` 的 8 帧移动；造型、动画意图及实际播放仍由根 TA/视觉报告裁决，不扩大到其余六个新方向或其他动作。

正式包 `enemy_eight_directions_v013_pilot_drone_v001_2026-10-06.zip`：SHA256 `2ef84aaa45b2970bf4db9c5abdf4f845f4d65be9878c97d929701d090d4e37f1`，707,823 bytes；56 条目=55 manifest 载荷+manifest。独立 CRC、清单集合、全部字节数/SHA 通过，活动 56 文件与固定包同字节。自有 `cold-project` 从该包逐项安全解开，初始无 `.godot` 缓存；没有用活动目录代替固定包。

来源保护成立。SE 源 SHA `8cef29b2ad627d52c256a812133b6a3d943ddbdc2a741bd67c0043c8c018acca` 与已过 s004/c003 固定包同字节，输出八向静态图 8/8 与 s004 同字节。转子/井底 master SHA `8824eeff102796d523fa8fab1f17f90c5716b7f34097987c0d5ea8151c2a3a94` 和 prompt 与原已过 v011 包同字节，来源并非 v011-r1。对照 down atlas 与 v012 固定包同字节；对照中性 PNG 与 v012 move_down/F00 同字节，使用的是正式量化成品，不是原始连续 Alpha canonical。`STATIC_SOURCE_RECEIPT.json` 的来源 SHA 对齐。

中性绑定按两轴 `(48.5,69.5)`、`(79.5,58.5)` 和共同半径 `(6.5,4.5)`，由像素中心重新计算两椭圆：89+89=178 点。原源→绑定 PNG 的全 RGBA 差恰好 **178 点且正好等于两椭圆集合**；外部 RGBA 差 0。八帧按固定 body_y `[0,-1,-1,0,1,1,0,0]` 归一后，全部非风口源像素 RGBA 差 0。因此机壳、完整舱壁、支架、短探头保持同源刚性，仅作整体整数升降；没有对每帧重新生图、挪轴或缩放壳体。八帧可见点数均 968，Alpha 仅 0/255，无画布边界实体裁切。该像素核验不以连通数量代替动画美术判断。

转子管线在代码与独立逆映射中确认：`plane.scale=(1,9/13)`，子转子局部角度为近侧 `+11.25°×f`、远侧 `−11.25°×f`，实际屏幕基底为 **S×R**，即先在自身平面转、后投影。风口 mask、井底和转子共用相同固定轴/半径；井底不旋转，壳体不跟着转。16 组屏幕矩阵的行列式均为 9/13，不是对已压扁椭圆直接作屏幕旋转。F07→F00 为四叶结构的下一 11.25° 相位回绕，不能据此声称高分源纹理具有严格四分之一周期的逐像素对称；循环观感由实际播放审核。

轴心观察点已独立定位。按升降归一的 far `(79,58+body_y)`、near `(48,69+body_y)` 两个屏幕像素八帧全部是 RGBA **(55,39,19,255)**；源转子 UV 中心 `(514.5,457)` 的相邻两行相应 RGB 也相同。F03 黄铜轴心没有新生、消失或改色，邻近叶片/井底的对比改变不能被误报为轴心身份漂移。

理想 CPU 风口逆变换与 PNG 每帧全 RGBA 差点为 `[32,17,25,22,24,21,25,28]`，合计 194；**Alpha 差点 0**。其中 101 点为 RGB 单码量化，93 点可对应固定转子或井底的边界邻侧源样本，最大跨理想 texel 边界距离 0.0434136534 源像素，无未解释来源点。例如井底 y=280/632 恰在整数边界；F02 转子源 y=371.043413653 的邻侧采样保留原源颜色。某些边界同时跨过转子 Alpha 门槛，允许显露固定井底。具体源坐标、原 RGB、PNG RGB、层别/残差均存 `binding.json`。这说明差异与采样/量化相容，不把理想 CPU 写成 GPU 零差；本轮没有复跑 framebuffer 来确定驱动精度路径。

8 PNG→1024×128 atlas 全 RGBA 差 0；TRES 内嵌 `Image` 原始 RGBA→atlas 差 0，8 个 AtlasTexture region 对应 `[128f,0,128,128]`，duration=1、唯一动作 8FPS/loop。catalog SHA `150329f234fb986f6bcd6bb2b74f2a77caa10129d9dde444cb8b89afa4150f62`，atlas SHA `8eadc7a469191f46a83e3942d5b6af3799763f8159294579d90af5a187c2e519`；catalog 的源 rig/script、bind、atlas、TRES 与每帧 SHA 均对应。四张黑白 1×/4×联系图独立重新合成全 RGBA 差 0。透明区隐藏白 RGB 保留，不误称所有透明 RGBA0。

作者记录分开核验：16 组 rig/PNG/TRES 黑白零差、4 播放器组见全八帧并至少完整循环、8 切向 PASS；三项 QA 记录 SHA/manifest 与本 catalog 绑定。固定包没有 16 张独立 framebuffer 对照 PNG，故这是**作者记录的绑定复核**，不是 TA 本轮 16GPU/4循环/8切向全套复跑。

TA 本轮实际最小冷验证：Godot 4.7.2-stable Steam，headless。新包冷导入 3.782s，exit0/stderr0；自有资源/场景/定点属性探针 0.368s，**29/29 PASS**、exit0/stderr0。检查包括嵌入 TRES 无外部依赖、八帧/8FPS/loop/region/duration、场景加载、唯一可选 drone、Nearest、SE 保持 F03+0.375 相位，以及未制作 NE 仅静态且保留 down 对照相位。导入后 55 原载荷 SHA 全保持；其他单位的公共 JSON 定义不进入 enabled 单位，也不是本包额外完成量。**没有实际 GPU framebuffer、自然循环或作者完整交互测试复跑**。

本地 6106 服务根登记的 `eight-direction-v013-drone-v001/index.html`、`pilot_catalog_v013.json`、SE atlas 三个实际文件与固定包对应项同字节；这是本地文件绑定，未发网络请求。Godot 冷工程可独立打开；网页使用该配套服务布局，其 HTML 的根相对资源路径不等同于直接双击包内 `previews/index.html` 即可加载。

证据：`binding.json`、`verify_binding.py`、`classify_cpu_samples.py`、`cold-probe.json`、`cold-receipt.json`、`probe_cold.gd`、`run_cold.py`、冷导入/探针 stdout/stderr；均在本 TA 目录。生产只读。最终 binding 状态已同步冷验证，通过范围不以哈希或长度扩大。
