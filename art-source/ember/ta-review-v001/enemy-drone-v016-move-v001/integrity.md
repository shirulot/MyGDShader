# Drone v016 move review v001 — 独立技术审计

结论：**TECHNICAL_INTEGRITY_PASS，未发现本项P2。** 六新向48帧的固定来源、风口外保护、Alpha/轴心稳定、64帧PNG/atlas/TRES与最小冷加载通过。独立CPU对旋转取样存在风口内残差，具体边界如下，**不能称CPU全帧重建零差或本代理独立GPU重跑**。本报告不替代旋转观感/末首/方向语义视觉审查，不批准idle/hit/attack/death。

审查日期2026-10-07。固定ZIP只读解至本TA目录 `package/`；冷加载在额外 `cold-load/` 副本完成，没有改生产、冻结ZIP或解包载荷。

## 固定对象

|对象|实际SHA-256 / 数量|
|---|---|
|`art-source/ember/deliveries/enemy_drone_eight_moves_v016_v001_2026-10-07.zip`|`fde467201be49929e894d000dcad974bb49854b752f3341eef0ef04610c4ba9a`；1,686,297 B；164文件条目|
|`manifest.json`|`8a4ca7305ca52e041289f68711935bcbb97cc93ac0666f88011e854c67e6515e`；163载荷；缺失/额外/hash或字节数错误0|
|`output/catalog.json`|`9b727a62f58841b24b66d509fdfd9ddd30f1853c458d5f59e1ccf73635934cde`|
|`rig.json`|`1499720296fbac82846081195ae4d02009c3dd591977b8484d10b79d8823cbb3`|
|`output/enemy_scout_drone_move_v016.tres`|`2955d915fa1525b1ede8dfe53a116b90ca54c3ee09c4fd31f7a2b119702bf419`；具体路径以catalog.tres为准|

新动作SW/W/NW/N/NE/E各8帧；旧S/SE各8帧原样保留。64个128×128 PNG、8张1024×128 atlas逐格RGBA零差，frame/atlas SHA与catalog一致，全部Alpha0/255。catalog rig/TRES哈希正确，canvas128×128/root(64,104)。

## 独立固定来源

直接读取下列旧固定ZIP对照，而非活动目录：

- s004静态ZIP `enemy_drone_seven_directions_v013_s004_2026-10-06.zip` SHA `3a6dc8a5ab9c16dc5e71d083568768ff3cabefae2675d5385e552149acb79342`：当前八张source壳PNG与各 `neutral_{direction}.png` 逐字节相同。
- v011 ZIP `enemy_drone_actions_v011_2026-10-06.zip` SHA `13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e`：`source/rotor_well_master.png`逐字节相同，SHA `8824eeff102796d523fa8fab1f17f90c5716b7f34097987c0d5ea8151c2a3a94`；rotor rect(223,165,583,584)、well rect(1000,192,535,528)与该旧rig登记相同。
- v012总包SHA `42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe`，及SE pilot ZIP SHA `2ef84aaa45b2970bf4db9c5abdf4f845f4d65be9878c97d929701d090d4e37f1`：旧S/SE的16帧PNG+2atlas共18文件逐字节相同。

四个参考ZIP的实际SHA都与 `SOURCE_RECEIPT.json`一致。源图没有逐帧更换，没有镜像、按帧bbox重注册或使用v011-r1探头实验；本代理核的是现存固定源码/原图及输出关系，不独立追溯历史生成服务调用。

## 风口保护和固定轴心

独立按像素中心重算两个椭圆风口，半径均(6.5,4.5)。每帧先去除声明hover `[0,−1,−1,0,1,1,0,0]` 比较s004源壳：**48新帧风口外全部RGBA差0，整张Alpha差0**。透明隐藏RGB也逐项比较，风口外差仍为0。圆舱边框、支架、中舱、暗红槽和底探头均由整壳保留，没有风口以外未声明的可见变体。

两风口合计178个像素位置；neutral相对s004可见RGBA改动SW/W/NW/NE/E各178，N为177，全部位于风口内。这是已声明的固定v011 rotor/well内部替换，不是整机重画。

