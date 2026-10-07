# 机器人 v003 的独立交付：逐帧核对、证据门禁、复制可编辑源，最后验证 ZIP 内每项 SHA。
# 本脚本不导入主工程，不改旧素材；暂存使用独立临时目录，避免覆盖旧 review。
[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$EvidenceConfigPath = 'art-source/ember/robot-actions-v003/package_evidence_v003.json',
    [string]$DeliveryName = 'robot_actions_v003_2026-10-06',
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskWorkspace = (Resolve-Path -LiteralPath $WorkspaceRoot).Path.TrimEnd('\', '/')
$taskSource = 'art-source/ember/robot-actions-v003'
$taskCatalogPath = 'assets/ember/characters/robot/robot_frames_catalog_v003.json'
$taskScene = 'scenes/ember/robot_animation_sandbox_v003.tscn'
$taskFiles = @{}

function Get-Field {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    if ($Object -is [System.Collections.IList] -and $Name -match '^\d+$') {
        $index = [int]$Name
        if ($index -ge $Object.Count) { return $null }
        return $Object[$index]
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Get-Fields {
    param($Object, $Names)
    $value = $Object
    foreach ($name in @($Names)) {
        if ($null -eq $value) { return $null }
        $value = Get-Field $value ([string]$name)
    }
    return $value
}

function Get-RelativePath {
    param([string]$Path)
    if ($Path.StartsWith('res://')) { $Path = $Path.Substring(6) }
    if ([IO.Path]::IsPathRooted($Path)) {
        $Path = [IO.Path]::GetRelativePath($taskWorkspace, [IO.Path]::GetFullPath($Path))
    }
    $Path = $Path.Replace('\', '/')
    if ($Path -match '(^|/)\.\.(/|$)' -or $Path -match '^[/:]' -or [string]::IsNullOrWhiteSpace($Path)) {
        throw "资源越出工作区或路径为空：$Path"
    }
    return $Path
}

function Resolve-SourceFile {
    param([string]$Path)
    $relative = Get-RelativePath $Path
    $resolved = [IO.Path]::GetFullPath((Join-Path $taskWorkspace $relative))
    if (-not $resolved.StartsWith($taskWorkspace + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "资源越出工作区：$Path"
    }
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) { throw "缺少交付依赖：$relative" }
    if (((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "依赖文件为链接，拒绝打包：$relative"
    }
    return $resolved
}

function Add-SourceFile {
    param([string]$Path)
    $relative = Get-RelativePath $Path
    $taskFiles[$relative] = Resolve-SourceFile $relative
}

function Assert-SourceHash {
    param([string]$Path, [string]$Expected)
    if ($Expected -notmatch '^[0-9a-fA-F]{64}$') { throw "没有有效 SHA256：$Path" }
    $actual = (Get-FileHash -LiteralPath (Resolve-SourceFile $Path) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Expected.ToLowerInvariant()) { throw "证据已过期，文件 SHA 不匹配：$Path" }
    return $actual
}

$taskCatalog = Get-Content -LiteralPath (Resolve-SourceFile $taskCatalogPath) -Raw | ConvertFrom-Json
if (@($taskCatalog.canvas).Count -ne 2 -or $taskCatalog.canvas[0] -ne 64 -or $taskCatalog.canvas[1] -ne 96) { throw '机器人画布必须为 64×96。' }
if (@($taskCatalog.anchor).Count -ne 2 -or $taskCatalog.anchor[0] -ne 32 -or $taskCatalog.anchor[1] -ne 80) { throw '机器人脚底锚点必须为 (32,80)。' }
if (@($taskCatalog.frames).Count -ne 40 -or @($taskCatalog.animations).Count -ne 12) { throw 'v003 必须包含 40 张原生帧与 12 段动作。' }
$taskFrameIds = @{}
$taskFramePaths = @{}
$taskNewFrameCount = 0
foreach ($frame in $taskCatalog.frames) {
    if ($taskFrameIds.ContainsKey([string]$frame.id)) { throw "重复帧 ID：$($frame.id)" }
    $path = Get-RelativePath ([string]$frame.file)
    if ($taskFramePaths.ContainsKey($path)) { throw "目录帧重复引用同一 PNG：$path" }
    if (-not $path.EndsWith('.png')) { throw "帧文件必须为 PNG：$path" }
    $taskFrameIds[[string]$frame.id] = $frame
    $taskFramePaths[$path] = $true
    Assert-SourceHash $path ([string]$frame.sha256) | Out-Null
    Add-SourceFile $path
    foreach ($sourcePair in @(@('pose_file','pose_sha256'), @('source_rig','source_rig_sha256'))) {
        $sourcePath = Get-Field $frame $sourcePair[0]
        if ($null -ne $sourcePath) {
            Assert-SourceHash ([string]$sourcePath) ([string](Get-Field $frame $sourcePair[1])) | Out-Null
            Add-SourceFile ([string]$sourcePath)
        }
    }
    if ($path.StartsWith('assets/ember/characters/robot/actions_v003/')) { $taskNewFrameCount++ }
}
if ($taskNewFrameCount -ne 20) { throw 'v003 必须新增 20 PNG，并复用旧 20 PNG。' }

# 旧 20 帧必须逐字节复用 v002，既防止漏包，也防止把历史断裂帧混入本次组合。
$taskOldCatalog = Get-Content -LiteralPath (Resolve-SourceFile 'assets/ember/characters/robot/robot_frames_catalog_v002.json') -Raw | ConvertFrom-Json
foreach ($old in $taskOldCatalog.frames) {
    $path = Get-RelativePath ([string]$old.file)
    if (-not $taskFramePaths.ContainsKey($path)) { throw "组合目录未复用已验收旧帧：$path" }
    Assert-SourceHash $path ([string]$old.sha256) | Out-Null
}
$taskClipIds = @{}
foreach ($clip in $taskCatalog.animations) {
    if ($taskClipIds.ContainsKey([string]$clip.id)) { throw "重复动作：$($clip.id)" }
    $taskClipIds[[string]$clip.id] = $true
    if ($clip.direction -notin @('down', 'left', 'right', 'up') -or $clip.state -notin @('idle', 'walk', 'collect')) { throw "未知动作或方向：$($clip.id)" }
    $expectedFrames = if ($clip.state -eq 'idle') { 2 } else { 4 }
    if (@($clip.frame_ids).Count -ne $expectedFrames -or [double]$clip.fps -le 0) { throw "动作长度或 FPS 不合法：$($clip.id)" }
    foreach ($id in $clip.frame_ids) {
        if (-not $taskFrameIds.ContainsKey([string]$id)) { throw "动作引用缺帧：$id" }
        $frame = $taskFrameIds[[string]$id]
        if ($frame.direction -ne $clip.direction -or $frame.state -ne $clip.state) { throw "动作混用方向或状态：$($clip.id)/$id" }
    }
}
foreach ($direction in @('down', 'left', 'right', 'up')) {
    foreach ($state in @('idle', 'walk', 'collect')) {
        if (-not $taskClipIds.ContainsKey($state + '_' + $direction)) { throw "缺少动作：${state}_${direction}" }
    }
}
Assert-SourceHash ([string]$taskCatalog.sheet.texture) ([string]$taskCatalog.sheet.sha256) | Out-Null
Add-SourceFile ([string]$taskCatalog.sheet.texture)

foreach ($path in @(
    $taskCatalogPath,
    'assets/ember/characters/robot/robot_frames_catalog_v002.json',
    'assets/ember/characters/robot/robot_sprite_frames_v003.tres',
    'scripts/ember/robot_action_preview_v003.gd',
    $taskScene,
    'tools/build_robot_actions_v003.gd',
    'tools/build_robot_animation_v003.gd',
    'tools/package_robot_actions_v003.ps1',
    'tools/validate_robot_actions_package_v003.ps1',
    'docs/shader-learning/asset-production-robot-actions-v003.md'
)) { Add-SourceFile $path }

# 可编辑旧 rig 和步行动作标注是来源依赖；只复制 JSON，忽略旧预览、缓存和生成母稿。
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $taskWorkspace 'art-source/ember/robot-repair-v002/annotations') -Filter '*.json' -File) { Add-SourceFile $file.FullName }

$taskEvidencePath = Resolve-SourceFile $EvidenceConfigPath
$taskEvidence = Get-Content -LiteralPath $taskEvidencePath -Raw | ConvertFrom-Json
if (@($taskEvidence.reports).Count -lt 2) { throw '至少需要像素检查和实际运行检查两份最终证据。' }
$taskReports = @{}
foreach ($entry in $taskEvidence.reports) {
    if ([string]::IsNullOrWhiteSpace([string]$entry.id) -or $taskReports.ContainsKey([string]$entry.id)) { throw '证据报告 ID 缺失或重复。' }
    $report = Get-Content -LiteralPath (Resolve-SourceFile ([string]$entry.path)) -Raw | ConvertFrom-Json
    $statusField = [string](Get-Field $entry 'status_field')
    if ([string]::IsNullOrWhiteSpace($statusField)) { $statusField = 'status' }
    $actualStatus = [string](Get-Field $report $statusField)
    $successValues = @(Get-Field $entry 'success_values')
    if ($successValues.Count -eq 0 -or $actualStatus -notin $successValues) { throw "证据不是最终 PASS：$($entry.id) / $actualStatus" }
    $issuesField = Get-Field $entry 'issues_field'
    if ($null -ne $issuesField) {
        $property = $report.PSObject.Properties[[string]$issuesField]
        if ($null -eq $property -or @($property.Value).Count -ne 0) { throw "证据仍有未解决问题或缺少问题字段：$($entry.id)" }
    }
    $taskReports[[string]$entry.id] = $report
    Add-SourceFile ([string]$entry.path)
}

# 本次交付需要实际帧、时序和输入状态检查；GPU 报告需覆盖全部 40×2 项，而非只截一张静态图。
foreach ($id in @('runtime','gpu')) {
    if (-not $taskReports.ContainsKey($id)) { throw "缺少最终运行证据：$id" }
    $observed = $taskReports[$id].observed
    # runtime_playback 是以场景节点路径为键的 JSON 对象；其值不是数组。
    # 数属性才能核对十二个独立 AnimatedSprite2D，而不是把整个对象误算成一项。
    $playbackCount = @($observed.runtime_playback.PSObject.Properties).Count
    if ($taskReports[$id].phase -ne 'verify' -or @($observed.source_frames).Count -ne 40 -or @($observed.resource_frames).Count -ne 40 -or $observed.atlas_regions_rgba_equal -ne 40 -or @($observed.clip_dependencies).Count -ne 12 -or $playbackCount -ne 12 -or @($observed.control_state_cases).Count -ne 4) { throw "运行证据没有覆盖完整 40 帧/12 动作/4 方向控制：$id" }
}
$gpuObserved = $taskReports['gpu'].observed
if ($gpuObserved.gpu_case_count -ne 80 -or @($gpuObserved.gpu_cases).Count -ne 80) { throw 'GPU 报告缺少完整 80 项读回。' }
foreach ($item in $gpuObserved.gpu_cases) {
    if ($item.alpha_changed -ne 0 -or $item.visible_rgb_changed -ne 0) { throw 'GPU 读回仍有 Alpha 或角色色差异。' }
}
if (-not $taskReports.ContainsKey('protected')) { throw '缺少旧源保留报告。' }
$allowedChanges = @('tools/assemble_map_asset_previews_v001.gd','scenes/ember/map_assets_tidal_port_v001.tscn','scenes/ember/map_assets_dry_mine_v001.tscn','scenes/ember/map_assets_overgrown_lab_v001.tscn')
foreach ($entry in $taskReports['protected'].files) {
    Assert-SourceHash ([string]$entry.path) ([string]$entry.sha256_after) | Out-Null
    if (-not $entry.unchanged -and ($entry.path -notin $allowedChanges -or -not $entry.authorized_registration_change -or -not $entry.only_expected_registration_change)) { throw "旧资源出现范围外改变：$($entry.path)" }
}
if (-not $taskReports.ContainsKey('encoding') -or -not $taskReports['encoding'].webp_exact_rgba -or $taskReports['encoding'].gif_native_palette_mismatch -ne 0 -or $taskReports['encoding'].native_palette_samples -le 0) { throw '动画预览没有通过无损/角色色检查。' }
if (@($taskEvidence.hash_bindings).Count -lt 2) { throw '最终证据必须绑定当前目录和工具的 SHA，不能仅检查 PASS 字样。' }
foreach ($binding in $taskEvidence.hash_bindings) {
    if (-not $taskReports.ContainsKey([string]$binding.report)) { throw "SHA 绑定引用未知证据：$($binding.report)" }
    $value = Get-Fields $taskReports[[string]$binding.report] $binding.field
    $key = Get-Field $binding 'key'
    if ($null -ne $key) { $value = Get-Field $value ([string]$key) }
    $expected = [string]$value
    Assert-SourceHash ([string]$binding.path) $expected | Out-Null
    if ((Get-Field $binding 'archive') -ne $false) { Add-SourceFile ([string]$binding.path) }
}
Add-SourceFile $EvidenceConfigPath

# 必须保留新 pose、生成记录与实际预览；拒绝源目录中的链接，排除会递归复制的打包/冷启动产物。
$sourceRoot = Join-Path $taskWorkspace $taskSource
foreach ($file in Get-ChildItem -LiteralPath $sourceRoot -Recurse -File) {
    $relative = Get-RelativePath $file.FullName
    if ($relative -match '/(\.godot|__pycache__|[^/]*-review|review-project|cold-start[^/]*|package-staging[^/]*)/' -or $file.Extension -in @('.log', '.tmp', '.pyc', '.import') -or $file.Name -match '^package_(validation|cold_start).*\.json$' -or $file.Name -eq 'helper_pid.txt') { continue }
    if ($relative -match '/map-registration/') { continue }
    Add-SourceFile $relative
}
$extraFiles = Get-Field $taskEvidence 'extra_files'
if ($null -ne $extraFiles) {
    foreach ($path in @($extraFiles)) { Add-SourceFile ([string]$path) }
}
$verify = Get-Field $taskEvidence 'cold_verify'
if ($null -eq $verify -or [string]::IsNullOrWhiteSpace([string]$verify.script) -or @($verify.arguments).Count -eq 0) { throw '缺少 cold_verify 脚本与只读检查参数。' }
Add-SourceFile ([string]$verify.script)
Write-Output ('ROBOT_PACKAGE_GATES_PASS: ' + $taskFrameIds.Count + ' frames; ' + $taskClipIds.Count + ' clips; ' + $taskReports.Count + ' reports')
if ($CheckOnly) { return }

if ($DeliveryName -notmatch '^robot_actions_v003_\d{4}-\d{2}-\d{2}$') { throw 'DeliveryName 必须是 robot_actions_v003_YYYY-MM-DD。' }
$taskDeliveries = [IO.Path]::GetFullPath((Join-Path $taskWorkspace 'art-source/ember/deliveries'))
if (Test-Path -LiteralPath $taskDeliveries) {
    if (((Get-Item -LiteralPath $taskDeliveries).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'deliveries 为链接，拒绝写入。' }
} else { New-Item -ItemType Directory -Path $taskDeliveries | Out-Null }
$taskArchive = Join-Path $taskDeliveries ($DeliveryName + '.zip')
$taskStage = Join-Path ([IO.Path]::GetTempPath()) ('CodexRobotActionsV003-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $taskStage | Out-Null
foreach ($path in @($taskFiles.Keys | Sort-Object)) {
    $target = Join-Path $taskStage $path
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $taskFiles[$path] -Destination $target
}
$project = @'
; 独立机器人动作审阅项目；不载入主项目的 Game autoload。
config_version=5

[application]
config/name="Ember Robot Actions v003"
run/main_scene="res://scenes/ember/robot_animation_sandbox_v003.tscn"
config/features=PackedStringArray("4.7", "GL Compatibility")

[display]
window/size/viewport_width=1536
window/size/viewport_height=1024
window/stretch/mode="canvas_items"

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
textures/default_filters/use_nearest_mipmap_filter=false
textures/canvas_textures/default_texture_filter=0
'@
Set-Content -LiteralPath (Join-Path $taskStage 'project.godot') -Value $project -Encoding utf8
$readme = @'
# 机器人动作 v003

这是可独立启动的 Godot 4.7.2 素材审阅工程。双击 Start.cmd，或在 Godot 导入本目录的 project.godot。

原生画布 64×96，固定虚拟脚底 (32,80)。四方向各含 2 帧 idle、4 帧 walk、4 帧 collect，共 40 PNG、12 段动作；新增 20 帧，旧版已验收 20 帧按原 SHA 复用。collect 是一次交互动作，具体播放/停顿以 SpriteFrames 中的设置为准。

工具说明、快捷键和实际检查记录见 docs/shader-learning/asset-production-robot-actions-v003.md。新动作使用可编辑像素部件与 pose 标注制作，源文件保留于 art-source/ember/robot-actions-v003/，原 rig 依赖位于 art-source/ember/robot-repair-v002/annotations/。

可复用入口：assets/ember/characters/robot/robot_sprite_frames_v003.tres、robot_frames_catalog_v003.json，以及 actions_v003/ 下的独立透明 PNG。展示场景使用整数缩放与 Nearest；本包没有主项目 Game autoload。

若 Godot 路径不同，可执行：

```powershell
.\run_showcase.ps1 -GodotPath 'D:\Godot\godot.exe'
.\run_validation.ps1 -GodotPath 'D:\Godot\godot.exe'
```

ZIP 不含本机 .godot 或 .import 缓存。file_hashes.json 记录逐文件 SHA（不含清单自身）；首次运行先导入资源。run_validation.ps1 使用独立日志和报告，不修改素材。
'@
Set-Content -LiteralPath (Join-Path $taskStage 'README.md') -Value $readme -Encoding utf8
$showcase = @'
param([string]$GodotPath = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe')
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $GodotPath -PathType Leaf)) { throw '请以 -GodotPath 指定 Godot 4.7.2 可执行文件。' }
$logs = Join-Path $PSScriptRoot 'validation-logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$stderr = Join-Path $logs 'showcase_import.stderr.log'
$process = Start-Process -FilePath $GodotPath -ArgumentList @('--headless', '--import', '--path', ('"' + $PSScriptRoot + '"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logs 'showcase_import.stdout.log') -RedirectStandardError $stderr
if ($process.ExitCode -ne 0 -or (Select-String -LiteralPath $stderr -Pattern 'SCRIPT ERROR|ERROR:' -Quiet)) { throw '导入失败，请查看 validation-logs。' }
& $GodotPath --path $PSScriptRoot 'res://scenes/ember/robot_animation_sandbox_v003.tscn'
'@
Set-Content -LiteralPath (Join-Path $taskStage 'run_showcase.ps1') -Value $showcase -Encoding utf8
$localVerify = @'
param([string]$GodotPath = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe')
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $GodotPath -PathType Leaf)) { throw '请以 -GodotPath 指定 Godot 4.7.2 可执行文件。' }
$logs = Join-Path $PSScriptRoot 'validation-logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'file_hashes.json') -Raw | ConvertFrom-Json
foreach ($entry in $manifest.files) {
    $path = Join-Path $PSScriptRoot $entry.path
    if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw ('文件缺失或 SHA 不一致：' + $entry.path) }
}
foreach ($stage in @('import', 'verify')) {
    $arguments = @('--headless', '--path', ('"' + $PSScriptRoot + '"'))
    if ($stage -eq 'import') { $arguments += @('--editor', '--import') }
    else {
        $arguments += @('--script', $manifest.cold_verify.script, '--')
        foreach ($argument in $manifest.cold_verify.arguments) {
            $value = [string]$argument
            $value = $value.Replace('{REPORT_PATH}', (Join-Path $logs 'runtime_report.json'))
            $arguments += ('"' + $value + '"')
        }
    }
    $stderr = Join-Path $logs ($stage + '.stderr.log')
    $process = Start-Process -FilePath $GodotPath -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logs ($stage + '.stdout.log')) -RedirectStandardError $stderr
    if ($process.ExitCode -ne 0 -or (Select-String -LiteralPath $stderr -Pattern 'SCRIPT ERROR|ERROR:' -Quiet)) { throw ($stage + ' 失败，请查看 validation-logs。') }
}
Write-Output 'ROBOT_ACTIONS_LOCAL_VALIDATION_PASS'
'@
Set-Content -LiteralPath (Join-Path $taskStage 'run_validation.ps1') -Value $localVerify -Encoding utf8
Set-Content -LiteralPath (Join-Path $taskStage 'Start.cmd') -Encoding ascii -Value @'
@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_showcase.ps1" %*
if errorlevel 1 pause
'@
$taskEntries = @(Get-ChildItem -LiteralPath $taskStage -Recurse -File | Sort-Object FullName | ForEach-Object {
    @{path=[IO.Path]::GetRelativePath($taskStage,$_.FullName).Replace('\','/'); bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
})
$taskManifest = @{revision='robot_actions_v003'; frame_count=40; new_frame_count=20; animation_count=12; canvas=@(64,96); anchor=@(32,80); main_scene=$taskScene; files=$taskEntries; cold_verify=$verify}
$taskManifestPath = Join-Path $taskStage 'file_hashes.json'
Set-Content -LiteralPath $taskManifestPath -Value ($taskManifest | ConvertTo-Json -Depth 9) -Encoding utf8
$taskExpected = @{}
foreach ($entry in $taskEntries) { $taskExpected[$entry.path] = $entry }
$taskExpected['file_hashes.json'] = @{bytes=(Get-Item -LiteralPath $taskManifestPath).Length; sha256=(Get-FileHash -LiteralPath $taskManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$taskPending = Join-Path ([IO.Path]::GetTempPath()) ('CodexRobotActionsV003-' + [guid]::NewGuid().ToString('N') + '.zip')
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($taskStage,$taskPending,[IO.Compression.CompressionLevel]::Optimal,$false)
$taskZip = [IO.Compression.ZipFile]::OpenRead($taskPending)
try {
    $seen = @{}
    foreach ($entry in $taskZip.Entries) {
        if ($entry.Name.Length -eq 0) { continue }
        $name = $entry.FullName.Replace('\','/')
        if ($seen.ContainsKey($name) -or -not $taskExpected.ContainsKey($name)) { throw "ZIP 包含额外或重复项：$name" }
        $seen[$name] = $true
        $expected = $taskExpected[$name]
        if ($entry.Length -ne $expected.bytes) { throw "ZIP 长度不符：$name" }
        $stream = $entry.Open()
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $actual = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','').ToLowerInvariant() }
        finally { $sha.Dispose(); $stream.Dispose() }
        if ($actual -ne $expected.sha256) { throw "ZIP SHA 不符：$name" }
    }
    if ($seen.Count -ne $taskExpected.Count) { throw 'ZIP 文件数量与清单不一致。' }
} finally { $taskZip.Dispose() }
if (Test-Path -LiteralPath $taskArchive) {
    if (((Get-Item -LiteralPath $taskArchive).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw '最终 ZIP 是链接，拒绝覆盖。' }
}
Move-Item -LiteralPath $taskPending -Destination $taskArchive -Force
$taskPackageReport = @{status='PASS'; revision='robot_actions_v003'; archive=$taskArchive; archive_sha256=(Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant(); stage_root=$taskStage; files=$taskExpected.Count; manifest_files=$taskEntries.Count; zip_entries_verified=$seen.Count; frame_count=40; new_frame_count=20; animation_count=12; evidence_config_sha256=(Get-FileHash -LiteralPath $taskEvidencePath -Algorithm SHA256).Hash.ToLowerInvariant(); tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant(); cold_start_validation='NOT_RUN_BY_PACKAGER'}
Set-Content -LiteralPath (Join-Path $sourceRoot 'package_validation_v003.json') -Value ($taskPackageReport | ConvertTo-Json -Depth 6) -Encoding utf8
Write-Output ('ROBOT_ARCHIVE_SAVED: ' + $taskArchive)
Write-Output ('ROBOT_ARCHIVE_SHA256: ' + $taskPackageReport.archive_sha256)
