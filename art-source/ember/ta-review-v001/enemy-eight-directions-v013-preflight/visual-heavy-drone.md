# 敌人 v013 方向母版独立静态预检：重型 / 无人机

结论：**重型新增七向 PASS_STATIC；无人机新增方向母版 NEEDS_REVISION。两类已批准 down 保留。** 本次只审核静态造型，不判断动画、相位切换或全批完成；巡逻兵、工蜂不在本报告的独立结论范围。

## 固定证据与范围

核对时间：2026-10-06 13:32:56 UTC。实际查看固定快照两张黑白底八向 4×联系图、两份生成原图、两张 approved_down、两张 generated_front 诊断图，以及重型/无人机全部 16 张实际中性 PNG 的原生/放大对照。16 张 PNG 的字节 SHA 均与快照 catalog 相符，生成原图也与 registration 所列 SHA 相符；审查副本保存在 `evidence-heavy-drone/`，未修改生产资源。

- 快照：`art-source/ember/enemy-eight-directions-v013/static_preflight_v001/`。
- catalog SHA：`8d673512350d2b388d04e250144d315ceac459263dcb6d0b6f6e19f7e5dd4e5a`。
- registration SHA：`d7f6f829318feb99d3ac252fd4c84a3638c5d47589f8a3849fa35610fabda68a`。
- 白底联系图 SHA：`d5ae887ff11416aeb474b00c6611063ab719ee64dc4d56e51305bdf9800e29ec`；黑底：`0842407dedbbca00c43d73cf49a04c618663869ab39464ee29fc5d4f6946e165`。
- 重型母图 SHA：`2cc4b365554c3eb1604e6c2b9360f8ea629adddbc0653e74bcd735b2df32e0e1`；无人机选用 v002 母图 SHA：`0926ff461b566cbc3935241d5077301c015d5b77c7ee9b138a68d71ac1d1f69b`。
- 全部图路径、SHA、裁切范围与最近邻倍率：`evidence-heavy-drone/image-binding.json`。

依据为 `docs/shader-learning/ember-enemy-animation-standard-v001.md`、`ember-enemy-eight-direction-standard-v002.md` 与 `ta-art-review-standard-v001.md` §3.3。相同单位须保持主体/组件体量、安装关系及固定左上光照；真实投影和遮挡可变化。

## 重型：新增七向通过静态预检

`down_left / left / up_left / up / up_right / right / down_right` 均未见明确的静态阻塞。

实际图中仍是同一短圆塔、蓝灰封闭顶盖、两组浅甲履带、黄铜轴座和一门短炮。前斜向炮口随朝向改变；纯侧向近履带遮住下部安装区，后斜向及 up 用背面格栅替代正面传感器/炮，未出现第二座塔或重复武器。left/right 展开同一组履带轮和胶边，远侧履带被机体遮住，能够读成双履带机的侧视。浅甲左上亮面与右侧暗面保持整体一致，未见简单镜像后亮面换边。

侧向履带长度展开、斜向底盘投影变深，以及顶盖/炮筒轮廓的像素取舍可以保留；没有仅以 bbox 的 71/80 宽度或 55/62 高度差判退。正向生成诊断图与批准 down 对比，主要塔体、履带罩和短炮的体量仍相近，未见无人机那种明显组件比例改写。

图证：`enemy_tracked_heavy_front_compare.png`、`enemy_tracked_heavy_{white,black}_dirs_{0,1}_detail.png`、`heavy_drone_native_1x.png`。以上均位于 `evidence-heavy-drone/`。

## 无人机：母稿组件比例与前传感器需修

### P2：风扇罩与机身/探头的相对体量改变

图证 `drone_front_and_up_native_10x.png` 保留同一 128×128 注册，依次为批准 down、生成正向诊断图、实际 up 母版，未按各图 bbox 缩放。图 SHA：`4afbeef17c509f8d2e8ab095e6e9b1d4b85e276a95dfdf048bfe59926a2ad8c7`。

同一正向对照里，新稿两只圆风扇罩明显变小并向中央机身收拢，机身本身和下端探头却没有同比例缩小。旧双转子中心约 x41.5 / 85.5；新生成正向的中心约 x50.5 / 88.5，去除整体平移后中心间距仍由约 44px 收为约 38px。这里中心数据只定位画面中已经可见的结构改变，不作为比例阈值。旧下端黄铜头亮面主要 x62–64，新生成正向为 x68–71，宽度也增加；不能靠整体放大新七向同时修复这两个相反变化。

实际 up 在 x41–58、x80–95 / y55–79 的圆舱与中央机身对照中仍显示较小圆舱、较紧舱距，底部探头约 x65–69 / y77–80 也更粗。up_left/up_right 及前斜向同样沿用了这套较小圆舱、较粗端件的母稿比例。left/right 的远风扇被机身遮挡是合理的，但近风扇也来自这套新体量，不能把纯侧向隐藏远舱当作修复证明。

因此需先修这套新增七向母稿的共同结构，然后重新提交对照；并不是按斜向总宽度较小逐张机械判错，也没有要求每个方向重现 down 的外接矩形。

最小修订：以已批准 down 锁定圆舱直径、双轴间距相对机身的关系、短连杆长度和原有小探头体量；回到方向母稿统一修改，保留真实侧向遮挡和四叶拓扑。不要改变已批准 down，不要对七张图各自拉宽，也不要仅增加整体缩放。

### P2：前斜向暗红传感器变成高亮黄橙点

down_left 的实际 x63,y67 为 RGBA `(252,255,7,255)`，紧邻 x64,y67 是红色；黑白底均读成一颗很亮的黄芯。down_right 的 x63,y67 为 `(250,169,6,255)`，x63,y68 为 `(248,77,0,255)`。相比批准 down 的 x63–64,y67–68 暗红槽，这个中性状态的器件换了明显不同的亮度/色相。生成正向诊断图也有同样的亮橙芯。

最小修订：前斜向沿用批准 down 的暗红传感器材料与亮度，保持朝向造成的槽宽/遮挡变化；不添加这种黄白亮芯。这里描述的是实际烘焙像素的观感，不推断作者使用了发光 shader。

## 逐方向结论

|方向|重型|无人机|
|---|---|---|
|down|保留已批准稿|保留已批准稿|
|down_left|PASS_STATIC|NEEDS_REVISION：共同圆舱/探头比例＋高亮传感器|
|left|PASS_STATIC|共同母稿体量返修；远舱遮挡可保留|
|up_left|PASS_STATIC|共同圆舱/探头比例返修|
|up|PASS_STATIC|NEEDS_REVISION：实际后向圆舱/舱距与端件比例|
|up_right|PASS_STATIC|共同圆舱/探头比例返修|
|right|PASS_STATIC|共同母稿体量返修；远舱遮挡可保留|
|down_right|PASS_STATIC|NEEDS_REVISION：共同圆舱/探头比例＋高亮传感器|

无人机七向暂不进入批量动作生产。原静态双风扇、双电机及四叶设计路线可保留，侧视只见近舱不构成独立缺陷。未要求动画证据作为本次静态预检阻塞；重型 PASS_STATIC 也不外推到任何新增动作或方向切换通过。
