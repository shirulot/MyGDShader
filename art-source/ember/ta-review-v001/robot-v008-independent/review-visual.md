# 机器人 fixed-rig v008 独立静态与过渡审查

快照：2026-10-06 17:29（UTC+08:00）。审查者：TA 子审查代理 `style_specs`。未改生产文件，未运行重渲染脚本。

**结论：本固定版本的八帧静态身份与关键相邻帧过渡可接受，未发现需要退回源稿的异常形变或断接阻塞项。** 本报告没有独立观看正常8 FPS完整循环，最终动画通过须与根代理的实际播放器审查合并；不凭制作方PASS、骨长或连通域直接给动画总通过。

## 固定范围及证据

仅审查 down 行走 F00–F07，64×96整格，固定root `(32,80)`。ZIP：`art-source/ember/deliveries/robot_fixed_rig_v008_walk_down_candidate_2026-10-06.zip`，实测 SHA256 `ac74a58d6ac1751556751046571d5d983a9dcc4f9f85a146b4494706b055ff1b`。

直接查看 `art-source/ember/robot-fixed-rig-v008/` 下：

- `source/robot_idle_down_canonical_original.png` 与 `source/robot_idle_down_fixed_rig_canonical_v008.png`；并查看当前canonical4x图。
- `frames/robot_walk_down_f00_v008.png` 至F07，八张原生原帧全部直接查看。
- `previews/robot_walk_down_fixed_rig_v008_contact_checker_1x.png`、整数4x联系图；F01和F05单帧4x重点复看。
- `gpu-playback/walk_down_board_4x_v008.png`，用于确认GPU输出与联系图的外观。
- `art-source/ember/robot-structure-v005/robot_three_views_annotated_v005.png`、`robot_exploded_joints_annotated_v005.png`，对照肩嵌胸架、骨盆整体、髋膝套接与解剖左腕工具固定关系。

读 `revision-plan.md`、README、最终rig及腕套变化登记；`qa/independent_art_review_v008.md` 是制作方的独立审查入口，但其通过结论没有替代本次看图。采用 `docs/shader-learning/ta-art-review-standard-v001.md` §3的用户首要闸门：无因跨帧形变是拒收项，姿态／投影允许有连续解释的轮廓变化。

rig、两份母稿、atlas、两份checker联系图和八张原帧共14项直接读取固定ZIP成员并计算SHA，均与当前工作区一致。本报告未使用 `draft-01-pre-cap-affine/`、`draft-02-pre-wrist-cuff/` 或v007帧评价当前交付。

## 身份与结构判断

| 项目 | 独立视觉判断 | 重点帧与边界 |
| --- | --- | --- |
| 头胸 | 头盔顶深色块、小侧标、面罩、外壳宽度与胸部中心暗面保留同一身份；小幅左右摆和下降表现为整体移动，没有一帧忽然换盔甲或头胸涨缩。 | 八帧，F00→F01及F04→F05 |
| 工具与手套 | 小黄铜工具始终在观众右侧，即解剖左腕，未换边或游离；紧凑深色手套的前后投影变化与手臂摆动方向一致。F01工具轮廓略压缩，F05手臂反向，未读成另一种工具。 | F01、F05；F07→F00 |
| 肩、肘、腕 | 肩甲通过暗色结构插入胸架；肘不是两块甲片无连接地分离。F01/F05腕与手套可读作有厚度的套接，未见旧稿那种独立悬浮手块。 | F01、F05；八帧交叉 |
| 骨盆与腿数 | 腰、骨盆与双髋构成中心承重部分，两腿持续属于同一骨盆，没有腿数改变、髋座换位或大腿脱离。 | F02、F06经过态及F03→F04 |
| 膝／胫／靴 | 上腿、膝套、胫甲与靴连续。膝侧的装甲避让凹槽仍存在，但中央深色套接可辨，未读成横切整腿的透明断缝。摆动腿的缩短可以结合弯膝和前后投影解释；靴仍保留同一装甲、脚趾与深色底。 | F01/F02、F05/F06重点 |
| 材料与轮廓 | 浅装甲、蓝灰暗结构、小黄铜工具保持统一；没有发现磨损／孔洞游走、颜色突然闪换或零件增减。原生1x中头胸和四肢仍可辨。 | 全八帧 |

固定源层和骨长只证明来源／制作约束，不证明可见投影必然正确。本次可接受判断来自最终像素中身份、套接厚度和运动方向仍成立。

## 八帧步相及相邻过渡

左右以解剖方向命名：角色左脚在观众右侧。

