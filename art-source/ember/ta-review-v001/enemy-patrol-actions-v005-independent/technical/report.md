# 巡逻兵 idle_down / hit_down v005 独立技术增量审核

结论：**两条动作本次来源、注册、端点、PNG 表示和恢复关系通过技术增量审核。** 作用力、关节可读性、动作自然程度由独立美术审核判定；不借用 move_down 的动作 PASS，也不把硬覆盖视为原生像素精修。

## 固定包与继承

从 `art-source/ember/deliveries/enemy_patrol_actions_v005_2026-10-06.zip` 独立解压至本目录 `package/`。ZIP SHA256 `6a3687783823cfd3e9db4b5c04d26b47c91a70df825ec74f8d195378b6c01468`，305064 bytes；54 文件条目、53 清单载荷，唯一未列载荷为清单自身。无重复路径、CRC失败或缓存载荷，53项大小/SHA及解压SHA全通过。

与已审 v004_r1 固定 ZIP 精确比较，canonical、rig.json、fixed_rig.gd、entity_cutout.gdshader 全部字节相同。canonical SHA为 `6e2c4eb57d214de69778291bcbdc4b40dfb4a5b4881fcb33338bb5f4474f348c`。仍是单一母稿、11个固定UV源区、相同左右工具、独立膝甲；没有8次独立生图。新 `action_rig.gd` 是明确声明的人工屏幕关节姿态，不冒充3D动力学。

导出脚本改为两条clip，仍以native128透明Viewport、straight RGBA、原0.5实体shader导出。仅source的导入设置文件保留在包内，没有 `.godot` 缓存。

## 独立注册与恢复关系

| 项目 | 实测 |
|---|---|
| 画布与root | 8帧均128×128，登记root(64,104)；两atlas均512×128 |
| idle_down | 4帧、4FPS、loop；SpriteFrames真实设置与catalog一致 |
| hit_down | 4帧、12FPS、nonloop；真实资源loop=false，duration均1 |
| frame bindings | 8个PNG SHA与catalog一致；单帧→atlas逐RGBA差0；两个内嵌Image/AtlasTexture链及全部region→正式atlas差0 |
| 恢复 | hit f03与idle f00全幅RGBA差0；hit f00亦为同一neutral。首末重复是恢复登记，未误报为缺帧 |
| 足部 | 实际固定ROI `[50,98,29,7]` 对neutral的8帧RGBA差0；两足basis恒等，ankle固定(56,98)/(72,98)，sole登记(56,104)/(72,104)，support=true |
| Alpha/边界 | 8帧部分Alpha0、画布边界可见像素0、Alpha只有0/255 |

足部结论限定于实际固定ROI、脚部变换和登记支撑点，不能替代完整腿部关节/遮挡观感。预览脚本在hit非循环结束后等待0.5秒再重播，是审阅播放器行为；Godot和HTML的重播没有改变资源nonloop属性。

## actual basis 端点与源表示

独立按 `action_rig.gd` 的shift/角度、腰点(64,80)、膝点及固定脚点用double三角函数重算姿态，再与actual导出矩阵比较。32骨段映射端点最大误差 `1.238e-6 px`，全部部件矩阵最大误差 `3.384e-6`，属于float32登记误差；没有旧rest斜向近似错位。膝甲均为恒等basis和平移，骨段轴向投影比例约0.868–1.123，是否在美术上合理由动作审查判断。

neutral的1137实体覆盖像素与相同canonical的声明阈值覆盖可见RGBA差0，8帧没有新增可见RGB颜色。CPU从源UV、polygon、actual矩阵、nearest及硬覆盖规则复算，保留了2处单像素差，而没有修改CPU结果以凑零：

- idle f01画面(56,93)：double UV y=93.999999657，float32为94.0，实际RGBA=(123,145,156,255)，为源(56,94)；与此前同类整数采样边界一致。
- hit f02画面(67,70)：CPU逆映射UV x=65.999382，CPU选择源(65,70)，实际GPU使用相邻源(66,70)颜色(216,206,190)，未新增颜色。随后独立冷GPU重复同一rig/PNG结果，确认不是导出预乘变暗/表示错位。具体texture-unit量化没有测量，不将CPU简化逆采样宣称为完整GPU逐纹素模拟。

0.5硬覆盖和未旋转neutralRGB保真仍不能证明已经完成原生逐帧像素精修；该验收边界继续保留。

## 16组黑白实图与快速冷GPU复核

包内保存了全部8帧×黑/白底，共16张512×320 rig/PNG左右对照。独立比较左右RGBA差0，两侧分别与正式PNG直接合成到对应底色、取固定64×80观察区域并nearest4×的结果差0。

为核对上述CPU采样差，另从同一ZIP复制至 `cold-gpu/`，冷导入并重新执行包内原样 `verify.gd`，没有运行export或改写 `package/`。实际Godot `4.7.2-stable (steam)`、Compatibility、NVIDIA RTX4070 Laptop GPU，导入及验证exit0、两stderr均0 bytes。新的16个native128 rig/PNG组合RGBA通道差均0；新生成16张对照与固定包原图逐RGBA差均0。

独立GPU复跑使用了固定包验证脚本；另有本次独立Python端点/注册/图像复算，因此不把作者报告或其浮点“端点0”直接当独立double结果。作者8.602秒播放覆盖/完成/循环记录有正确catalogSHA绑定，但本次没有重跑8.6秒播放器，仍标为作者运行记录。

## 本地预览绑定

`enemy-sequences-v001/previews/preview_server.json` 指向该previews目录、port6106。本地 `patrol-actions-v005/index.html` 与包内preview.html SHA相同；served catalog、两atlas均与固定包SHA相同：idle `84a29c3af3b2f6dff3c0136a8bc4c1104814442725fa61ac0f5ab140b1197017`，hit `21625b527b143757e553d91591b5df5506ca2654ff0875497fdf62b137d5a64c`。此为配置/本地文件绑定核验，没有把网页浏览器辅助预览当作新的正式素材包。

## 证据与范围

本目录 `evidence.json`、`verify.py` 保存53项载荷、32actual端点、8帧/两个内嵌图集、16静态对照、采样差及served绑定。`independent-gpu-evidence.json` 和 `cold-gpu/qa/roundtrip_*` 保存新的GPU结果及实图差异；日志在本目录。

复验独立静态审核可运行 `python -X utf8 art-source/ember/ta-review-v001/enemy-patrol-actions-v005-independent/technical/verify.py`。GPU原样探针只应对冷副本运行 `--path <cold-gpu> --script res://verify.gd`。

本次生产只读；通过范围只含巡逻兵这两条技术增量，不扩展到攻击、死亡、其他方向或其他敌人，也不代替最终美术放行。
