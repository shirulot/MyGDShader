# 机器人 v011 阶段 A：独立技术定点回执

**TECHNICAL_BINDING_PASS，未确认技术 P1/P2。** 固定文件、24审查图、10 clips、冷加载、SW部件/补丁来源账本闭合。此结论不代替造型、接地、步态或跨帧关节观感审查，也不批准最终24段112帧八向包。

固定ZIP：robot_eight_way_v011_phase_a_rc01_2026-10-06.zip，4,559,554 bytes，SHA256 ee0b416f194363d4e37e751c03446c944c217af3a2f567a03eff4a00ad91e7e6。**182 entries = 180清单载荷 + sha256-manifest自身 + frames/idle空目录**，实际普通文件181个；空目录不是额外已完成idle帧。

## 封包、帧与接入资源

- CRC、唯一/安全路径检查通过。180载荷大小/SHA在ZIP及冻结phase-a-rc01目录两侧完全一致；解包仅写本审查package/。
- 24 PNG均64×96、二值Alpha，与metadata文件SHA相同；512×288 atlas全部24 regions逐格全RGBA一致。Godot工程的atlas与metadata副本也字节一致。
- SpriteFrames有且仅有10段：walk_down、walk_down_left各8帧/8FPS/loop=true；八个pose各1帧/1FPS/loop=false。24 AtlasTexture region、次序、1.0 duration与metadata逐项一致。单帧pose没有被当作最终双帧idle。
- 画布64×96、root(32,80)、1:1资源比例一致；实际预览native/4×实例均centered=false、offset(-32,-80)，Nearest采样。
- v010 down八帧与v010原ZIP逐文件字节相同，并与旧独立审查保留的export_validation SHA 81e3f3345d85327d1a23a57336eb4a6a306d5d6aa0e3f888628abe98c5a217c7及当前v010文件相符。不是仅信新metadata的“保留”声明。原ZIP成员带目录前缀，已按唯一匹配源路径登记，未因路径schema差异制造问题。

## SW独立像素重算

独立Python实现从源PNG提取多边形分区和刚性逆映射；**没有运行制作方build/composite CJS**。

源可见归属共1334点：body682、arm_right86、arm_left126、leg_right228、leg_left212；没有跨肢体多重归属。11固定部件与独立提取结果全RGBA零差，静止复拼与母版全RGBA零差。上下段在同一关节的声明源重叠保留，不误判为重复肢体。

8个原rig-pilot逐帧由11固定部件及登记刚性变换重算，全RGBA零差。每帧所有变换只有sourcePivot/targetPivot/radians，没有逐帧scale。最终局部修形是独立补丁流程，不能据此声称成品所有关节仍是严格刚性源片。

进一步独立推导body、手/左腕工具、靴子及外轮廓透明邻域的保护区，按骨点重建椭圆选择区/保护裁除与整板补丁坐标：8个mask与实际mask全RGBA零差，8个最终帧与重算零差；逐点before/after/区域标签账本全部一致。每帧改动196/200/182/173/145/152/187/219点，共1454点；**保护区变化0、mask外全RGBA变化0**。

补丁raw母板SHA 60ce1c45df11cfe7c45dc9ba877124471d9d1e1a062ccc0853e769c01034dc6b，尺寸1448×1086；量化板256×192、SHA 234b48acf7fcf8d998258e093878721adb450db7f9bd3253e86739af048e1927。独立脚本按声明Sharp Nearest整板采样、Alpha160阈值及11色色板距离重算，量化板全RGBA零差。Pillow Nearest诊断有1774点差异，属于其采样坐标规则与Sharp不同；按明确的生产Sharp契约复验为0，因此没有把库差异或透明RGB当P2。两份诊断均保留说明。

## 本轮运行与作者证据

仅复制小Godot工程到独立cold-project，再启动隐藏headless进程；未操作用户编辑器、未改生产/M0。冷import exit0、stderr0；独立资源加载 **37/37**、exit0、stderr0：10 animation合同、24实际AtlasTexture尺寸/region/duration、资源名称集合、native/4×锚点与过滤。

作者48 GPU cases及两段walk各actual_loops=2的记录，通过manifest/atlas SHA和原始报告绑定。**本轮没有重跑48 GPU截图、自然两循环或把其声明冒充独立引擎运行。** 作者export报告同样只标为绑定证据。文件哈希正确及mask保护不意味着关节和步态美术已通过。

范围仍为8方向静态候选、已过down walk与新SW walk小样。pose_down复用v010 F02，其作为idle的支撑姿态由视觉审查判断；其余方向walk、双帧idle和collect仍未完成，README和metadata已明确，不作为阶段A技术缺陷。

## 证据

- [封包/24图/10clip与作者记录绑定](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v011-phase-a-independent/integrity-data.json)
- [11部件、8帧、mask/保护区重算](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v011-phase-a-independent/sw-pixel-reconstruction.json)
- [raw母板到量化板的明确Sharp契约复验](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v011-phase-a-independent/patch-source-sharp-contract.json)
- [独立冷加载37项](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/robot-v011-phase-a-independent/cold-project/ta-resource-load-result.json)

cold-import.log / cold-import.stderr.log、cold-load.log / cold-load.stderr.log 在本目录，两份stderr0 bytes。审查源码verify_integrity.py、verify_clips.py、verify_sw_pixels.py及采样诊断脚本保留，可复核来源边界。