| 帧 | 在实际像素中看到的关系 | 静态结论／返修 |
| --- | --- | --- |
| F00 | 左脚前接触、右脚后位；双腿轮廓完整，工具仍在左腕。 | 接触关键姿态可辨，无静态返修 |
| F01 | 躯干轻降，左腿承重；右腿缩短并准备经过，膝套仍承接上下腿；相反侧手臂向前。 | 未见贯穿膝缝或工具换形 |
| F02 | 右脚收近身体经过，左右腿的长短与深度差清楚；膝／靴没有突然换比例。 | 经过态可辨，无静态返修 |
| F03 | 右脚前摆，逐渐接近下一次接触；臂摆随相位反向。 | F02→F03→F04方向连续 |
| F04 | 右脚进入前接触，左右支撑关系交换；头胸保持同一体量。 | 与F00相反步相可辨 |
| F05 | 右腿承重下降，左腿回收；观众左腕的深色连接仍承接手套，左腕工具仍固定。 | 未见独立手块或断腿 |
| F06 | 左脚经过，身体与骨盆仍连成中心；另一腿支撑。 | 经过态与F02对应，无静态返修 |
| F07 | 左脚继续前摆，准备回到F00接触；F07→F00无需重新摆成中立姿态。 | 末首静态边界可解释，动态节奏待根代理 |

前后两脚投影的屏幕Y不同，并且摆动脚会收短、抬起。共同root未随bbox重新齐底；不能把所有脚底强制对齐屏幕Y80作为正确步态条件。联系图表现为紧凑、小步幅的机器人行走；主玩法移动速度是否与这段步幅匹配不在该无地面小样中验证。

## 限制及最小后续

- 当前静态审查未发现必须新增装甲、重新设计头胸或重做固定母稿的理由，也没有提出加速／柔化／缩小显示来隐藏问题。
- 我查看了现有深色checker、透明原帧及4x细图；浅色背景下的连续播放与正常8 FPS至少两轮、慢速和F07→F00实际运动由根代理交叉审查。若出现短暂断接或体积跳变，应记录实际相邻帧并返修源连接／局部像素，不以本静态结论覆盖。
- 正式接入仍须验证地图地面、root、支撑脚与位移速度；待机切换、其它朝向、其它动作和整套动画不在本次范围。
- F01工具有两个逆UV采样边界Unknown是制作方来源诊断的已声明限制；本次没有用“每像素已精确回溯”替代视觉验收，也没有观察到对应的可见道具身份失真。

## 版本SHA256

| 文件（相对 `art-source/ember/robot-fixed-rig-v008/`） | SHA256 |
| --- | --- |
| source/rig_down_v008.json | `e11638a6751cdaab475224cea772aa80425066daadcfab6e71436f84fd1341a4` |
| source/robot_idle_down_canonical_original.png | `c65f68455554edb03aea0a7b7b3cea6e1a779fa9d5aa49cba9b4aa5c4f6fbfff` |
| source/robot_idle_down_fixed_rig_canonical_v008.png | `a8d1b22073999c8d85fc89f68581ccb3fdd1d93d4bd23a708bcc9d1bd629b700` |
| robot_walk_down_atlas_v008.png | `899689597da6f0986c6a39dcc931097f4b09369167a9636d77ed5462e99d63c5` |
| previews/robot_walk_down_fixed_rig_v008_contact_checker_1x.png | `08d9f716ae5efda5e06d7770fb62e7498660614592c932d0cb9006a2a9fd1984` |
| previews/robot_walk_down_fixed_rig_v008_contact_checker_4x.png | `d66300d88f5092803ad9d27c5728bf98ace69d1965c5a8352d802a2a2d3bc649` |
| frames/robot_walk_down_f00_v008.png | `9ad4836c732e1b8b8bcbf7c2d756bb45c8f7ab69f14efb5034afcf7a39e780e2` |
| frames/robot_walk_down_f01_v008.png | `c224f0fcc892fc1d9735352fb7ca009b12baebcf045e3681905d37aa11811dc1` |
| frames/robot_walk_down_f02_v008.png | `27ffc6266bcd6d923e87771a4d97eecca8a6a2eab52e5bcf6cb141a03fbf2da8` |
| frames/robot_walk_down_f03_v008.png | `388e7e378dad503bda16ad70aa2a7ae02741dcfa77088485bbe123b614afcedc` |
| frames/robot_walk_down_f04_v008.png | `5ba027dd9a38b2a64ed2fc5ad22c6963d2e41e930225114affc1ab34cd4e09cc` |
| frames/robot_walk_down_f05_v008.png | `7e119ee3834b5b4edbe1acc7253a91e752d82a4f2dfc9ae55c40ab973fc00645` |
| frames/robot_walk_down_f06_v008.png | `f565c543aee5e317ea946aedbec919e3f955b9ab904c0bbed332d4a46df85956` |
| frames/robot_walk_down_f07_v008.png | `564cafb10f4528699a6efde3c48ea35338d144bfb2257fe7786d56a4f4d2520c` |
