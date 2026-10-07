# D18 v001 侦察机 attack/death 独立技术审查

结论：**TECHNICAL_INTEGRITY_PASS**。限定七新向 attack/death 的14条、98帧；旧down两条14帧保持。未发现本轮来源、保护区、导出或资源加载 P2。外观、动作意图、死亡重量及连续播放由根/视觉代理另审；本报告不把技术结果替代美术通过。

## 固定包与清单

只读从固定ZIP解至本报告同目录 `technical-package/`，测试副本另在 `technical-cold-load/`；未修改生产或固定包。

| 对象 | 独立核得 SHA256 / 数量 |
|---|---|
| `deliveries/enemy_drone_attack_death_v018_v001_2026-10-07.zip` | `3da0700799bbc002601a77887912a64d67c7582c10ed86a1ccb64b1cd4661e7d`；2,773,657 B；263文件条目，262载荷+manifest |
| `manifest.json` | `4f6a774ac405bb4d2bdd562e7518682d3fb13ac2173da08fb0a1efeb0ade9447`；262项无缺失、额外或哈希不符 |
| `output/catalog.json` | `7c50cffd747c1fb3dfdd87ade24d2d0dacc72e53c1512145930e644f89959432` |
| `rig.json` | `355de5ad05ee2440dc12081ff35e9abd9e9bacb9430bb48637dd79039059b6d4` |
| `output/enemy_scout_drone_attack_death_v018.tres` | `a941da3c91b69984fa614ed71b52590deec5e7d852c8174a31ec36476683c143` |

实际16条、112张128×128 PNG、16张横向atlas。攻击6帧、768×128；死亡8帧、1024×128。全112帧二值Alpha；PNG与atlas格RGBA零差，catalog帧/atlas/rig/TRES哈希均吻合。收尾再次核263个解包成员及ZIP未变（`technical-post-audit-binding.json`）。

## 来源与旧稿保持

- 八张整壳PNG逐字节等于已过 s004 固定包对应源，未重新生成、镜像或补壳体RGB。对应来源ZIP：`enemy_drone_seven_directions_v013_s004_2026-10-06.zip`，SHA `3a6dc8a5ab9c16dc5e71d083568768ff3cabefae2675d5385e552149acb79342`。
- `source/rotor_well_master.png` 逐字节等于 v011 原稿，SHA `8824eeff102796d523fa8fab1f17f90c5716b7f34097987c0d5ea8151c2a3a94`。转子UV矩形 `[223,165,583,584]`、内腔 `[1000,192,535,528]` 与v011一致。来源ZIP SHA `13a4942d34d0ceabac7473c1689aa4784bc0c6f1555ff68817ed9d93159dab3e`。
- 旧 `attack_down` 6帧、`death_down` 8帧及两atlas，共16文件逐字节等于v012固定包。来源ZIP SHA `42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe`。旧down死亡局部3px折舱未被新七向的刚性落差方案覆盖。

证据：`technical-pixel-integrity.json` 的 sources/fan_source/preserved_down；来源包也独立锁SHA。

## 新动作变换、原探头和保护区

逐98帧对照源图、注册几何、catalog pose和实际PNG。壳体basis恒identity、只有整数Y平移；风口之外仅声明的原探头搬运区和灯窗可变。保护区可见RGBA差0、透明RGB差0、移动端片之外的Alpha差0。左右解剖转子角度符号保持相反；所有28组动作/风口的轴心采样颜色恒 `[55,39,19,255]`。

攻击6@10FPS、单次：bodyY `[0,0,1,2,1,0]`；转子角度 `[0,22.5,45,67.5,22.5,0]`。七向F00/F05 PNG逐字节相同。SW/SE相对body的probeY也是 `[0,0,1,2,1,0]`，最大相对伸出2px，区别于body同时下移2px。

| 方向 | 原图端片ROI（x,y,w,h） | 端片原实体像素 | 注册灯窗 |
|---|---|---:|---|
| SW/down_left | (55,75,6,5) | 26 | (57,67,2,2) |
| SE/down_right | (67,75,6,5) | 25 | (69,67,2,2) |
| E/right | 空 | 0 | (73,67,1,2) |
| W/NW/N/NE | 空 | 0 | 空 |

