# C24 attack/death v002：独立技术增量复审

结论：**PASS_TECHNICAL_INCREMENT_COLD_VISUAL_SEPARATE**。本轮固定包的源、变更范围、实际 ownership/姿态、资源和冷载入均通过。v001 锯盘 P2 所涉及的错误分片与轴心已实际更改；修后轮廓是否稳定、旋转是否仍带来不合理缺口，以独立视觉及主 TA 播放结论共同判断，不能由配方复现自动放行。

## 固定包与改动范围

- 固定目录：`art-source/ember/enemy-cutter-attack-death-v024-review-v002`。
- ZIP：`art-source/ember/deliveries/enemy_cutter_attack_death_v024_v002_2026-10-07.zip`，3,807,029 bytes，328 载荷 + manifest，共 329 项。
- ZIP SHA256：`3fc81f650daf58c949f216c4b9a783b03348d9ba11fcf512f7e6f08f92ff80be`。
- catalog SHA256：`fd2bf874e376a4ec7194e975a45c3b47a9cbee471ee6a09591b3fb5534f11a70`。

独立验证 ZIP CRC、manifest 所有大小/SHA、固定目录逐载荷字节一致。完整 ZIP 被解至 TA 副本，冻结包未修改。相对已审 v001（ZIP `c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c`），逐 PNG 独立比较得到 **59 改帧、11,597 RGBA 像素次变化、53 张帧图字节保持**，与提交记录吻合。

保持范围包括 S attack/death 两段、W attack/death 两段、N death，以及所有新方向 F00 绑定与 attack F05 回位帧。S 两段 14 PNG + 2 atlas 另对原 v012 ZIP 字节复核通过；W 两段和 N death 的 PNG/atlas 对 v001 字节保持。八张 neutral PNG 字节保持，七份新向 bind 对原固定源完整 RGBA 零差。

七张源 PNG 与 v001 字节一致：六向仍对已过 C22 固定源，SE 仍对 HC 实际装配中性图 SHA `79e56cd5438f5b78d4dad555e9a364c359635b8cb8b58c6b1790cc166679b462`。本轮未生成或补画新的源 RGB；“盘面补全”在此指原图现有像素的归属修正。

## 五向锯盘实际归属与轴心

独立重建 owner 并对实际 Godot ownership texture 逐像素检查，66 份 mask 完全一致；每个源不透明像素仍唯一归属。v002 的工具选择范围显式包含 blade polygon，使超出旧工具 polygon 的原盘面像素能够正确归入锯盘。

| 方向 | v001→v002 可见 blade 像素数 | 新 hub | 新投影半径 | 实际归属变化 |
|---|---:|---|---|---|
| SW | 154→141 | (41.5,90.5) | (6.5,7.5) | 13 个原 blade 归回 saw |
| NW | 94→146 | (84.5,79.5) | (6.5,7.5) | 36 saw + 19 body + 2 腿点归 blade；5 blade 归回 saw |
| NE | 157→154 | (86.5,87.5) | (6.5,7.5) | 3 个原 blade 归回 saw |
| E | 141→167 | (80.5,92) | (7,8) | 26 个原 saw 归 blade |
| SE | 166→149 | (59.5,96.5) | (6.5,7.5) | 19 blade 归回 saw；2 saw 归 blade |

五处 hub 坐标均在源图黄铜轴心区域；原图、旧 blade、修后 blade 并排放在 `technical-blade-registration-10x.png`，所有实际重归属坐标与 RGBA 均列于 `technical-increment.json`。这张登记图是源语义核验材料，不以椭圆面积反推“应补”像素。

NW 点名的原源 (80,76) 为 RGBA (62,56,54,255)，原 `front_right` 归入 `saw_blade`；(82,87) 为 (0,0,0,255)，原 `rear_right` 归入 blade。v001 开口缺扇区追踪到的源 (83,77)、(83,78)、(83,79)、(83,80) 原归 saw，本轮全部归 blade。NW 肩轴 y=78→74，E 挥击幅度 20°→10°，SW spindle 末端随 hub 登记更新。没有把新注册等同于新画完整圆盘，也没有把原 body/leg 标签当作源像素视觉身份的最终证明。

五向 blade 仍在固定椭圆投影度量中旋转，变换 det=1；其屏幕 basis 不一定正交，因此不能写成屏幕空间正交刚体。身体、工具臂和腿甲使用正交刚体变换；不得用 blade 这一投影例外豁免硬甲伸缩。

