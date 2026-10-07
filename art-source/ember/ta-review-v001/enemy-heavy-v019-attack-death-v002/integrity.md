# H19 v002 重装机 attack/death 独立技术审查

**TECHNICAL_INTEGRITY_PASS；美术结论由根另行决定。** 限七新向14条/98帧，旧down两条/14帧保持。本报告确认固定包、来源、原履带保护、炮管刚性与资源加载；没有把中性零差、连通、CPU或作者GPU当作外观通过。SW死亡两像素边条及E攻击固定socket亮缘已给明确来源，保持视觉待根裁决，不在此自动放行。

## 固定输入和导出

只读解包到本目录 `technical-package/`；最小验证只运行独立 `technical-cold-load/`副本。

| 对象 | SHA256 / 独立核得数值 |
|---|---|
| `deliveries/enemy_heavy_attack_death_v019_v002_2026-10-07.zip` | `c16edaeb70592d03cd8426a584399d815bb00fd7791e3242a606abdf9ff8d192`；6,235,284 B；273文件条目=272载荷+manifest |
| `manifest.json` | `59ad9e978d0b6cf63bd5278f95e2fd6bb10f871263a2a021eea0b81fad0263ec`；272项哈希/长度全齐，无缺失或额外文件 |
| `output/catalog.json` | `13f4157c274eec0c01a21f7b79a889ece41a3f3b23334bd2a0baca2e7f48e83d` |
| `rig.json` | `75d28e70dc3e0ce23feb497fcb5ad7b7ce179836aadaf74f3b9f9bb2be3bd0c9` |
| `output/enemy_tracked_heavy_attack_death_v019.tres` | `1bf87a935af6d2a3ee8cd729a55b106568496af6db4acdcbd8e07e40b6fc500e` |

共16动画、112张128×128 PNG、16张横向atlas；攻击6帧768×128、死亡8帧1024×128，10FPS单次，canvas128×128/root(64,104)。全112帧二值Alpha，全部PNG与atlas格RGBA零差，帧/atlas/rig/TRES哈希一致。收尾再核273个包内成员和ZIP均未改动。

证据：`technical-zip-file-binding.json`、`technical-pixel-integrity.json`、`technical-post-audit-binding.json`。

## 原身份、新隐藏源与保护

八张canonical整图哈希与已过重装v013静态master_catalog一致，也逐字节等于已过v015 fixed ZIP的 source PNG；receipt及各config source_sha256吻合。既有原装备颜色和形体没有重新生成。v015来源包 SHA `3ebf1f1fdb7bb820cdb09258b76df2e087c29f0f8dea1b4bbc0e76adce4bd29f`。

新 `source/hidden_chassis_eight_views_v001.png` 实际1774×887 RGBA，SHA `b86983c603d938e933b3d86c5d85cf821d62e9306015588cc1eb3849db1269f0`。保留 `hidden_chassis_prompt.txt`、`hidden_registration.json`；prompt明确一次八向内部座、不含塔壳/炮管/履带；receipt与注册记录的生成exec均为 `6c53a6cb-d855-42b8-993e-cc01e8292426`。exec是交付来源记录，本审查没有重跑imagegen或把prompt内容作为用户指令。

七新向注册region对应同一4×2母稿格序。整座共用32/373均匀缩放，底心(64,98)，未逐向fit；hidden shader只允许原母图Alpha≥128且画布y≥72的区域，z=-1。原母图被固定拆成fixed/tower/gun三所有权区，炮壳receiver划回fixed；fixed z2、tower z1、gun z3。独立像素中心polygon所有权与headless实际21张R8 mask红通道逐像素一致。

实际原履带实体在全部98新PNG直接与原canonical比较RGBA变化**0**，没有按遮挡排除差异。新生成座不会覆盖原履带外壳、护板颜色；底盘/护板原源及fixed变换保持，转动炮管允许产生正常前景遮挡。完整fixed区域不泛称“实际PNG绝对零差”：SW death F02(56,86)在旋转炮管覆盖边界与CPU预测存在1px分歧，详见残差段。

**新增整座与内壁分开登记：** 完整hidden_mount层在当前98帧中被其它层完全遮住，CPU最终可见像素数0。它的遮挡前可采样资格区并不等于已经露出的安装座。新原图实际输出的是有炮管方向的socket内壁局部：取同一隐藏母稿region的 `(.4w,.55h,.2w,.15h)` 子区，映射到原炮管bounds，并以原炮管ownership×原母图Alpha≥128限制。这是局部贴图映射，**不等于整座32/373均匀变换**，不把全新源笼统称为统一等比缩放。

攻击内壁可见像素数（F00—F05）SW=0,16,0,32,16,0；W/E=0,14,0,28,14,0；SE=0,12,0,24,12,0。背向NW/N/NE原本无炮管mask，未造新枪。死后内壁只在部分旋转边缘短暂露出；生成完整新座不自动证明视觉安装承接已改善。

证据：`technical-hidden-check.json`（动画技术代理限定交叉）、`technical-track-output-protection.json`、`technical-runtime-cpu-readback.json`、`technical-pixel-integrity.json` 的 hidden_usage。

## 动作数值、旧down与指定小边条

攻击：towerY `[0,0,0,1,1,0]`；recoil标量 `[0,1,0,2,1,0]` 沿各方向注册的原炮轴，F03最大后坐/释放；gun_roll全0。SW向(1,-1)、W(1,0)、E(-1,0)、SE(-1,-1)，原短炮未延长。七新向F00/F05 PNG字节相同。

