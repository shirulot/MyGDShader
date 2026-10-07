# 巡逻兵 move_down v002 独立来源与技术审查

结论：**固定来源、固定注册、封包与帧资源一致性 PASS；生产像素与导出颜色 NEEDS_REVISION；骨段投影是已声明近似，不能代替刚性造型和步态视觉验收。** 此报告未修改生产素材或脚本，未启动 Godot。根代理与视觉审查另行决定首关是否通过。

## 固定版本与可编辑来源

固定 ZIP SHA-256 `7bca0066890706a814f569de504e4902917e20db05f50f60a1d8b623e6f061a1`，208,377 字节，33 个条目 / 32 项 file_hashes 清单。32 项 SHA、长度、当前工作区内容、CRC 均匹配；唯一未列为载荷的是 file_hashes 自身。无重复路径、`.godot` 缓存或 `.import`。包与当前审查材料一致。

`source/canonical.png` SHA `6e2c4eb57d214de69778291bcbdc4b40dfb4a5b4881fcb33338bb5f4474f348c`，与既有 `enemy-sequences-v001/templates/enemy_patrol_canonical_down_v001.png` 完全相同。`rig.json` 确实登记 9 个固定 Polygon2D / UV 区域：两股、两胫、两足、头胸骨盆、右枪臂、左夹爪臂。`fixed_rig.gd` 每次从 bind 重置，固定两工具侧和股/胫来源，只有既定部件变换，没有逐帧 bbox 拟合、重新居中或 8 次独立生图。source / rig / atlas 的 catalog SHA 绑定均通过。

## 帧资源一致性

- 每帧 `128×128`，atlas `1024×128`，共同 root `(64,104)`，8 帧、8 FPS、循环；8 帧均非空、未触画布边界、没有完全重复帧。
- 独立裁取 atlas 8 格与 f00–f07 的 RGBA 差异均为 0。atlas SHA `8520ca3193389f6a3144cf416fc92851d1eab3ab203d651ed9d05ce3fd0d9f62`。
- 不调用 Godot，直接解析 SpriteFrames 的 524,288 字节内嵌 RGBA；与 atlas 差异 0。8 个 AtlasTexture region 依次为 x=0 / 128 / … / 896，尺寸128；move_down、speed 8、loop 1，duration 均为1。
- 固定头胸 ROI `(54,52,20,25)` 只撤销已登记 body_y 后，8 帧与 **rendered bind_pose** 差异均为0，证明该局部跨帧稳定。它与原 canonical 的该 ROI 各有289处RGBA差异，不能把它写成“与原源RGBA一致”。
- gpu_playback 的 atlas SHA 正确，8.4022 秒、正常8轮、8 FPS与1 FPS均遍历0–7。代码逻辑确实统计实际帧序号，但它播放的是 rig 节点、且记录主要证明遍历；不证明渲染导出 PNG 的颜色与直接 rig 播放相同。没有必要为这些静态绑定检查重新冷导入。

## 发现 1：透明 Viewport 输出按预乘 RGB 直接存入 PNG（P2）

源PNG本身未修改，**导出RGBA不等于原始采样RGBA**。即使零变换 bind_pose，1,224个可见像素中801处RGBA不同，其中752处RGB不同、51处Alpha不同。14,307处纯隐藏RGB变化（Alpha=0）不构成视觉问题，不用其数量夸大错误。

可复核样本：

| 原坐标 | canonical RGBA | bind_pose RGBA |
|---|---|---|
| (66,52) | (27,31,43,65) | (7,8,11,65) |
| (60,53) | (223,211,192,252) | (220,209,190,252) |
| (68,53) | (48,51,55,162) | (30,32,35,162) |

1,213 / 1,224 个可见采样符合 `RGB_out≈RGB_source×Alpha_out/255`，各通道误差不超过1。其余11个都在Alpha3–19的边缘；当前Godot import登记 `fix_alpha_border=true`，因此这少量低Alpha RGB也不能当作原始PNG逐像素原样读取。源图没有被美术调色，但输出存在透明渲染合成与读回转换。