|方向|解剖右风口中心、spin|解剖左风口中心、spin|
|---|---|---|
|SW|(48.5,58.5), +1|(79.5,69.5), −1|
|W|(64.5,57.5), +1|(64.5,72.5), −1|
|NW|(79.5,58.5), +1|(48.5,70.5), −1|
|N|(85.5,64.5), +1|(41.5,64.5), −1|
|NE|(79.5,70.5), +1|(48.5,58.5), −1|
|E|(64.5,72.5), +1|(64.5,57.5), −1|

两转子都先在自身平面旋转，随后由plane scale=(1,4.5/6.5)投影，轴不随局部旋转移动；只有整机hover移动轴的屏幕y。12个轴心在全部8帧采样RGBA均固定为 **(55,39,19,255)**。每帧角为index×11.25°×spin，catalog逐帧角度/中心/半径/hover/root与rig声明一致，左右解剖符号跨方向始终相反。这里核的是代码/数据和像素稳定；摄像机方向语义/可见投影仍须结合独立视觉回执。

## CPU旋转取样残差：准确保留

TA未调用作者rig/export/GPU，用Python双精度逆旋转、原UV矩形、最近邻floor源纹素与Alpha≥128硬覆盖，在固定椭圆内重建well+rotor；椭圆外保留原壳。CPU与实际PNG的全RGBA残差 **每个新方向均为F00…F07：[32,17,25,22,24,21,25,28]**，每向194、六向共1164像素次。

所有残差都在风口内，Alpha没有残差。不能将它们只称1色阶误差：CPU选点与实际像素的RGB最大通道差可达49。实际RGBA都可以匹配CPU所选rotor或well原纹素的 **±1源像素邻域** 内不透明纹素，RGB逐通道差≤1；未匹配数0。UV、理论采样点、原RGBA、实际RGBA和邻域匹配全量保留在 `independent-pixel-integrity.json` / `cpu-residual-classification.json`。

这些差异与原大图经GPU UV注册/最近邻边界选择的差别相符，但本代理没有独立live-rig GPU对照，不能据邻域匹配宣称已证明其具体GPU原因或改写CPU残差为0。本次外壳/Alpha/轴心的独立保护检查不依赖该取样近似；确切well/rotor完整渲染一致性仍只有作者GPU记录。本技术项未发现跨出风口或无来源的新实体像素风险，转子内形态和循环观感另由实际视觉审查决定。

90°只是八步的几何角累计。v011原图四叶不同方向的纹理/光照并非rawRGBA严格四重对称，因此本报告没有把“4叶×90°”写成末首必然完美；末首需要实际图像及播放审查。

## 最小冷加载与作者记录

**独立实测 PASS**：固定包34个必要入口/源/atlas/TRES载荷复制到TA独占 `cold-load/`，Godot4.7.2 headless冷导入、加载TRES、实例化 `preview.tscn`。实际8 clips/64格，8帧8FPS loop、duration=1、128×128 region、1024×128嵌入atlas逐格RGBA与PNG atlas一致；root/canvas正确，两个显示sprite为nearest/centered=false。错误0。没有独立执行GPU截图、自然循环或方向切换矩阵。

**作者结果仅绑定，NOT_RUN_BY_TA**：`qa/gpu_roundtrip.json` 有96条六新向黑白底GPU记录，加16条旧S/SE记录；包内没有逐次GPU PNG档。`qa/runtime.json` 含16正常/慢速播放器的循环和全帧覆盖记录、8条切向记录。上述文件连同 `qa/pixel_audit.json` / `qa/rotor_audit.json` 的SHA与固定manifest相符，均绑定当前catalog `9b727a…`。没有将作者96GPU/16loops/8turns描述为本代理重跑或连续观看。

## TA证据

- `zip-file-binding.json`：固定ZIP及164成员。
- `independent-pixel-integrity.json` / `audit_integrity.py`：四个旧固定ZIP、来源字节、64PNG/atlas、48新帧外壳/Alpha、轴心及CPU残差。
- `cpu-residual-classification.json`：保留原CPU差值的邻域源纹素诊断。
- `minimal-cold-load.json` / `cold-load/ta_minimal_load.gd`：本代理实际最小8clip/64frame冷加载。
- `author-evidence-binding.json`：96GPU记录、16loops、8turns仅绑定。

收尾再次核163载荷SHA不变。可合并综合TA回执，保留上述CPU精确渲染与播放证据边界。
