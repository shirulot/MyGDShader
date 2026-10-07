# 巡逻兵 SE move pilot v001：独立来源、导出及最小冷加载

**结论：FIXED_SOURCE_MASK_EXPORT_AND_COLD_RESOURCE_PASS。** 固定包、既有方向来源、源区归属、八帧/嵌入 SpriteFrames 和冷资源加载未确认新的技术 P1/P2。技术结论限于本条 SE move 八帧；动画观感与通过通知仍由根 TA 汇总，不扩大到其余方向或单位。

## 固定包与原来源

- ZIP `enemy_eight_directions_v013_pilot_patrol_v001_2026-10-06.zip`：独立 SHA256 `c7cf9683604740953a48d43b6fd2fbf7cd5d11767ee3af1fbc65171d4493dd21`，312,869 B，53 条目为 52 manifest 载荷加 manifest。全部 CRC、字节数与 SHA 通过；52 载荷与固定活动目录同字节。独立解包至本报告目录 `cold-project/`，首次没有 `.godot` 导入缓存。
- catalog SHA256 `b20ac1a75f5eefef42deee8dfbac324418967ab6e76a8c4d5af65e9f10ce348f`，实际绑定 `pilot_rig.gd`/`pilot_rigs.json` SHA。
- 方向源 SHA256 `e1916f467c4493bab2b95b57b558f18ab2090c45721c48cff590422139cb93f2`，逐字节等于原 s002 固定 ZIP 的 SE。包内八个静态方向 PNG 都与 s002 对应文件同字节；中性 rig PNG 与 SE 源完整 RGBA/文件字节一致，没有重新绘制母稿或逐帧生成。
- reference down atlas 与原 v008 固定 ZIP 对应 atlas 同字节；八个 `phase/body_y/depth/lift/support` 记录与 v008 `rig.json` 的 phases 完全相同。reference neutral_down 与包内保留 down 同字节。旧来源比较均使用原 ZIP，不以当前活动目录自证。
- `enabled_pilot_units` 只有巡逻兵。公共 JSON/脚本中的其他单位定义不代表其它单位动画提交，未扩审或加载其生产源。

## 固定 mask 与邻工具

独立按源像素中心重算 8 个部件的 include/exclude polygon 与 body 剩余区；1162 个源可见像素均恰有一份归属，重收/漏收为 0。

| 源区 | 可见源像素 |
|---|---:|
| right_thigh / right_shin / right_cap / right_foot | 22 / 14 / 57 / 83 |
| left_thigh / left_shin / left_cap / left_foot | 20 / 15 / 57 / 89 |
| body | 805 |

结合原 SE 图看工具邻域并核真实归属：枪邻 ROI `[46,79,54,96]` 的 75 个可见点、夹爪邻 ROI `[76,84,84,94]` 的 43 个可见点全部属于 body，进入任一移动腿区的点数均为 0。完整靴缘归属于对应固定 foot 区。上述是源结构与实际 mask 的交叉观察，不以单纯像素连通数量裁决造型。诊断图：[source-owner-legs-16x.png](source-owner-legs-16x.png)。

独立重算 32 个 thigh/shin 实际 basis 端点，最大误差约 `9.83e−7px`；登记的 knee/ankle/hip 与实际矩阵承接一致。32 组 cap/foot 变换均保持单位 basis，只做固定膝甲和靴的平移。短轴连接区有投影长度变化：轴向比例约 `0.515–1.178`，法向宽度保持 1；这是声明的端点映射近似，并非所有部件均为刚体或原生精修的证明。姿态是否自然不由端点零差代替。

补查摆臂关系：`pose_patrol` 没有独立腕部前后 depth/lift 变换；头胸、两臂和工具都在 body，保持原形，仅随 `body_y=[0,1,0,-1,0,1,0,-1]` 上下移动。未发现同侧腕与腿同时向前的符号实现。固定持工具姿势与是否需要额外摆臂由根视觉评判，本报告不因另一单位的摆臂问题强加改动。

## 八帧、atlas 与 CPU 来源重建

八张 PNG 均为 128×128，Alpha 0/255，画布边界没有可见裁切点；root `(64,104)`。八张 SHA、1024×128 atlas 切片及 TRES 内嵌 Image 的原始字节全 RGBA 一致。TRES 无外部资源依赖，8 个 AtlasTexture 的 region 依次为 `(i×128,0,128,128)`；帧 duration 均为 1，`move_down_right` 为 8FPS、loop。

按固定源、独立 mask 与登记 actual basis 重建八帧，理想 CPU 与导出 PNG 的覆盖差全部为 0。完整 RGBA 比较只有以下三个 RGB 差点，其余帧为 0差：

| 帧 / 输出点 | 部件及理想源坐标 | floor 采样 / PNG实际同值源点 | 原因 |
|---|---|---|---|
| F00 `(60,84)` | right_thigh，约 `(61.061553,84.0)` | `(61,84)` / `(61,83)` | 源 y 恰在整数纹素边界。 |
| F03 `(69,92)` | left_shin，约 `(70.999999978,93.499999997)` | `(70,93)` / `(71,93)` | 单精度边界向 x=71 的另一侧取样。 |
| F07 `(60,83)` | right_thigh，约 `(61.061553,84.0)` | `(61,84)` / `(61,83)` | 同 F00 的源 y 整数边界，目标 body 相位相差1px。 |

三个 PNG 像素均与同部件内相邻边界纹素**全 RGBA 精确相等**，不是重新上色、Alpha变化或工具污染。CPU floor 的 RGB 分别为 `[9,20,29]`、`[35,54,72]`、`[9,20,29]`，PNG 分别为 `[15,30,45]`、`[39,63,84]`、`[15,30,45]`；Alpha 均255。不得将它们写成“CPU全RGBA零差”，也无须因此重新跑完整 GPU。完整坐标与原值在 [binding.json](binding.json)。

## TA 实际最小冷验证与作者记录

本轮独立运行 Godot `4.7.2-stable (steam)`：从无缓存冷包 headless 导入，退出0、stderr0；随后自有小探针 **29/29 PASS**，退出0、stderr0。它覆盖 TRES 冷加载、内嵌依赖、8帧/8FPS/loop/duration/region、原 preview 场景 `_ready`、仅巡逻启用、10个可用静态/移动动画、Nearest，以及两个定点：SE切向保持 `frame3/progress0.375`，未制作 NE 回退静态并保留 down 参考相位。导入后包内52个原载荷 SHA仍不变。

这是 **headless 资源/场景/属性核验**；未实际捕获 GPU、未重跑自然循环或作者完整方向切换套件。自有探针及记录：[probe_cold.gd](probe_cold.gd)、[cold-probe.json](cold-probe.json)、[cold-receipt.json](cold-receipt.json)。调用日志和 SHA 见 receipt。

制作方的 16 个黑白底 live-rig/TRES/PNG GPU 对照数字记录均绑定本次 catalog SHA，逐帧/背景组合完整，差异数字均0；固定包未附16张独立 roundtrip 实图，因此本代理核的是**记录完整性和来源绑定**，不称已独立逐图验证或 GPU 重跑。作者四播放器均登记看过0..7并完成循环、八次方向切换 PASS，同样仅作作者记录绑定。根 TA 的浏览器播放和视觉报告是另一个实际观察范围。

未改生产、未运行生产导出/捕获器、未发其他聊天消息。复算：[verify_binding.py](verify_binding.py)。本技术通过不新增或扩大动画、美术与其他方向验收范围。
