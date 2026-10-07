# V027 v001 实际安装增量验收

日期：2026-10-07。结论：**PASS_INSTALLATION_ONLY**。

对应此前统一包 PASS_ASSEMBLY_ONLY，新增确认实际 `assets/ember/characters/enemies_v003` 和 `review-current` 安装正确。未发现阻断项。

固定 ZIP：`art-source/ember/deliveries/enemy_sequences_eight_directions_v027_v001_2026-10-07.zip`，SHA256 `aba87363a03247ab5069dc2d21dac9544a29e200932d86f0d7aa2a8a12e91826`。未改写冻结包与其中的历史待审记录。

## TA 独立验证

- 1157 项实际安装载荷与固定 ZIP 的 output 逐字节一致，包括 4 个 SpriteFrames、160 图集、960 单帧、32 neutral 和 catalog。
- 检查 1152 张 PNG 的 `.import`：源路径均为新目录，Lossless、关闭 mipmaps / fix_alpha_border / premult_alpha / 自动 3D 压缩；2304 个 ctex/md5 缓存文件与安装回执 SHA 相符，remap 指向真实缓存。
- 以真实主项目为 `--path`，运行 TA 独立 headless 探针，通过 `res://assets/ember/characters/enemies_v003/` 加载四个已安装资源。160 段、960 格实际 RGBA（含透明像素）、图集区域、尺寸、帧时长、FPS、循环属性全部通过。引擎退出 0，stderr 为空。未运行作者验证脚本来代替独立验证。
- 472 个保护文件的当前 SHA/大小与安装前记录、作者安装后记录一致。旧预览备份的 index/status 与安装前 SHA 一致。安装前状态基于留存回执，TA 在本轮独立核对其当前文件匹配性。
- 当前预览 1154 项文件与上轮已验证的固定预览逐字节一致。浏览器实际打开当前入口，确认 v027 / 160 段 / 960 帧，抽查四种单位路由、移动播放及攻击/受击单次结束行为；实际画面正常载入。

证据：`check.py`、`technical-installation.json`、`probe.gd`、`resource-load.json`、`load.stdout.log`、`load.stderr.log`、`root-current-entry.png`。先前完整逐帧视觉与 320 切向 / 320 自然播放器验证保留在 `../enemy-v027-unified-v001/review-unified-package.md`。

## 范围与交接

通过范围是已安装视觉资源和当前预览入口。本轮未重复作者 GPU 矩阵测试，也未启动主游戏验证 AI、伤害或碰撞；不将这些列为本次通过项。

生成端可把活动安装状态更新为 `PASS_INSTALLATION_ONLY` 并引用本回执，同时保留此前汇总验收来源。不要回写固定 ZIP 或冻结包中的历史 PENDING 状态。后续新增内容另开批次；模型设置继续 GPT-6 Astra / High。
