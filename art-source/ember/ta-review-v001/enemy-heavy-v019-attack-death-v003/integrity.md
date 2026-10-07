# H19 v003 独立技术增量复审

**TECHNICAL_INCREMENTAL_PASS**。两处声明修改、实际逐像素差分与最小冷加载已闭合；未发现新来源、导出、所有权或资源加载P2。限定重装机七新向attack/death14条98帧，旧down两条14帧保持。最终形体/播放由根另行回执，本报告不扩大动作或单位范围。

## 固定包与基线

| 对象 | 独立绑定 |
|---|---|
| `deliveries/enemy_heavy_attack_death_v019_v003_2026-10-07.zip` | SHA `18666a8a60b03a5d90ca96d0ae9e49db05f2384d4cf5e05b43fc27895c1935a4`；6,236,316 B；275条目=274载荷+manifest |
| `manifest.json` | SHA `fe7a50ab1cfa2e539d174c06feb341e707cb007769a47a09e614cc6d9032c7c9`；274项哈希/长度全齐 |
| `output/catalog.json` | SHA `d6c619f962c775cc910551763ed8d15c9677b11fad9844569e7faf9850a2e82b` |
| `rig.json` | SHA `fa1f33f6e3847ebad1b82fae75b31115a985fad603919f98ee9c03fd42e31095` |
| `output/enemy_tracked_heavy_attack_death_v019.tres` | SHA `060191383db833247427e73a976c295b1f3de4d28043450d1bfd57cc97519dfd` |
| 已审v002基线ZIP | SHA `c16edaeb70592d03cd8426a584399d815bb00fd7791e3242a606abdf9ff8d192` |

只读解包到独占 `technical-package/`，验证运行在 `technical-cold-load/`副本。包内16条、112PNG、16atlas，128×128/root(64,104)，attack6/death8、10FPS、单次。112PNG哈希、atlas格RGBA、FPS/loop/count、rig/TRES绑定均一致；全帧二值Alpha，atlas差0。收尾核275包内成员及ZIP未变。

## 实际修订账本

独立逐112帧RGBA及文件字节比较，实际**17帧、106个RGBA像素**变化，与包内 `qa/revision_audit_v003.json` 的坐标、before/after、数量逐项一致；其余**95帧逐字节保持**。

| 动作 | 变动帧及各帧像素数 |
|---|---|
| SW attack | F03/F04：2/2 |
| SW death | F01/F02/F03：2/2/2；F04/F05/F06/F07：4/4/4/4 |
| E attack | F01/F03/F04：12/24/12 |
| E death | F03/F04/F05/F06/F07：4/7/7/7/7 |

仅这四张atlas改变；其余六方向12atlas字节保持，包含down。11个source文件（八canonical、新隐藏母稿、prompt、registration）全部字节保持。去除新增 `fixed_receiver_pixels`/`socket_clip_rect` 字段后，rig所有旧字段与v002完整相同；actions、preserved注册、全部16条catalog poses不变。新14中性以及旧2中性共16帧与各原source RGBA差0。

证据：`technical-incremental-integrity.json`、`technical-summary.json`；ledger由实际PNG重算，未只复述作者PASS。原身份、原生成源和旧down v012来源完整性沿用已审v002证据，当前字节保持证明其仍适用；不重造v001验收。

## 两处修订的源/几何闭环

**SW：** 仅原source(46,76)/(46,77)从tower归fixed，原RGBA不变。它们位于原gun polygon之外，fixed循环之后的gun赋值不会覆盖这两点；其余所有权没有改变。原死亡F04/F06/F07输出(46,89)/(46,90)现在Alpha0，原两点留在固定坐标(46,76)/(46,77)；不是删掉源RGB，也不是逐帧抹条。塔体及炮管运动表不变，固定护板职责不再随塔下沉。

**E：** socket新clip `[92,73,3,14]` 即x92/93/94、y73—86；shader在原ownership×原实体Alpha裁样上另加半开几何范围。仍按原target bounds `[92,73,8,14]` 和同源source rect `[1084,675.75,59,36.75]`采样，**没有把内壁贴图拉伸进新3px宽区**。所有x98都在socket禁止区。

`attack_right` F03的(98,83)/(98,84)已Alpha0；实际新枪前缘x96显示原gun源(98,83)/(98,84)的暗色RGBA(2,5,12,255)/(3,7,12,255)，符合后坐−2px。这关闭了v002在原前沿固定露出新白色socket纹理的来源问题。其它方向clip默认全画布，原gun mask/短炮刚性和履带固定职责保持。

限定源归属交叉 `technical-scope-crosscheck.json` 由动画技术代理独立完成；本代理另对SW/E 28帧做增量CPU重建、点源溯源和headless实际mask/pose读回，两处规则与真实PNG一致。原完整hidden_mount层在两向增量重建仍可见0，余向字节保持；没有新增完整安装座的视觉验收。

## CPU残差与不变范围

SW/E 28帧只重建两新增规则，仍有原基线3个RGBA残差：SW death F02(56,86)、F03(48,81)旋转枪覆盖边界；E death F01(84,65)灯窗整数取整。Alpha残差0，没有新残差。SE旧9点所在帧均字节保持，原v002全部12个残差坐标实际RGBA也都保持。

因此本轮不把完整CPU重建写成零差：基线12残差的源邻样/覆盖解释仍适用，最大单RGB差60照原报告保留；当前实测是28帧3残差，其余9点按不变帧绑定继承。未重做98帧全CPU流水或完整GPU矩阵。见 `technical-two-direction-reconstruction.json`、`technical-incremental-integrity.json` 的 baseline_12_residual_pixels，以及v002 `technical-cpu-residual-classification.json`。

## 独立最小冷验证和作者证据

独立cold **PASS**：36个必要资源由固定包逐字节复制到新Godot4.7.2 headless工程并重新import；加载16动画112格，内嵌RGBA逐格等atlas，region/duration1/10FPS/loop=false及canvas/root一致。预览两个AnimatedSprite2D实例化成功，nearest、centered=false，无资源或脚本错误。

仅对修订的SW/E两套rig做CPU实例化：6张实际R8所有权mask的red通道与独立像素中心所有权比较差0；28个运行pose与catalog一致。其余方向以字节/参数保持及v002已审证据绑定。未独立渲染GPU图、自然播放完成事件或16切向。

证据：`technical-cold-dependency-binding.json`、`technical-minimal-cold-load.json`、`technical-cold-engine-log.txt`、`technical-runtime-cpu-readback.json`。

作者196新深浅GPU+14旧TRES记录=210、32播放器/16切向、pixel/pose/revision audit均绑定当前catalog SHA，记录PASS；本代理只核记录计数和归属，**没有重跑其完整GPU/播放/切向矩阵**。独立revision账本比较另有实际像素证据。绑定见 `technical-author-evidence-binding.json`。

## 元数据与通过边界

catalog.version/export已改 `v019-heavy-attack-death`，project应用名为heavy attack and death v019，preview注释及export print正确指attack/death；检查当前代码/JSON/project/README未再命中 `v019-drone`、`HEAVY_IDLE_HIT`、`idle and hit v015`旧标签。SOURCE_RECEIPT的14条new_actions仍正确。

本轮技术增量通过仅绑定上述固定v003。两处可见问题的美术关闭及其余既有动作表现由根综合；不将旧v002技术检查改写为整体美术通过。
