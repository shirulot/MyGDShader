# 敌人正向五动作：冻结审阅稿的美术逐帧审阅 v001

日期：2026-10-06。范围：四款已认可敌人、down 正向、待机/移动/攻击/受击/死亡，共 20 条 / 120 帧。root 已固定本批源图并重导；本文件绑定当前选中的源图、atlas、catalog 和 spec，**结论为 NEEDS_REVISION / PENDING_TA，不是 TA 通过记录**。

本批候选制作与技术导出已完成，可用于独立 Godot 动作审阅和问题定位。正式原生像素美术不通过。技术 PASS 仅覆盖列明的加载、固定格导出、资源与 GPU 播放等条件，不能推出身份、步态、拓扑、接地或二值 Alpha 通过。

## 固定版本与依据

- spec：`art-source/ember/enemy-sequences-v001/sequence_specs_v001.json`，SHA256 `225fd6333590f80e526f7422d58ac89ba74edd5d52607daf1a092f5cf2c368a7`。
- catalog：`assets/ember/characters/enemies_v001/sequence_catalog_v001.json`，SHA256 `568c280046c007c88240a40574592cc46e7f19b54ece1e0171a94807a3ba40e6`。
- 本审阅的 JSON 为每条动作保存选中源图、源 SHA256、atlas SHA256、原生位置测量及美术返修项；全部 20 条 `formal_art_pass=false`。
- 依据：`docs/shader-learning/art-style-standard-v002.md`、`ember-enemy-animation-standard-v001.md`、`ta-art-review-standard-v001.md`及 `art-source/ember/enemy-design-sheets-v001/design_catalog_v001.json` 的三视图/拆件设定。
- 全部动作画布 128×128，固定虚拟接地点 (64,104)，使用整条共同缩放/偏移；审阅者没有改 spec、atlas 或主玩法。

## 审阅方法与证据边界

- 已逐张查看 20 个选中实际 atlas、全部初稿源及 14 个修订候选、四款最终全 30 帧的 1× / 4× 联系图、巡逻移动 8 帧条。帧索引从 0 起，按 row-major。
- 已复看最终 Godot GPU 白底 Alpha 截图和 20 动作联系图。Godot 白底没有查看器里的黑/灰板；查看器显示的隐藏 RGB 不等于实际不透明背景。
- 源图最低像素采用只读检测 Alpha≥128，源格边界 Alpha>25。后文原生数据来自最终 catalog 的 Alpha≥0.1 可见 bbox，`baseline_bottom_px=y+height` 是下边缘坐标（不包含最后像素），**不是已登记的语义脚底/步足/履带接触点**。
- 工具、摆动脚、遮挡、压低/倒地会改变 bbox；最低点相同或面积相近不能证明刚性部件同一性。静态联系图和播放截图不能替代完整循环动态美术验收。
- 连续 Alpha 原样保留，实体有 250–254 等中间值；全 20 条正式实体 Alpha=0/255 闸门 FAIL。JSON 的 partial fraction 分母是整个 128² 画布，不能误称为实体中半透明比例。
- 本批没有同一可编辑原生母稿、linked cels 和逐帧像素精修的证据；AI 整条图、Nearest 缩小及可播放均仅表示候选阶段。没有程序逐帧齐底、重新居中、缩放、补画或阈值化修图。

## 当前阻塞项