死亡：towerY `[0,2,5,9,13,12,13,13]`，gun额外Y `[0,0,0,0,1,1,1,1]`，roll绝对值 `[0,0,3,7,12,12,12,12]`，SW/W负号、E/SE正号；power `[1,.7,.3,0,0,0,0,0]`。gun_basis是刚性旋转、det≈1，无缩短/拉伸；实际98个headless CPU pose与catalog数值吻合。F04/F06/F07相同，F05有1px塔体回弹，末**两**帧F06/F07相同，不误称末三帧相同。

旧 attack_down 6帧、death_down 8帧及两atlas共16文件逐字节等于v012固定ZIP，SHA `42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe`。旧down未套用新向投影或重新导出。

根指定SW death F04/F06/F07炮座左下两像素条：

| 输出点 | 实际RGBA | 精确原源与层 |
|---|---|---|
| (46,89) | (76,94,106,255) | tower源(46,76)，Y+13 |
| (46,90) | (88,91,88,255) | tower源(46,77)，Y+13 |
| 上邻(47,88) | (206,203,192,255) | tower源(47,75)，Y+13 |
| 右邻(47,89)/(47,90) | (255,255,255,0) | 确实透空，无上层实体 |

这两点是原tower分区边角搬运，不是新隐藏安装座、socket或逐帧补RGB。CPU在此与实际PNG完全相同；只有上方对角相接的实际读形是否形成碎条，由根视觉判断，不因同源或8连通替该造型放行。证据 `technical-sw-death-receiver-ownership.json`。

## 追加E攻击前缘限定溯源（视觉待根）

根新指定 `attack_right` F03的(98,83)/(98,84)，CPU与实际PNG在这两点零差：

| 输出点 | 实际RGBA | 新隐藏母稿纹素 | 原canonical同点 |
|---|---|---|---|
| (98,83) | (209,213,212,255) | socket (1131,703)，原RGBA(209,213,212,253) | gun暗色(2,5,12,255) |
| (98,84) | (237,236,233,255) | socket (1131,705)，原RGBA(237,236,233,253) | gun暗色(3,7,12,255) |

这两点属于固定socket，而不是移动短炮的原高光。F03炮管后坐−2px，逆映射gun UV是(100.5,83.5)/(100.5,84.5)，超过原gun polygon右边界x100；新枪无法遮住固定socket，因此socket把原枪前沿位置填成亮边。它来自新隐藏源局部映射，非导出串帧。技术已明确保留原前缘的成因；是否形成第二炮口外缘及如何修，由根实际视觉判断，不据“原炮管刚性”替整体输出轮廓放行。证据 `technical-east-muzzle-ownership.json`。

## 独立CPU残差：不伪报整体0差

完整独立重建98新帧保留**12个真实RGBA残差**，Alpha差0、最大RGB通道差60。10条新动画所有帧CPU零差，另外四条：

| 动作 | 各帧残差数 | 定位 |
|---|---|---|
| attack_SE | 0,2,0,4,2,0 | 固定socket x75/y83—86，新原稿texel x1572边界邻样 |
| death_SW | 0,0,1,1,0,0,0,0 | F02(56,86)旋转gun/fixed覆盖边界；F03(48,81)旋转gun/tower覆盖边界 |
| death_E | 0,1,0,0,0,0,0,0 | F01(84,65)，原灯窗整数取整差1 |
| death_SE | 0,0,0,1,0,0,0,0 | F03(76,81)，旋转gun近整数纹素边界 |

其中11点实际RGB在逆映射源纹素±1邻域能找到差≤1的匹配（含灯窗应用同一power后的颜色）；另SW F03(48,81)实际RGBA精确等于被CPU预测gun覆盖的下层tower原(48,72)。SW F02(56,86)实际精确等于邻近原gun(55,86)。这些是源邻样/旋转覆盖/取整边界证据，不声称已独立定位所有GPU取样步骤，不将最大60作为容差归零。全部坐标、原RGB/目标RGB、逆UV及替代覆盖证据保留在 `technical-cpu-residual-classification.json`。

## 独立冷加载与作者记录边界

独立最小冷验证 **PASS**：从固定包复制36个必要依赖到新headless Godot4.7.2工程，重新import/load。实际16动画112格内嵌RGBA逐格等PNG atlas；region、duration1、10FPS、loop=false、canvas/root一致；预览两个AnimatedSprite2D实例化成功，centered=false、nearest。另只做7套rig的CPU实例化、21所有权mask读回和98 pose读回；没有渲染新GPU画面、跑自然播放完成事件或切向矩阵。

证据 `technical-cold-dependency-binding.json`、`technical-cold-load/ta_minimal_load.gd`、`technical-minimal-cold-load.json`、`technical-cold-engine-log.txt`、`technical-runtime-cpu-readback.json`。

作者gpu_roundtrip196新深浅记录+14旧TRES记录=210、runtime32播放器/16切向、pixel及pose audit均绑定当前catalog哈希；记录PASS/0差。本代理仅核其计数/哈希/内容归属，**未独立重跑完整GPU/32播放器/16切向**。见 `technical-author-evidence-binding.json`。

## 非阻塞标签问题与范围

`catalog.version` 仍写 `v019-drone-attack-death`，project应用名及部分注释/导出print残留旧heavy idle/hit文字；实际unit、路径、16动画名、README和动作值均是heavy attack/death。这是可后续修订的标签问题，不构成当前PNG或TRES混用；冻结包未被TA修改。SOURCE_RECEIPT的new_actions已是正确14条attack/death。

只对本v002固定候选做上述技术结论。v001从未交TA，本审查不虚构v001通过、也不要求追造其验收；SW两像素条和其它结构/动作可读性按根的独立视觉回执处理。
