# v006 重绘与铺刷修复

2026-10-05。可运行的候选版本，尚未取得用户视觉认可。

## 直接查看

- 实际 Godot 渲染：[godot_render.png](../../assets/ember/environment/autotiles_v006/godot_render.png)。
- 可操作铺刷页：[autotile_sandbox_v006.tscn](../../scenes/ember/autotile_sandbox_v006.tscn)，Godot 打开后 F6。左键画，右键擦，滚轮缩放，中键拖动。水面与岸沿同时更新。
- 完整笔刷图集：[floor](../../assets/ember/environment/autotiles_v006/floor_autotile_v006.png)、[wall](../../assets/ember/environment/autotiles_v006/wall_autotile_v006.png)、[bridge](../../assets/ember/environment/autotiles_v006/bridge_autotile_v006.png)。原稿见 `art-source/ember/autotiles-v006/`。

## 本轮实际修改

| 类别 | 本轮采用 | 数量 |
| --- | --- | ---: |
| 地板 | 完整重绘，降低重复锈斑，保留金属倒角与圆润转折 | 47 |
| 墙体 | 重绘清理墙顶；排除逐格凸起版本；校正开放边切片漂移 | 47 |
| 栈桥 | 完整重绘；整体注册消除多余留白造成的纵向断口 | 16 |
| 水面、池岸、管线、栏杆 | 复用 v005；两轮池岸新稿因串边而排除 | 126 |

共 236 个连接配置，其中 110 个采用本轮新图。纹理 128px，世界格 32 单位。数量不增加原课程素材预算；未替换主游戏引用。

## 裂图的实际原因

1. 生成的整张 atlas 虽然看似按网格排版，行边界仍会漂移几像素。把它机械均分会把相邻格的边梁、立面或阴影切入当前格。
2. 栈桥图还有额外留白。只统一最外一排像素，内部仍可能断开。
3. 生图会误把相邻格画成一个连续展示对象，例如池岸跨行阴影。此类稿不能通过改 Terrain 编号修好，已保留为拒收稿。

导入时先逐格裁切，再独立缩放。地板/墙体开放边剔除 4px 注册偏差后整体归位，闭合外边保留；栈桥按整体占位包围盒注册，不描摹旧图轮廓、不拼接局部肢臂。最后只在 8px 开放接口边带校准共享截面。原始母稿、注册图和运行图分别保存，便于审阅处理影响。

## 验证与限制

- 实际 Godot Terrain 邻接、随机铺设及擦除后重建：25,541 个格子，0 失败。
- 所有兼容接口：2,960 对，RGBA 边缘不匹配 0。
- 路径端口到主体的 Alpha 连通性：48 个图块，0 失败。栈桥和栏杆是透空结构，不要求端口中央实心。
- 已检查 GPU 渲染的长条、凹洞、转角和分支。墙顶横向串边及栈桥大段断口已修正。
- 技术检查不代表美术已通过：地板局部圆角接点仍有重复感，墙面材质仍能看到轻微块间明暗差，栈桥接头的局部纹理连续性仍需结合实际使用比例判断。池岸新稿没有通过审查，不能登记为重绘完成。

## 重建

依次执行：

```powershell
python tools/build_ember_autotiles_v006.py
python tools/check_ember_v006_ports.py
# $engine 指向本机 Godot 可执行文件；GUI 版使用 Start-Process -Wait 等待结束。
& $engine --headless --path . --editor --import
& $engine --headless --path . --script res://tools/build_ember_autotiles.gd -- --revision=v006
& $engine --path . --script res://tools/capture_ember_seams.gd -- --revision=v006
```

不传 `--rebuild-demo` 时，构建器保留已存在的铺刷场景，避免覆盖手工修改的布局。