1. **全套二值 Alpha 与同一可编辑原生母稿未完成。** 美术结论保持需修订；不以代码阈值或技术 PASS 掩盖。
2. **巡逻 move 是下一次生产闸门。** f0–2 同侧前脚、f3–4 换侧、f5–7 反复换侧，缺明确经过/抬升与均匀闭环。先修一角色、一方向、一动作再扩展。
3. **跨行支撑/注册仍漂移。** 最终巡逻 death 底排上移 8px、工蜂 death 约 7px、重装 death 5px；不能用逐帧 bbox 齐底消除证据。
4. **工蜂 hit 选中的 v001 f2 拓扑仍阻塞。** 抬起的锯/爪看似占用后步腿座，只有两步足清楚；新 v002 没解决，未选入。
5. **侦察 move/death 转子与落地仍阻塞。** move 多为三叶 Y；death f6/7 又像两叶横条，f3→f4 由底缘89上抬至82，最终85仍比 ground104 高19px。attack/hit v002四叶改善不代表整套四叶通过。
6. **跨动作中性姿态仍需同一部件复核。** 巡逻 f00 高46–50px、侦察 f00 总宽59–64px；bbox 是风险定位，不直接证明模型形变，但当前没有固定部件/中性联接证据。

## 最终选中 20 条动作