`export.gd` 把 transparent SubViewport 的 `get_image()` 直接 RGBA8 / save_png / blit_rect。结合本包实际像素，可以判定颜色存储符合预乘模式；普通 PNG / 浏览器 / 默认 SpriteFrames 消费又按直通 Alpha 混合，会把半透明RGB再次压暗。Godot官方仓库同类透明 SubViewport 行为记录也明确讨论了这一问题：[godotengine/godot #99715](https://github.com/godotengine/godot/issues/99715)。本包结论以实际像素为主，并非假定所有Godot版本必然相同。

最小修法：修正导出透明度表示，在 PNG、atlas、内嵌 SpriteFrames 之前统一从读回预乘颜色还原为规范直通 Alpha（Alpha为0时RGB归0）；或按固定source / UV / 变换做直通RGBA导出。此操作属于导出表示转换，应记录为转换，不能称原始字节无改变。8位预乘会损失极低Alpha RGB精度，因此不要宣称反除后绝对逐像素还原；最终原生二值实体 Alpha 仍应在母稿完成。验证源图→bind及同帧 rig / PNG 在黑白底显示一致，而不是给播放器加补偿着色掩盖PNG的问题。

另：51个 source 可见像素位于两个已登记区域的重叠处；独立按 `A_out=1-(1-A_source)^n` 计算，所有51个Alpha与bind完全一致，误差0。这是关节套叠的正常source-over结果，不是程序阈值化；但README的“原生Alpha保留”只适用于原始文件和纹理输入，不能扩展为“最终导出各像素Alpha未变”。

## 发现 2：语义骨末端与真实部件变换并未精确对齐（P2，限技术精度）

`apply_segment()` 采用 `rotation=current.angle()-rest.angle()` 与 `scale=(1,current.length()/rest.length())`。但原股、胫向量分别含±1的局部x分量，缩放发生在局部Y而不是原骨段方向。这并不严格把原 `end` 变换到记录的 knee / ankle。

独立把原end代入实际二维矩阵：最大偏差 **0.538px**，f01右胫、f05左胫；f02右胫、f06左胫为0.449px。股末端多数0.281px。比如f01右胫语义踝 `(56,95)`，真实原end变换约 `(55.465,94.943)`。这是亚像素误差，不能仅凭该数断言画面已经断腿；但“metadata末端相接”没有证明皮肤图块精确相接。

最小修法：沿原骨段基底构造仿射变换，`A = B_current · diag(1,length_ratio) · inverse(B_rest)`，其中第二轴沿对应骨段，第一轴是其法线；或直接由原骨段及法线解出等效矩阵。让原pivot/end均精确落到目标关节，再单独检查实际不透明袖口套叠。复验应记录**变换后真实end**误差和可见连接，而不只是IK目标。

## 投影、支撑与甲片缩短边界

独立核算16条腿记录：world股长约11、胫长约15，误差在浮点范围；采用固定前屈分支、投影 `104-0.75*height+0.35*depth` 与记录整数关节完全相符。foot为纯平移，scale1 / rotation0；所有 support 帧的sole marker与其depth对应ground相同。摆动脚f01/f05高2px、f02/f06高4px、f03/f07高1px。这些标记是**语义sole边界**，不能代替可见像素接触检查。

原地行走的支撑足有前后depth，ground y可以为102–106；不能机械要求足底永远104，也不能把bbox最低点当支撑。f07→f00是右支撑到左接触/双支撑的转换，登记相位一致。

图块缩放范围值得实际审图：

| 对象 / 相位 | 实际局部 scale_y |
|---|---|
| 股甲多数帧 | 1.2806 |
| 摆动腿经过步 f02/f06 股甲 | 1.1402 |
| f01右 / f05左胫甲 | 0.4616 |
| f02右 / f06左胫甲 | 0.5507 |
| 支撑胫甲多数帧 | 0.8198 |

这不是随机逐帧缩放，它来自明确固定源区和投影目标；但使用同一2D甲片直接压缩54%或伸长28%，也不是完整的3D刚性装甲透视证明。最近邻采样会丢掉部分连接/装甲像素，固定UV和世界骨长通过无法证明装甲簇、膝踝遮挡、支撑腿承重读形正确。应优先改出少量可复用的倾斜/遮挡姿态源或更合理分段，维持认可形制；需要新增被遮挡部位时保留绘画来源。当前审图中的明显比例/观感结论交由视觉代理，不能由技术表自动给PASS。

## 未完成的原生像素要求

| 帧 | 可见像素 | 1–254半透明 | 其中250–254 |
|---|---:|---:|---:|
| f00 | 1203 | 1153 | 1026 |
| f01 | 1170 | 1120 | 994 |
| f02 | 1173 | 1123 | 998 |
| f03 | 1216 | 1165 | 1032 |
| f04 | 1205 | 1155 | 1025 |
| f05 | 1170 | 1119 | 993 |
| f06 | 1176 | 1126 | 998 |
| f07 | 1215 | 1164 | 1034 |

整条仍是连续Alpha候选，不能production pass。源Alpha候选本身也1219 / 1224可见像素非255，原生实体修整尚未完成。正确返修是在固定母稿修整实体轮廓/装甲像素簇，保留编辑来源，再统一导出；不得用批量阈值或逐帧独立形变掩盖。

## 证据与复现

本目录 `verify.py` 只读生产和固定ZIP，写入本目录 `evidence.json`。该证据保存32载荷、8帧SHA/Alpha、SpriteFrames内嵌像素、16条腿投影/真实末端、source→bind具体样本与51个重叠区域坐标。运行：`python art-source/ember/ta-review-v001/enemy-patrol-v002-independent/technical/verify.py`。

本报告没有把技术绑定通过、IK长度或制作方多循环证据作为美术通过结论。
