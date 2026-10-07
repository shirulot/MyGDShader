# 建筑 v004r1：UI 定点增量回执

**UI_P2_CLOSED。** 本轮未发现新的 P1/P2。原 v004 的说明、toast、名称超出窗口问题已在独立冷包与真实键盘事件中关闭。正式二值覆盖/导出由另一条独立审查裁决；此回执不代替其结论，也不重新审定造型。

固定 ZIP：building_assets_v004r1_2026-10-06.zip，28,875,505 bytes，79 files / 78 manifest payload，SHA256 22dc4017aef594f33350e71b0af723909fbd1c4fde1a88208c9a66e34c9e2a32。78项路径、字节数和SHA独立核对正确，冷解包受限于本审查目录。

## 独立结果

Godot4.7.2 Steam、GL Compatibility / RTX4070，新建隐藏进程；不操作用户编辑器、不打开浏览器。独立 editor cold import exit0、stderr0；定点运行 exit0、stderr0，**12/12**。

| 定点范围 | 实测 |
|---|---|
| 原 help / toast | help (28,722,1352,58)，toast (28,680,1352,27)，整个矩形均在1408×800内。 |
| 三栋名称 | (65,100)、(419,100)、(935,100)，各190×28，均完整可见。 |
| 实际 E 输入 | 在塔人门前设置真实锁门状态，使用 Input.parse_input_event 走原事件分发；自然 _process 显示“门已锁定”，门 target/progress 仍为0。未直接调用 toast、键盘回调或设置 visible 冒充输入验证。 |
| 按键说明/反馈关系 | E与F5/F9说明仍存在；help与toast不相交；反馈文字未裁切。 |
| 实际 F5 输入 | 独立用户存档目录内保存成功，toast自然显示“已保存建筑状态”。 |
| GPU 人工查看 | 两张完整1408×800截图已实际查看：名称、中文拒绝/保存反馈与两行说明清楚，没有旧底部超界。 |

修订位置：[building_demo_v004r1.gd](E:/dev/shader/godot-shader/godot-shader-simple/scripts/ember/building_demo_v004r1.gd:27) 覆写UI；第45–53行按视口放置说明和toast、按当前 PLACEMENTS 放置名称。旧版本脚本没有被改写。

## 对原功能结论的继承依据

固定 v004/v004r1 ZIP 共同的9份 runtime/shader 全部字节相同：building_asset_v001/v003/v004，building_demo_actor_v001/v004，building_demo_v001/v003/v004，building_intact_v004 shader。

新 building_asset_v004r1 只有 catalog生产路由与snapshot版本标签。新 demo 的世界比例、YSort、3摆放点、演员及地板沿用v004；增量是新生产类、UI布局与独立存档名。状态机、角色占用刷新后再恢复建筑的顺序、门碰撞释放阈值和整壳淡出逻辑均未改。

三栋脚印256×128 / 384×128 / 608×224，以及 source pivot、uniform scale、门源矩形/倒角/净口、服务/舱盖/灯/窗区域逐字段保持一致。塔的派生 center_world_x 从1.9555555555555557序列化为1.9555555555555555（约2.2e−16），已明确记录；运行门中心由未变 source_rect 与 scale 重算，不使用此派生值。不是新几何变更。

因此没有机械重复旧72项行为检查或全部104项，原已验证功能范围仅继承至当前整壳淡出/深暗门洞范围；不扩展为楼层/房间高度分区。

## 证据区分

作者包内94/94及cold_runtime stderr0已绑定，报告SHA 734c377d7924aad56023cdc50b92a6f8d005194f427401206ab20797595b1524。**94项是作者证据，本轮独立运行只有上述12项。**

- [独立结果JSON](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004r1-independent/ui-technical/cold-project/ta-ui-incremental-result.json)
- [独立E锁门GPU图](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004r1-independent/ui-technical/cold-project/ta-ui-locked-E.png)
- [独立F5保存GPU图](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004r1-independent/ui-technical/cold-project/ta-ui-saved-F5.png)
- [ZIP/源码/几何增量绑定](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004r1-independent/ui-technical/incremental-binding.json)
- [独立probe](E:/dev/shader/godot-shader/godot-shader-simple/art-source/ember/ta-review-v001/building-v004r1-independent/ui-technical/cold-project/tools/ta_ui_incremental.gd)

import-independent.log / import-independent.stderr.log、probe-independent.log / probe-independent.stderr.log 均在本目录。两份stderr为0 bytes。生产文件及原始提交未修改。