| 动作 | 选中源 | 最终实际判断与具体帧 | 返修与复审 |
|---|---|---|---|
| enemy_patrol_idle_down | v003 | 工具左右与双腿保持；选中v003没有v002的格界截断。实际原生底缘[104,104,102,102]，底排全体上移2px，待机接地未统一。 | 在同一原生母稿固定双脚支撑与躯干呼吸，保留底排关键姿态，修复后复验共同root。 |
| enemy_patrol_move_down | v001 | 工具侧正确；f0–2同侧前脚、f3–4换侧、f5–7反复换侧，经过/抬升相不清楚、节奏不均。f6底缘102对其他帧104，需按支撑脚解释，不能仅齐bbox。 | 作为首个生产闸门，先以同一可编辑母稿重做接触/下沉/经过/抬升与另一脚接触，再审完整闭环。 |
| enemy_patrol_attack_down | v003 | 选中v003抬枪/蓄势/后坐/回收可读、工具侧保持。f3头胸投影明显偏转，刚性头盔身份仍须复核；f3–5底缘103对f0–2的104，收回末帧没有回到相同支撑边缘。 | 固定头盔/胸甲形状与双脚接触；验f03释放位置和回到待机的衔接，不把晕染隐藏RGB当作实际不透明背景。 |
| enemy_patrol_hit_down | v002 | 选中v002：f0中性、f1轻倾、f2明显侧倾、f3回稳；双腿与工具侧保持。实际底缘[104,104,105,105]，底排残留1px定位差。 | 同一母稿固定支撑线和原臂工具，保留局部侧倾；弃用跨行反向退化的v003。 |
| enemy_patrol_death_down | v001 | 保留v001；侧倒/静止残骸可读，未见主要组件复制。f0–3底缘104，f4–7突然变96，末帧残骸比ground边缘高8px。v002首排越格已弃用。 | 重做格内侧倒到接地的关键姿态及唯一残骸，不将上移当作完成坠地。 |
| enemy_cutter_idle_down | v002 | 选中v002，四条短步腿与独立锯/爪基本可辨，锯观众左、爪观众右。底缘[104,104,106,106]，壳体与工具底排也下移，四腿实际接地点没有逐点登记。 | 固定四腿支撑与前部工具插座，区分工具臂和步腿；恢复同一接地线后复审微动。 |
| enemy_cutter_move_down | v003 | 选中v003的新atlas已保持全部8帧锯观众左、爪观众右，旧v001底排换边没有沿用。底缘[104,104,104,104,101,100,101,101]，底排上移3–4px；对角步相仍不足以通过。 | 保留已修好的工具安装侧，重做四腿交替支撑与均匀循环；拒绝镜像整身或逐帧齐底。 |
| enemy_cutter_attack_down | v002 | 选中v002：锯举起/前切/回收可读、工具侧正确。f1/f2锯臂靠近后腿插座，需证明是遮挡而非挂接迁移。底缘[105,105,105,101,100,101]，作用/回收底排上移4–5px。 | 按拆件图固定前部工具臂座、四步腿接地点，回收末帧衔接中性；独立检查f03作用点。 |
| enemy_cutter_hit_down | v001 | 保留v001；f2抬起的锯/爪看似占用两后腿安装座，下方仅两步足清楚，四腿拓扑无法证明。底缘[103,104,95,99]，f2/f3整体定位与接地也明显变化；v002未修好安装位而弃用。 | 同一模块母稿重做f2：明确四步腿与两独立工具臂座，登记受击时保留的支撑足，再做恢复过渡。 |
| enemy_cutter_death_down | v002 | 选中v002：壳体降低、步腿内折、传感器熄灭可读，锯爪各1。f0–3底缘约103–104，f4–7固定97，残骸上移约7px，接地未完成。 | 按同一ground参考重做压低、折腿和停住残骸，禁止靠逐帧bbox齐底掩盖。 |
| enemy_tracked_heavy_idle_down | v001 | 保留v001，双履带/单短炮身份稳定，底缘全104。活动较小，f2塔顶下沉投影可读但原生微动需要动态验收。 | 保持底盘及履带接地，在同一母稿整理有意义的待机微动与色阶稳定。 |
| enemy_tracked_heavy_move_down | v001 | 保留v001，双履带/单短炮保持，履带花纹小幅变化。底缘[105,105,105,105,104,104,105,104]；相对idle的104有1px切换差，履带相位完整闭环未通过。 | 固定底盘root和履带接触，整理履带连续相位，不以整图上下晃动代替推进。 |
| enemy_tracked_heavy_attack_down | v001 | 保留v001，单短炮蓄势/回收和小幅后坐可读，无新增武器；底缘全104。f03后坐辨识度有限，头部投影变化需以固定装甲确认。 | 实际播放复验f03释放可读性；射弹与闪光独立，固定装甲体量及接触。 |
| enemy_tracked_heavy_hit_down | v001 | 保留v001，塔体侧倾后回稳，双履带/单短炮保持。底缘全105，相对idle/attack的104有1px跨动作差。 | 统一底盘接触与跨动作root，保留关节侧倾，不将装甲轮廓重设计成受击形变。 |
| enemy_tracked_heavy_death_down | v002 | 选中v002，顶盖抬起后塌下、传感器熄灭、双履带/单短炮不复制。f0–3底缘105，f4–7变100，履带残骸跨行上移5px。 | 以履带固定支撑重做塔体塌陷与停止状态，末帧应能在ground参考上解释真实接地。 |
| enemy_scout_drone_idle_down | v001 | 保留v001，双风扇/双支臂/中央传感器稳定，四叶相位较清楚。底缘[80,79,78,79]，幅度2px；格间横向也有约1–3px摆动，不能以bbox证明固定机体。 | 锁定两个四叶转子及刚性支臂，按恒定ground投影点整理±1px悬浮和相位闭环。 |
| enemy_scout_drone_move_down | v002 | 选中v002，总风扇2和中央机体保持，底缘[80,80,80,80,80,80,81,80]较稳。但f0–7主要仍像三叶Y形转子，固定四叶未修好。 | 沿用固定外壳/支臂，以同一四叶部件制作转相；禁止把三叶Y视为四叶模糊相位通过。 |
| enemy_scout_drone_attack_down | v002 | 选中v002，各格四叶较v001明显改善，双风扇/传感器/原短探头保持。底缘[81,82,83,78,77,77]，底排回收整体偏高，末帧与中性80不一致。 | 保留四叶改善，固定地面投影root与原部件，整理前倾/释放/回到原悬浮高度；不新增枪架。 |
| enemy_scout_drone_hit_down | v002 | 选中v002，四叶较v001改善，左右倾斜可读，双风扇不复制。底缘[80,83,78,76]，f3回稳仍比中性高4px；部分遮挡下的四叶仍须原生母稿复核。 | 固定双支臂与四叶部件，按同一悬浮中性做受击后恢复，逐格证明叶片遮挡而非数量变化。 |
| enemy_scout_drone_death_down | v002 | 选中v002仍未满足：f0–5转子多像三叶Y，f6/7像横向两叶条。底缘[80,84,85,89,82,85,85,85]，f3→f4从89上抬到82；f7仍比ground104高19px，坠地未完成。 | 重做单向下降、支臂折叠、两个四叶转子停止和最终接地，唯一残骸不得复制风扇或叶片。 |

