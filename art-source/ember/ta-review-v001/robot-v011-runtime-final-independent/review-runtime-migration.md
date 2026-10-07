# 机器人 v011 正式运行包迁移回执

**PASS_MIGRATION_ONLY，2026-10-07。** 正式运行包保留已通过C2 rc02的八向idle/walk/collect，共24段112帧；独立映射、冷导入、实际新Godot入口与新网页入口复核通过。主游戏集成不在本次范围内。

| 交付 | 固定绑定 |
| --- | --- |
| 运行目录 | `art-source/ember/robot-eight-way-v011/delivery/robot-v011` |
| ZIP | `art-source/ember/deliveries/robot_eight_way_v011_final_2026-10-07.zip` |
| ZIP SHA256 | `8dc65a715b41b2c61a09eb6e2afbcd31134db60228f4b3081a0a39e4d153f4bb` |
| 大小／文件 | 1,398,383 bytes；336载荷＋manifest＝337文件 |
| manifest SHA256 | `d605101d0e668796995599a44f9cd86010220f108ef0e21adec62faf20797235` |
| 已过来源ZIP | `64a3a18625dccc2fc1bde35ae44388a7acfb92ddb9aa4c83db811d2e5c10aa1b` |

112PNG、atlas及192GIF/WebP逐字节保持。TRES、预览GD/TSCN、project仅各一处声明路径替换；导入参数完全保持，包括关闭Alpha边缘修复和mipmap。metadata仅28个状态／路径／绑定变动，网页仅三行状态或工程链接变更，播放逻辑未变。[独立迁移明细](integrity.md)。

从最终ZIP新建无旧缓存副本，在Godot 4.7.2实际实例化工程main_scene：24段112格RGBA、时序、原点和节点参数通过；idle/walk各自然循环一圈，walk切向保留帧索引；SE collect实际0→1→2→3、锁向、一次finished、双节点回idle F00。这里只验证原实现保留帧索引，没有把小数frame_progress保留写成通过。正式素材64×96、root(32,80)、nearest、centered=false、offset(-32,-80)。

实际SE采集F01在1×和4×下分别核1,421／22,736个不透明像素，零差；固定目录和冷副本336载荷引擎前后均保持。自有探针首轮类型推断错误已留记录，修正审查探针后从新冷副本有效通过，未修改交付脚本。原224画面GPU矩阵仅继承来源记录，没有冒称本次重跑。

根实际访问新网页，检查SE采集F01浅底/F02深底、原生与4×显示，并重播确认回同向idle。[网页入口记录](root-preview.md)。正式包可按README作为独立运行交付；后续新增内容或主游戏接入另核。本回执存于TA目录，不改写冻结ZIP。
