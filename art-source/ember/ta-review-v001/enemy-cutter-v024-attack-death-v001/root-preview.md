# C24 v001 根实际入口与姿态复核

2026-10-07，入口 `http://127.0.0.1:6106/cutter-attack-death-v024-v001/index.html`，固定ZIP SHA `c3c1d9fb84d909fb113ee0a9d7ddac6afa98b8132f669ae0f5be5fa0963d572c`。

## 实际操作和所见

- 七新向SW/W/NW/N/NE/E/SE逐向查看attack F03浅底4×，同相位与旧S并列。另逐向查看death F07浅底4×，SE死亡由实际正常播放停到第8/8帧，切向保留末帧。
- NW attack F03锯盘明显变成U形/开口钩，随后逐步核F00/F01/F02/F03深底4×。原中性盘形在极值时缺扇区，背景开口随盘改变方位，不能读作完整圆盘仅改变透视；NW death F07也有缺口。已交独立视觉/技术线查固定可见半盘与自转来源。E attack F03盘外轮廓偏直切，需要同批来源检查。
- NE death F07远前腿原小块露在壳外，根先记录疑点；独立视觉局部复看发现仍沿壳缘承接，未仅因小块暴露就判断肢，最终以专项来源及实图合并。
- SE attack F03工具臂旁的小浅片和关节，在脚掌探针/UV来源发现语义边界后交专项继续核，不能以工具像素替代前脚接地。
- NW在慢速1FPS启动攻击，查看状态进展，再用单步定位上述姿态；另用正常10FPS、原生1×深底从头播放，观察第1/6至第6/6和“从头播放当前动作”结束状态。截图是离散状态证据，不冒称完整连续录像。

## 截图

七新向各有 `root-{sw,w,nw,n,ne,e,se}-attack-f03-light-4x.png` 和 `root-{sw,w,nw,n,ne,e,se}-death-f07-light-4x.png`。

重点：[NW攻击F03浅底](root-nw-attack-f03-light-4x.png)、[深底](root-nw-attack-f03-dark-4x.png)、[F02深底](root-nw-attack-f02-dark-4x.png)、[F01深底](root-nw-attack-f01-dark-4x.png)、[原F00深底](root-nw-attack-f00-dark-4x.png)、[正常原生攻击结束](root-nw-attack-normal-dark-native.png)。

[NW死亡末帧](root-nw-death-f07-light-4x.png)、[NE死亡末帧](root-ne-death-f07-light-4x.png)、[SE攻击极值](root-se-attack-f03-light-4x.png)、[SE死亡末帧](root-se-death-f07-light-4x.png)。

本记录不能单独覆盖全98新帧，需合并全帧视觉与独立技术报告。已见锯盘身份缺口不能因源像素一致、静态bind零差或冷加载通过而放行。

## 合并补记

N attack 另以原生正常10FPS浅底从头播放到结束，并单步看F03浅底4×。实际主要为待机同幅度起伏，F03没有明确攻击释放；与独立C23 idle逐帧比对一致，作为第二项P2。截图为 `root-n-attack-normal-light-native.png` 与 `root-n-attack-f03-light-4x.png`。

NE death疑点经实际来源核实，是原固定 `front_left_foot`（约x41–44、y77–80），F04–F07有真实像素贴接body，不是旋转上腿或新增碎片。SE工具附近复核未另确认关节视觉P2，但名义sole误落工具必须校正登记。

作者新增NW轴心登记偏离实际金色轮毂的线索尚不算TA验证的唯一根因。正式返修允许先校准已有固定源的轮毂、刃片范围和遮挡，再以实际所有相关帧的轮廓验收，不强制重做母稿。