“可读”“保持”描述的是已看到的局部结果，不是整条正式通过。四款身份、像素与动作连续性仍需按固定原生母稿复审。

## 原生注册与跨动作诊断

下列数值来自绑定的最终 catalog。顺序为 f0 起；f00 bbox 为 [x,y,width,height]。死亡的压低可以改变高度，却不能用无解释的整排上移替代接地；悬浮机的底缘应按投影 root、倾斜和探头运动解释。

| 动作 | 原生 bbox 下边缘数组 | f00 可见 bbox |
|---|---|---|
| enemy_patrol_idle_down | 104, 104, 102, 102 | 44, 58, 40, 46 |
| enemy_patrol_move_down | 104, 104, 104, 104, 104, 104, 102, 104 | 44, 56, 40, 48 |
| enemy_patrol_attack_down | 104, 104, 104, 103, 103, 103 | 44, 56, 40, 48 |
| enemy_patrol_hit_down | 104, 104, 105, 105 | 44, 54, 40, 50 |
| enemy_patrol_death_down | 104, 104, 104, 104, 96, 96, 96, 96 | 44, 57, 41, 47 |
| enemy_cutter_idle_down | 104, 104, 106, 106 | 37, 65, 55, 39 |
| enemy_cutter_move_down | 104, 104, 104, 104, 101, 100, 101, 101 | 37, 64, 54, 40 |
| enemy_cutter_attack_down | 105, 105, 105, 101, 100, 101 | 37, 66, 55, 39 |
| enemy_cutter_hit_down | 103, 104, 95, 99 | 36, 66, 56, 37 |
| enemy_cutter_death_down | 104, 103, 104, 104, 97, 97, 97, 97 | 36, 66, 55, 38 |
| enemy_tracked_heavy_idle_down | 104, 104, 104, 104 | 25, 50, 78, 54 |
| enemy_tracked_heavy_move_down | 105, 105, 105, 105, 104, 104, 105, 104 | 24, 51, 80, 54 |
| enemy_tracked_heavy_attack_down | 104, 104, 104, 104, 104, 104 | 24, 50, 80, 54 |
| enemy_tracked_heavy_hit_down | 105, 105, 105, 105 | 24, 50, 80, 55 |
| enemy_tracked_heavy_death_down | 105, 105, 105, 105, 100, 100, 100, 100 | 24, 50, 80, 55 |
| enemy_scout_drone_idle_down | 80, 79, 78, 79 | 32, 55, 64, 25 |
| enemy_scout_drone_move_down | 80, 80, 80, 80, 80, 80, 81, 80 | 33, 54, 62, 26 |
| enemy_scout_drone_attack_down | 81, 82, 83, 78, 77, 77 | 34, 55, 60, 26 |
| enemy_scout_drone_hit_down | 80, 83, 78, 76 | 34, 54, 59, 26 |
| enemy_scout_drone_death_down | 80, 84, 85, 89, 82, 85, 85, 85 | 34, 54, 60, 26 |

- 巡逻五动作 f00：idle [44,58,40,46]、move/attack [44,56,40,48]、hit [44,54,40,50]、death [44,57,41,47]。上缘和总高跨动作有4px范围；须逐部件锁定头盔直径、胸甲体量和腿长，检查切动作跳变。
- 工蜂五动作 f00 下边缘103–105、高37–40；工具尖端最低点不能证明四腿接触。尤其 move f4–7、attack f3–5、hit f2/f3、death f4–7必须独立登记步足与工具座。
- 重装 f00 总宽78–80、下边缘104–105；跨动作有1px接地差。death f4–7履带残骸上移5px；履带接触应先固定，再允许塔体塌陷。
- 侦察 f00 总宽59–64，可能包含转子相位投影，但固定风扇舱/支臂/外壳同一性尚未证明。attack f5底缘77、hit f3为76均未回到中性80；death f7为85远未接地。不能逐帧按bbox拉伸成64px来假装修复。

