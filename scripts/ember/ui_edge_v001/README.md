# A 边缘标记 UI 组件（当前修订 v003，路径保留 v001）

本目录只包含新的可复用 UI，不修改 `scenes/m0` 或 `project.godot`。
实例化入口：`res://scenes/ember/ui_edge_v001/components/edge_hud.tscn`，建议挂在 `CanvasLayer` 下。

## 数据接口

```gdscript
# 外部适配器读取玩法，再把结果交给 HUD；UI 自己不读写 Game。
hud.set_game_state({
    "life": 2,
    "max_life": 3,
    "energy": 145.0,
    "energy_goal": 380.0, # 由调用方明确注入；当前 Game 没有 goal 字段。
    "seconds": 78.0,
    "station_state": 0, # 0安全、1预警、2爆发、3冷却。
    "collecting": true,
    "station_name": "采能站 01",
})
hud.set_station_state(1, true)
hud.set_marker_screen_position(Vector2(280, 280), true)
hud.open_drawer()
hud.close_drawer()
```

`set_data(Dictionary)` 是 `set_game_state` 的别名，支持部分更新。
`get_game_state()` 返回深拷贝。`drawer_closed` 信号由返回按钮/`close_drawer` 发出。
`set_drawer_open(bool)` 用于直接同步外部开闭状态。
`get_available_world_rect()` 返回当前可见世界区域，供外部投影/检查使用。
`set_station_portrait(Texture2D)` 同步当前站点肖像；传 `null` 可清空，入树前也可以设置。

生命限制在 `[0,max_life]`；大于六格或可用高度不足时折叠格数，追加准确的 `life/max_life` 数字。相同生命数据和仅能量变化不会重建槽节点。
能量限制在 `[0,energy_goal]`；零/负/非有限目标按零处理，填充比例为零。
倒计时取非负并向上取整；`0秒` 为 `00:00`。不足100分钟保留 `MM:SS`，100分钟起至99小时采用 `HHhMM`，再长显示整天 `Xd`；10000天起使用科学计数天数。长格式为紧凑展示，完整非负秒数仍保存在 `timer.seconds` 浮点字段。
非法状态显示“未知”，没有任何状态行被激活，不会被当作安全。

## 实例场景和独立组件接口

| 场景 / 脚本 | 接口 | 可独立替换的层 |
| --- | --- | --- |
| `life_indicator` | `set_data(current:int,maximum:int=3),set_slot_budget(0..6)` | 生命轮廓、填充、标题 |
| `timer_badge` | `set_data(seconds:float)` | 暗底、四个角件、标题、动态时间 |
| `energy_progress` | `set_data(value:float,goal:float)` | 轨道、FillClip/填充、两端铜夹、数值和百分比 |
| `state_row` | `set_data(state:int,active:bool)` | 行底、白色可染竖条、状态图标、正文 |
| `station_marker` | `set_data(state:int,collecting:bool)` | 文字遮盖底、状态图标、正文 |
| `bracket_button` | 标准 `Button.text/pressed/disabled` | normal/hover/pressed底层、focus角层、正文 |
| `station_drawer` | `set_data(Dictionary),open(),close()` | 遮盖底、把手、标题角件、透明肖像、肖像框、状态行、目标进度、提示、返回按钮 |
| `edge_hud` | 上述HUD接口 | 生命周期HUD、场景标记、抽屉分别管理 |

## 程序判断和遮盖

