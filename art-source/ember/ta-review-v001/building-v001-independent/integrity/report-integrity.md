# 建筑 v001 独立来源与固定包完整性审查

结论：**SOURCE / REGISTRATION / ARCHIVE PASS（本报告范围）**。没有发现来源替换、RGB 改色、轴向拉伸、注册结果偏离规范、门洞残留或分层复装损失。本结论不代替整栋视觉、交互、存档及最新组合交付要求的 TA 验收。

审查对象是固定 ZIP `building_assets_v001_2026-10-06.zip`，SHA-256 `5870774d53e2010158523021661cf30a560386fe2826c39a66845d8e7e45dbc1`，69,786,519 字节。审查只读生产素材、脚本和 ZIP；只在本目录写入独立验证脚本、JSON 和本报告。没有启动 Godot 或覆盖固定包。

## 固定包与绑定

- 187 个文件条目，186 个 manifest 载荷；唯一不在载荷清单中的文件为清单自身 `portable_file_manifest_v001.json`。无重复路径；CRC、186 项字节数及 SHA 均通过。
- ZIP 内 manifest 与封包清单原件 SHA 均为 `9d019ed98626024deddf9537fee7c8510514876a4af4ec19e771294cc5dbe0e2`。包中没有 `.import`、`.godot` 缓存、prototype/precheck 或嵌套 godot-review 路径。
- source_specs 的 28 个 master ID 与 generation_manifest 完全相同，44 个 RGB 资产使用的源路径集合恰好为这 28 个 master；未使用 rejected 来源。28 个 master 与 imagegen 工具原始输出文件的 SHA 全部相等，28 份 prompt 和 reference 路径均存在。
- 47 个生产 asset ID 唯一，47 个 canvas / pivot / texture SHA / source SHA 匹配 catalog；3 个白色数据 Mask 均明确登记，来源绑定 source_specs，而不是伪装成 imagegen RGB。
- catalog → source_specs，registration → source_specs / build 脚本，validation → source_specs / catalog / registration / validator 的 7 项内容绑定均通过。
- 包内 184 个同路径工作区文件可直接比较；除 TA 规范快照外均相同。portable 根 `project.godot` 与 godot-review 的对应配置 SHA 一致，不能与主工程根配置混淆；`README_PORTABLE.md` 是封包脚本直接产生，清单哈希通过，其文本与 packager 声明内容相同。

TA 规范差异是封包后根代理按用户最新要求新增的 **4.1 建筑组合资源与交付边界**（6 行，详见 `ta-standard-snapshot.diff`）。这是包外政策更新，没有源图或生产 PNG 漂移；不要求覆写 v001 ZIP。v001 是否满足最新组合主交付要求由总审查单独判定。

## 注册与 ROI 独立复算

使用 Python 从原始 RGBA、source_specs 重新计算来源 Alpha 裁框、统一缩放尺寸、每个区域的来源/目标坐标、最近邻采样和 Alpha 规则，再与最终 PNG 逐像素比较。没有调用生产 validator 或以其 PASS 字段作结论。全部 47 件 **RGBA 差异 0**，其中 44 个 RGB 件保留像素均能追溯到规定来源采样。

读取实现 `tools/build_building_assets_v001.gd`：完整来源裁框只进行一次相同比例的 nearest 缩放；3 段墙面保护左/右结构，中间裁组装；9 段屋顶保护边角，不再缩放各段、不复制纹理填面。独立计算所有 region_segments 与 catalog 一致。整数尺寸是同一比例的 roundi 结果，普通注册各轴舍入误差不超过 0.5 像素，未发现任意宽高伸缩。

关键示例：塔墙原框 `[66,189,990,1077]` 统一缩至 `147×160`，安装 body `[2,2,128,160]`；保留 resized 源左 `[0,0,12,160]`、中 `[21,0,104,160]`、右 `[135,0,12,160]`，目标 x 分别为 2 / 14 / 118。具体 source ROI、比例、独立 segments 在 `integrity-evidence.json` 中逐件保存。

三格窗框不是整件不等比压缩：明确原稿 source cell 分别统一 nearest 后各进行 9 段保护，三格为 27 段；narrow frame 为单格 9 段。各格因整数来源分栏及目标宽度有轻微缩放舍入区别，属于已登记 segmented_frame。glass 来自真实闭合透明孔，独立 flood fill 排除外连空白和小于 16 像素的磨损孔，再裁于指定 frame 内口；没有依据 RGB 猜孔或填造缺失框材。

## Alpha、门洞与分层

- 47 件最终 Alpha 均为 0 / 255，半透明像素总数 0。规格中的所有 aperture / cutout 净口可见像素 0；personnel 净口 `40×56`、cargo 净口 `104×60` 与对应规定一致。
- 3 个数据 Mask 完全等于声明的白色矩形：lamp `[6,6,16,1]`，panel `[6,7,4,6]`，service `[12,18,8,2]`。Mask 与美术 RGB 来源分别记录。
- 4 组 native 分层逐像素复装均为 **0 重叠 / 0 RGBA 差异**：塔前墙 upper / storey-band / lower；塔 roof center / trim；工坊 roof center / trim；仓库 roof center / trim。
- 复装只证明已经提供的层能够完整还原该 parent PNG，不能证明整栋组合 PNG 已交付，也不能证明运行时排序和存档行为。

静态查看了正式 `gpu_parts_library_v001.png` 与 `gpu_buildings_native_2x_v001.png`，关键墙角、四周屋檐、门框及窗格在这些图中可辨识。未发现算法登记之外的额外颜色或纹理变化。nearest 下采样会减少细节，分段裁组装会移除来源中部宽度；此过程并不意味着用户原参考逐像素保真。较深屋顶、较大统一人员门、屋顶铜角帽减弱等设计差异已在提交说明中声明，仍须由总视觉审查判定接受。

## 用户参考与历史保护边界

3 张用户选定参考的当前 SHA 均匹配提交绑定：control tower `2e6212e1…906b4`，workshop `2bf26dba…3f71`，warehouse `d075ed00…eeed3`，完整 SHA 见 JSON。

对比既有 `ui-v003-integrity/integrity-v003.json` 的 protected_workspace 原记录，以下 5 个当前文件 SHA 均保持一致：

- `scenes/m0/energy_station.gd`
- `scenes/ember/map_assets_tidal_port_v001.tscn`
- `project.godot`
- `scenes/m0/ui.gd`
- `scenes/m0/ember_harvest.gd`

这是相对于该 UI 审查时间点的内容等同证明。记录没有原 robot / floor PNG 的历史 SHA，也不是建筑制作前专门快照，因此不扩大表述为“全部旧资产未改”。

## 复现与证据

在工程根目录运行 `python art-source/ember/ta-review-v001/building-v001-independent/integrity/verify_integrity.py`，只更新本目录 `integrity-evidence.json`。最近邻采样直接使用精确中心整数坐标；Pillow 的常规 resize 在恰逢整数边界的采样处可能有浮点累积偏差，不能把该工具差异当作生产 RGB 修改。

总审查可直接引用本报告的来源、技术注册和固定包通过结论；整体验收状态应继续结合独立视觉、引擎审查以及最新组合交付要求。
