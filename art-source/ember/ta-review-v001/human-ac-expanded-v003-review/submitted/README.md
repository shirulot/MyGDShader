# A / C 方向与动作扩展 v003

这是供用户挑选和复审的动作试样，不是通过视觉验收的生产资源。

- A 勘探员、C 信号员：八方向待机、行走、跑动，合计48段。
- 两人各增加左向下蹲起身、原地跳跃、采集、原地推力、原地拉力，合计10段。
- 总计58段、456帧。6段左向基础动作的40帧逐字节沿用v002。
- 每帧64×96，虚拟地面root=(32,80)；方向依次down/down_left/left/up_left/up/up_right/right/down_right。
- 新待机125ms，行走120ms，跑动80ms，下蹲150ms，跳跃110ms，采集160ms，推拉140ms。左向旧待机保持4帧×250ms。

## 查看

当前预览：http://127.0.0.1:8158/revisions/human-ac-expanded-v003/preview.html

页面提供八向切换、正常与慢速、1×与4×、深浅背景、逐帧和尾首四帧对照。新增交互动作目前只做左向，方向按钮会禁用未制作方向。

`final/` 是透明PNG图集和逐段JSON；`frames/` 是逐帧PNG；`previews/` 是普通/慢速WebP；`qa/` 是1×/4×深浅底联系图、首尾帧条与检查记录。

## 已知问题与验收边界

新增斜向走跑的上下半周期仍存在身体朝向摆幅和水平定位漂移，新增待机存在轮廓细节跳动。首尾相接不代表视觉无缝，当前仍须修订。尚未通过同一角色跨帧一致性、真实浏览器十周期观看或Godot播放验收。浏览器自动化连接失败；播放器脚本11周期模拟检查仅证明索引不越界和尾帧能返回首帧。

推拉保留原地施力版本；尝试带位移的版本出现裤腿露肤、支撑及步相问题，作为rejected原稿保存，没有进入目录。脚本没有用倒放、交叉淡化或逐帧bbox缩放/居中掩盖问题。

新增图像通过imagegen按单角色、单方向、单动作生成，再进行整段共同缩放、二值Alpha和固定18色量化。源图的4×2排版每行使用共同地面基线；这仍不等于可靠的动画骨架注册。64×96导出是诊断资产，不能称为原生逐像素完成稿。

## 来源与复现

遵循`docs/shader-learning/ember-art-unified-v001.md`和`ta-art-review-standard-v001.md`；用户最新授权扩展方向和动作，覆盖旧版仅左向基础动作的范围限制。

走跑姿态参考：Hormelz 的 [8 Directional Melee Character](https://hormelz.itch.io/8-directional-melee-character)，作者标注CC0。仅参考姿态，角色外观沿用用户选择的A/C。未获取或声称匹配Dead Revolver付费完整包。

`source/extended-generation-ledger.json`记录本轮后续生成和修订来源；早期记录见`source/generation-ledger.json`及`prompts/`。公开参考压缩包、抽取脚本和姿态板保存在`references/`。`package.py`只切片、共同注册、量化和导出；`audit_delivery.py`检查导出并制作联系图，`qa/check-player.cjs`检查播放器。

未替换Godot主工程角色，未改旧v002的PNG与ZIP。当前ZIP是导出审阅包，包含实际帧、图集、预览及检查材料；完整生成历史保留在本目录。