- `edge_ui_state.gd` 是状态颜色、文字、图标和可采集语义的唯一映射。
- SAFE 和 WARNING 都允许“采集中”；外部还须判断玩家在采集区、停止移动且游戏正在进行。UI 不替外部完成这三个玩法判断。
- 全局能量目标在 HUD 和抽屉共用；抽屉不是虚构的站点储量面板。
- `EnergyProgress` 只裁 `FillClip` 的子节点。轨道、铜夹都在裁切外；满条宽度为 `size.x-20`，填充宽度为 `round((size.x-20)*ratio)`。
- `show_labels/show_clamps` 支持运行时立即更新；显示数值时最小高度64px，纯轨道24px。数值与百分比保留8px间隔；纯轨道宽96px即可，带默认数值建议至少224px，长数字会省略。
- `energy_track_32x16` 使用 `[8,4,8,4]` 九宫边距；填充从轨道内部 `(2,4)` 起，原生高度8px。
- 抽屉打开后缩短底部目标条并将时钟移到剩余世界区域右上。标记整块落在抽屉下或世界可见区外时隐藏；保留源屏幕坐标，关闭或调整尺寸后可恢复。
- 抽屉底板独立遮盖世界，只有抽屉/按钮 `mouse_filter=STOP`；所有 HUD、图标、文本为 `IGNORE`。关闭抽屉隐藏节点并释放其焦点。
- `close_drawer/close` 可重复调用，只有真实可见到隐藏时发出关闭信号；独立抽屉可入树前关闭。Button运行时禁用后在下一帧释放焦点并隐藏focus角层。
- 抽屉内部 `ContentClip` 裁切全部内容，铜拉手留在该层外，保持左侧外露。长标题/目标数值使用实际分配宽度和省略号，不扩大抽屉或越界；极大有限能量以科学记数表达，真实目标不被修改。
- 本抽屉非模态。`STOP` 只阻止鼠标事件传播，不阻断 `Input.get_axis` 等玩法轮询；接入方自行决定是否暂停/锁定移动。

全部文本由 Label/Button 的真实字体渲染，不在生图中烘焙。默认系统中文字体为 Microsoft YaHei / SimHei / Noto Sans CJK SC 回退，可通过共享 Style 工厂替换为项目字体。
共享字体采用700字重；覆盖世界的生命和目标HUD文字额外使用2px暗描边。
抽屉排布先为两行提示、8px按钮间隔和12px底边预留空间，再分配肖像高度；960×540下返回按钮仍完整可见。
静态PNG来自 `assets/ember/ui_final/skins/`，采能站透明肖像复用 `assets/ember/map_assets_v001/buildings/energy_station.png`。
所有皮肤节点采用 Nearest；世界瓦片的0.25缩放不能套到屏幕UI。

## v002 复用审计边界

保留 `ui_edge_v001` 路径，修订包标记为v002。完整布局实测逻辑画布480×480至1280×720；360×640开抽屉时优先完整显示224px终端并隐藏现场HUD，收起恢复。480px高时肖像隐藏以保留返回按钮，长数值可能省略。这不等于改变720×720逻辑画布的物理窗口缩放。

`safe_margin/drawer_width` 可运行时调整。可选M0适配器提供 `max_life` 参数（默认3），直接更换 `station_portrait` 会刷新；没有Node2D投影的数据源会清除旧标记。

静态皮肤、按钮、进度和时间组件可独立复用；状态行/标记/抽屉仍使用四种采能状态。父节点的通用Theme尚不能全面替换共享工厂的本地字体/颜色覆盖。完整设置、滚动列表、模态对话框需要新增逻辑组件，见项目证据目录的 `usability-audit-v002.md`。

## v003 离树与重新挂接

已构建HUD可从父节点移除后暂存，离树期间允许 `set_drawer_open/open_drawer/close_drawer`、数据和边距设置；关闭始终隐藏抽屉并设置IGNORE，不需要有效viewport。直接同步的 `set_drawer_open(false)` 保持不发关闭信号的契约。

重新挂接时在子节点和锚点恢复后按最新开闭状态同步布局；复用原组件实例，不调用 `request_ready()` 重新创建节点。焦点只交给已入树、可见、未禁用的返回按钮。独立Drawer在入树前close后也保持IGNORE。

自动设备标记要求设备与HUD都在树内且属于同一Viewport；暂时离树或跨Viewport时隐藏标记。跨视口映射由调用方通过 `set_marker_screen_position` 注入。组件本身不改变玩法暂停和移动规则。
