# Ember 最终 UI · 唯一资源入口

按用户要求，新建并统一使用 **`res://assets/ember/ui_final/`**。

| 内容 | 位置 |
| --- | --- |
| 浏览所有资源、截图和组件 | [可视化总览](index.html)，可在本地浏览器打开；保留项目相对目录 |
| 18 张实际使用的皮肤 PNG | [skins/inventory.json](skins/inventory.json)；图片位于同一 `skins/` 文件夹 |
| 16 张最终 Godot 效果截图 | [previews/overview.png](previews/overview.png)；其他窗口和焦点／小屏示例位于 `previews/` |
| 可复用 UI 总入口 | [ui.tscn](ui.tscn)，放入宿主 CanvasLayer 并按使用说明接入数据与信号 |
| 可直接运行的完整示例 | [demo.tscn](demo.tscn)，在 Godot 打开后按 F6 |
| 继续制作的规范 | [UI 风格与制作规范](../../../docs/shader-learning/ember-ui-style-guide.md) |
| 真实数据接入 | [窗口与交互使用说明](../../../art-source/ember/ui-interactions-v004/README.md) |
| 原冻结的独立交付包 | [v006 ZIP](../../../art-source/ember/deliveries/ui_edge_interactions_v006_2026-10-06.zip) |
| 正式审核与规范统合 | [v006 回执](../../../art-source/ember/ta-review-v001/ui-v006-independent/review-ui-v006.md) · [规范统合回执](../../../art-source/ember/ta-review-v001/ui-spec-integration.md) |

## 文件夹用途

```text
ui_final/
├── skins/               18 张游戏运行时皮肤与尺寸合同
├── previews/            16 张引擎截图，只用于参考；.gdignore 避免导入游戏
├── ui.tscn              稳定的 UI 实例化入口
├── demo.tscn            稳定的可运行示例入口
├── index.html           可搜索、查看原图、复制路径的资源总览
├── catalog-manifest.json 总览文件绑定
└── README.md            本说明
```

`ui.tscn` 和 `demo.tscn` 复用现有场景，组件实现仍放在项目的 `scripts/` 和 `scenes/` 下。此目录中的 `skins/` 是活动皮肤的唯一来源，原 `assets/ember/ui_edge_v001/` 已迁移，图片没有复制第二套。

当前视觉与交互内容沿用已通过的 v006；本次是目录迁移和入口整理。原 v006 ZIP 保留原路径结构与 SHA256 `af61549eef1605a98301f822c2018d68bed4687118a2ed8c499073e71e758504`，用于重现原审查版本。当前工作区的皮肤加载路径、截图路径和工具已指向本目录，不能再宣称所有文件与原 ZIP 字节完全相同。

迁移文件映射及验证见 [folder-migration.json](../../../art-source/ember/ui-final/folder-migration.json)；历史清理记录见 [cleanup-report.json](../../../art-source/ember/ui-final/cleanup-report.json)。旧审查报告中的路径按迁移映射查找，历史冷目录仅保留证据，复验原版本请解压完整 ZIP。

在项目根目录运行 `python tools/build_ui_final_catalog.py` 可重建此处总览；不会重新生成图片。浏览器工具不允许打开本地 `file://` 页面，本轮总览仅做文件、链接及脚本检查。