## N 攻击与 SE 测点修正

N attack 机身围绕固定点 **(64,85)**，六帧登记 `(dx,dy,degree)` 为 `(0,0,0)`、`(1,0,3)`、`(2,1,5)`、`(-2,-1,-7)`、`(-1,0,-2)`、`(0,0,0)`。独立计算与 catalog、真实 rig 节点 pose 一致；body basis 正交、轴心变换等于原轴心 + 登记位移，所有 foot 仍是恒等变换。F00/F05 恢复原绑定。N 没有新暴露或生成隐藏锯盘；可读性由机身蓄力/释放表现承担。

SE 的新 sole 登记逐点验证都落在其自身实际源 foot mask：

| 部件 | 原 sole | 新 sole | 真实采样点及 owner |
|---|---|---|---|
| rear_right | (44,85) | (44,85) | (44,84)，rear_right_foot |
| rear_left | (79,79) | (78,81) | (78,80)，rear_left_foot |
| front_right | (52,94) | (50,94) | (50,93)，front_right_foot |
| front_left | (81,91) | (79,91) | (79,90)，front_left_foot |

登记调整没有改变原 ankle、pivot、foot cut 或 foot 变换。动态不保证始终可见：例如 attack F02 front_right 被 saw_blade 覆盖，F03/F04 front_left 被 claw 覆盖，death F02 rear_left 被 front_left 腿壳覆盖。不能把“固定脚”写成所有帧都可见的接地测量。

SE front_left 的固定 2×2 UV 区仍为 **1 个深棕不透明源像素 + 3 个透明像素**；说明已更正，未伪称四个蓝灰实体。所有 24 组 UV 实际节点、2×2 源区域、width 及源 RGBA 均独立记录。

## 资源、姿态与最小完整冷载入

112 张 128×128 PNG 的 SHA、二值 Alpha、atlas 对应格完整 RGBA、登记边界均通过。16 clips 为八向 attack 6 帧与 death 8 帧，10fps、单次；攻击首尾一致，死亡末三帧一致。新向输出不越过 y=104，旧 S 的原攻击下界保留。根锚 (64,104)。

新目录 `technical-cold-load` 来自完整 ZIP，初始无 `.godot` 缓存，保留导入配置。Godot 导入与独立探针均 exit 0、stderr 0：**16 clips / 112 实际导入纹理格 RGBA**、两个实际 preview actor 的 Nearest/uncentered/资源参数、**7 rig / 66 ownership mask / 24 UV / 98 pose** 通过。catalog 中姿态与独立数学重建、实际节点返回值一致，material sensor power 也逐姿态读取。运行后 328 载荷 SHA 全部保持。

本轮 cold 使用 headless 资源与节点读回，**没有独立重跑 210 GPU 截图或 32 player / 16 switch 全矩阵**。作者本轮 GPU/runtime 记录已按本轮 catalog 与文件 SHA 绑定，不能计作独立重跑结果。

## 残差与证据范围

独立 CPU 反采样/UV 组合对 98 帧保留 **73 个 RGBA 像素次残差、10 个 Alpha 像素次残差**；v001 为 84/21。NW death F05/F06/F07 各 10 个重复残差照实保留。未把这些位置改图抹平，也未宣称当前 98 帧 CPU 完整 RGBA 零差。

实际输出相对独立 CPU 的刚体底图，有 **156 个像素次**能定位在登记 UV polygon 内并匹配原 2×2 源色；另 **4 个像素次**仍处于 CPU 底图采样残差边界，不强归 UV 新像素。连接实例会新增输出 Alpha，这不意味着新增源 RGB，也不应说“输出没有新增像素”。

- `technical-zip-binding.json`：完整 ZIP、manifest、冻结目录绑定。
- `technical-increment.py/json`：v001→v002 112 帧、59 改帧、源保持、真实归属变化、hub、N 轴心与 SE sole。
- `technical-audit.py`、`technical-integrity.json`：源/旧动作、唯一归属、绑定、98 姿态、CPU 残差和 UV 源色证据。
- `technical-cold-probe.gd`、`technical-cold-receipt.json`、`technical-minimal-cold-load.json` 及日志：最小完整冷导入与实际节点读取。
- `technical-blade-registration-10x.png`：原图/旧 blade/新 blade 与 hub 标记。

技术证据支持本次修订确实执行了声明的范围、来源和注册调整；最终锯盘连续轮廓、N 攻击可读性、死亡关节承接仍以本轮独立视觉结果为准。
