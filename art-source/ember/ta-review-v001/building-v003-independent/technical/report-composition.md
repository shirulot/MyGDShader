# 建筑 v003 独立静态组合与接合定位

结论：**NEEDS_REVISION。** 当前屋顶与墙体在两端各自保留完整倒角、暗收边和柱帽，合成后仍有明显拼接感；用户最新要求以未拆整栋图的连续衔接为依据。静态组合忠实通过，不能据此将外观退回问题关闭。本次只定位结构与正式资源是否一致，按根审查通知停止无必要运行和大规模交互复验。

固定 ZIP SHA256 `624e62421ada6b468fe7324991ba8c563602ea875a46678f96f44af7f0901ff9`，74403942 bytes，346 文件（345 载荷与 manifest）；catalog SHA256 `40fc8c92c5f6b677cd652a29858e5c5e56d4cb4890452f4c479449498f2f6006`。独立只读解包位于本目录 `package/`。主证据 [composition-evidence.json](composition-evidence.json)，复现脚本 [inspect_composition.py](inspect_composition.py)。

## P2：独立倒角叠合使接合处收窄后再次外扩

实际来源：`assets/ember/building_assets_v003/alignment_sources/<id>_roof.png` 的前檐保留向内斜下的倒角和深色底边；`assets/ember/building_assets_v001/parts/<id>_front_wall.png` 的墙顶则保留向外斜下的倒角与柱帽。工坊、仓库的两张源图单独看都有一套完整收边；共享画布叠合后出现两组上下相邻的檐帽，外轮廓先内收再外扩。仓库两个柱轴对齐也没有取消上下两套柱帽。不是导入偏移、遗漏 Alpha、预览比例或主成品漏同步。

复现：打开 [工坊同坐标源图与合成 4×](repair_workshop_seam_source_4x.png) 或 [仓库同坐标源图与合成 4×](logistics_warehouse_seam_source_4x.png)，按 ROOF only→FRONT WALL only→COMPLETE 查看两侧角部及中央柱帽；再直接看正式 `complete_closed.png`。

| 建筑 | 实际完整画布上的角部外轮廓证据 |
| --- | --- |
| 工坊 | 左边从 y146/x32 内收到 y152–153/x38，又在 y158 回到 x33；右边同时从 x223 收到 x217，再扩到 x222。 |
| 仓库 | 左边从 y177/x32 收到 y185/x39，又在 y191 回到 x33；右边由 x287 收到 x280，再扩到 x286。 |
| 控制塔 | y167 为左右 x39/x152，下一行 y168 变成 x35/x156；同处接合出现轮廓台阶，详见 [塔同坐标接合图](control_tower_seam_source_4x.png)。 |

这些坐标用于定位用户可见的衔接，不把任意 Alpha 轮廓变化自动判成美术错误。原始未拆整栋参考已直接查看 `art-source/ember/selected-buildings-v001/references/repair_workshop_user_selected.png`，其屋顶下角与墙柱转折作为同一结构延续；当前工坊则明确读成两个带独立包边的部件叠放。

生产链定位：

- `tools/build_building_alignment_v003.gd:24` 的 8px 前檐、`:26`–`:40` 的保边分段登记只重新分配屋面跨度，沿用原先屋顶的完整包边，并未重建屋顶与墙共同角部。
- `scripts/ember/building_alignment_source_v003.gd:11` 在 `-wall_height+8` 登记屋顶；墙体继续由原 `building_asset_v001.gd:274` 登记。两套倒角都进入母实例。
- `tools/compose_buildings_v003.gd:8` 先 Roof 再 FrontWall 的组合顺序将这一形状忠实带入主交付，功能层合并本身未造成新失真。
- `tools/validate_building_alignment_v003.gd:65`–`:82` 明确跳过两侧各 12px 倒角，只对中间 `width-24` 列测空缝。中央无空缝及包围宽度相同的 PASS 没有覆盖此次用户指出的圆角连续性；这不是原测试声称圆角已经通过。

建议返修：先以三个 `selected-buildings-v001/references` 未拆整栋图建立统一外轮廓、檐口及柱帽连接，再从同一整体确定揭顶、门片、检修和前后遮挡所需拆层。角部和柱帽应只有一套结构关系，不继续依赖“分别完整包边的屋顶、墙体对齐后叠加”作为闭合依据。必要的屋面/墙面功能分层可以保留；随后重新导出主完整 PNG、固定主体、功能层与交互预制体，提交同尺度无辅助线的原图对照及圆角局部证据。未替生产方修改素材或代码。

## 已实际完成的有限技术验证

1. 从固定 ZIP 的每个 `source_member` 原 PNG、整数源矩形和目标坐标独立重组 **41 个功能层**，每层全 RGBA 差异 0。按闭合状态的显隐和状态镜片色重组 **3 张 complete_closed 与 3 张 fixed_shell**，六张全 RGBA 差异均 0。因此本缺陷已在正式完整图，不能仅重画预览。
2. 三栋 `canvas_px`、`pivot_px`、`footprint_px`、`wall_height_px`、doors、mounts 与 v002 全等；门洞、门片、安全区及设备位置没有声明外改动。旧 `building_asset_v001.gd`、`building_demo_v001.gd`、`building_demo_actor_v001.gd` 在两个固定包间字节相同。
3. runtime 增量仅资源入口、版本号及 `building_asset_v003.gd:58`–`:60` 的 RearShell 显隐；v003 demo 的 `load_state()` 函数体保持 v002 的玩家→接触盒→建筑恢复顺序，未发现旧读档修复回退。diff 已保存 [runtime diff](building_asset_v002_v003.diff)、[demo diff](building_demo_v002_v003.diff)。没有为了已退回的静态候选复跑历史数百项交互。
4. 三张 RearShell 功能 PNG 与 v002 全 RGBA 相同，仍完整纳入 catalog。闭合完整图重组时明确隐藏 RearShell；运行时代码在 `interior_visible or inspection_mode` 时显示，调用父级遮挡逻辑后再设置。控制塔另有下段窗后背衬进入 FrontWall；来源与裁切矩形保存在证据 JSON。静态/代码路径支持预期新规则，本次没有新增 GPU 或离树运行复验。

此次未执行完整 manifest 审计、冷 Godot 导入、118 GPU 组合复跑或 148/41/32 历史交互；这些不影响已定位并需返修的圆角问题。最终整包状态由根审查结合用户反馈与独立视觉报告发出，本文的静态 PASS 不构成美术 PASS。
