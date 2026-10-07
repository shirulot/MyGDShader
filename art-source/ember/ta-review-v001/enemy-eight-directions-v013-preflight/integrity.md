# 敌人 v013 静态预检：固定输入与像素完整性

结论：**STATIC_PREFLIGHT_BINDING_PASS**。本轮仅固定和验证32张neutral的静态候选证据；不代表28张新方向已通过美术审查，不继承南向动作PASS，也没有运行Godot或行为测试。

## 固定四输入

| 固定输入 | SHA256 |
|---|---|
| eight_direction_masters_black_4x.png | 0842407dedbbca00c43d73cf49a04c618663869ab39464ee29fc5d4f6946e165 |
| eight_direction_masters_white_4x.png | d5ae887ff11416aeb474b00c6611063ab719ee64dc4d56e51305bdf9800e29ec |
| registration.json | d7f6f829318feb99d3ac252fd4c84a3638c5d47589f8a3849fa35610fabda68a |
| master_catalog_v013.json | 8d673512350d2b388d04e250144d315ceac459263dcb6d0b6f6e19f7e5dd4e5a |

四份原始字节已复制至 bound/。catalog中的registration SHA与固定registration一致，当前生产registration也相同。32张当前output图全部符合catalog SHA，检查结束再次读取仍无变化，因此32张neutral已按原路径复制至 bound/output/，没有混入不匹配的新图。

## 基线与联系图

- 4张down分别与source/approved_down字节一致，与已通过v012固定包idle首帧PNG哈希一致；独立读取v012实际idle atlas裁首格，全RGBA也零差。仅验证四首帧，没有机械复验旧120帧。
- v012固定ZIP SHA为42a5416385c8e8d309501fb5ec3295b1ef0e4d0d700146576b4bcca0030621fe，其assembly_recipe SHA与此前独立通过回执一致。本轮基线证据不是仅信v013自报baseline。
- 联系图4096×2048按4单位×8方向、每格512²，对应128²neutral。黑/白两底共64格：4×nearest每个像素块完全一致；按独立Alpha合成复算原生RGB，**两底均0差异，最大通道误差0**。因此这批无需使用Godot截断/Pillow整数round的±1容差。
- 32图均128×128，Alpha只有0/255，连续Alpha0点。每张实测bbox和Alpha直方图均见integrity.json，bbox与catalog登记一致。bbox数据只作为诊断，未按比例或面积机械裁决造型。

## 用于根级视觉复核的诊断图

每单位的原联系图前4/后4列已直接裁至 diagnostic-crops/，保留原4×nearest与黑白底，无重排、移底或改色。

新增两张8×浅底同画布三列对照：

- [巡逻：approved down / generated front / down-right](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/diagnostic-crops/enemy_patrol_approved-generated-front-down-right_light_8x.png)
- [无人机：approved down / generated front / down-right](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/diagnostic-crops/enemy_scout_drone_approved-generated-front-down-right_light_8x.png)

左/右列取绑定的approved down和catalog neutral；**中列来自当前working的qa/generated_front，仅诊断，未冒充四份冻结输入或固定neutral**。三列均保留原128×128画布中的位置，再统一Nearest8×；没有裁bbox齐底、平移或额外缩放。统一浅底RGB(210,214,220)，图尺寸3072×1024。中列原文件与诊断成图SHA单独记录在calibration-working-diagnostics.json，采集期间中列未变化。

证据：[integrity.json](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/integrity.json)、[工作态三列来源](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/enemy-eight-directions-v013-preflight/calibration-working-diagnostics.json)。生产路径只读，所有新增文件均位于本审查目录；未发送制作方消息。