## 修订候选与弃用记录

以下为源图级的历史比较，源局部最低 y 是 Alpha≥128 的最后可见像素，不能直接与上表原生 bbox 边缘混用。最终选择以本文件上表及 JSON 绑定为准。

| 动作 | 修订候选 | 当时判断 | 源格局部最低 y |
|---|---|---|---|
| enemy_patrol_idle_down | v003 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 610, 610, 585, 585 |
| enemy_patrol_hit_down | v002 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 610, 610, 615, 618 |
| enemy_patrol_attack_down | v003 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 490, 490, 490, 483, 483, 483 |
| enemy_patrol_death_down | v002 | REJECT_KEEP_V001 | 442, 442, 442, 442, 362, 362, 362, 362 |
| enemy_cutter_idle_down | v002 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 514, 514, 527, 527 |
| enemy_cutter_move_down | v003 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 393, 393, 396, 393, 372, 368, 372, 376 |
| enemy_cutter_attack_down | v002 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 452, 452, 452, 426, 421, 428 |
| enemy_cutter_hit_down | v002 | TOPOLOGY_NOT_FIXED_REMAIN_CANDIDATE | 543, 543, 465, 486 |
| enemy_cutter_death_down | v002 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 434, 428, 434, 434, 397, 397, 396, 395 |
| enemy_tracked_heavy_death_down | v002 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 404, 404, 404, 406, 386, 386, 386, 386 |
| enemy_scout_drone_move_down | v002 | ROTOR_COUNT_NOT_FIXED_REMAIN_CANDIDATE | 339, 339, 336, 339, 339, 339, 343, 338 |
| enemy_scout_drone_attack_down | v002 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 371, 382, 385, 354, 346, 344 |
| enemy_scout_drone_hit_down | v002 | PREFER_FOR_REVIEW_NOT_PRODUCTION_PASS | 425, 451, 417, 398 |
| enemy_scout_drone_death_down | v002 | LANDING_AND_ROTOR_NOT_FIXED_REMAIN_CANDIDATE | 327, 348, 358, 380, 339, 358, 358, 358 |

- 巡逻 idle v002 底排脚被格界截断，弃用；v003无裁边但最终底排仍上移2原生px。hit保留v002，v003跨行注册退化而弃用。
- 巡逻 death v002 f0–3 源格边界 Alpha>25 像素数 [143,144,154,230]，脚部越格，弃用并保留v001。
- 工蜂 move v001 f4–7 工具換边，弃用；已修身份的v003重导为新atlas，并绑定新SHA，未沿用旧cb8b9…图集。
- 工蜂 hit v002没有解决f2安装位，保留v001并显式阻塞。侦察 attack/hit v002四叶改善而选入；move/death v002仍有阻塞，仅作为固定审阅样稿保留。
- 其余 root 选中的修订均保留需修订状态。版本号更大不构成通过依据。

## 交付与复审

`visual_art_review_v001.json` 同时保存上述最终绑定、12个已查看证据文件的SHA、20条具体返修项和历史候选记录；初次atlas快照明确标为历史，不替代最终版本。

由root提交技术美术总监。本批状态 `FIXED_TA_REVIEW_SAMPLE / NEEDS_REVISION / PENDING_TA`；TA结论必须绑定本批SHA。再次改源图或导出后重登记并复审。下一轮首先用同一可编辑母稿修巡逻move完整循环，通过后才扩大生产范围；本批不宣称正式原生像素完成或整套敌人已接入游戏。