代码将同一原壳纹理ROI用 `probe_tip.gdshader` 叠绘并平移；原位置端片仍留在整壳，形成固定基段。没有新增探头RGB或抹掉基段。固定壳体内结构是否能读为叉架/套筒属于视觉判断，本技术报告仅确认固定基段与移动端片的同源关系。98帧端片RGBA独立重建差0；侧后五向无探头sprite/ROI，不另造武器。

死亡8@10FPS、单次：转子 `[0,25,42,52,58,60,60,60]`，power `[1,.6,.2,0,0,0,0,0]`。F03起注册灯窗原RGB乘0.3再取整，SW4/SE4/E2实体像素逐帧重建差0；背侧未注册窗口不会凭材质暗红、黄铜轴心颜色被强行灭黑。这里“灭灯”指注册传感灯变暗，power0并不输出纯黑RGB。

| 死亡方向 | 独立核得bodyY（F00—F07） | 终点落差 |
|---|---|---:|
| SW/SE | 0,3,7,12,18,21,21,21 | 21 |
| W/E | 0,3,7,13,18,22,22,22 | 22 |
| NW/NE | 0,3,7,12,17,20,20,20 | 20 |
| N | 0,3,8,15,21,25,25,25 | 25 |

落差等于104减各源Alpha bbox的排他下沿，末三帧PNG字节完全一致。终态Alpha bbox下沿104，实体末行103；这是注册边界证据，不能单独证明真实接地或重量。七向壳/转子/探头一起刚性下落，probe相对位移0，没有旧down的局部舱下折。

## CPU采样残差（如实保留）

CPU重建包含原壳、风口井/转子、原端片、灯窗，不声称完整RGBA重建零差。七向各自残差数相同：

| 动作 | 各帧CPU→实际PNG残差像素数 | 每向合计 |
|---|---|---:|
| attack | 32,25,24,25,25,32 | 163 |
| death | 32,14,23,21,21,14,14,14 | 153 |

98帧总2212个残差，全部位于两风口内；残差Alpha差0，最大单RGB通道差49，不是按49容差当作零差。每点实际RGB能在该点逆映射源纹素的±1邻域内找到RGB差≤1的井/转子纹素；逐点UV、候选源纹素及数值留在 `technical-pixel-integrity.json`。此结果支持邻近采样差的解释；未独立运行GPU矩阵，因此不宣称已定位所有渲染取样细节。风口以外、探头、灯窗独立重建则确为0差。

## 独立冷加载与作者证据边界

独立最小冷验证 **PASS**：固定包35个必要资源复制到新工程副本，在Godot4.7.2 headless重新import；实际加载16动画、112个AtlasTexture格，逐格内嵌RGBA等PNG atlas，region、duration1、FPS10、loop=false、128×128和root(64,104)均一致。`preview.tscn`实例化成功，两个AnimatedSprite2D均centered=false、nearest，无资源/脚本错误。此验证不包含GPU画面、自然播放完成事件或转向矩阵。

证据：`technical-cold-dependency-binding.json`、`technical-cold-load/ta_minimal_load.gd`、`technical-minimal-cold-load.json`、`technical-cold-engine-log.txt`。

作者 `qa/gpu_roundtrip.json` 的196新深浅底记录+14旧记录（总210），`qa/runtime.json` 的32播放器/16转向，以及pixel/pose audit均独立绑定当前catalog SHA。它们记录PASS/0差；本代理只核记录归属和计数，**未独立重跑210 GPU、32播放器或16转向**，不把JSON记录表述为逐张GPU画面的独立检查。绑定见 `technical-author-evidence-binding.json`。

本轮不要求新七向死亡逐帧复刻旧down，技术范围已明确为刚性坠落。侧后attack的动作读感、原探头承接和死亡姿态由根/视觉独立回执决定。只核本候选14条新动作，不扩大其它单位或动作的通过范围。
