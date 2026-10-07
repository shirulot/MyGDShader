# 独立素材包：先校验最终证据，再复制 review；本脚本不导入 Godot、不同步 review。
# 路径尚未定稿时可传入各 ReportPath，或 EvidenceConfigPath JSON（report_paths / hash_bindings）。
# -CheckOnly 只执行完整性门禁，不创建、清理或修改交付目录。
[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$ReviewRoot = '',
    [string]$DeliveryName = 'map_assets_v001_2026-10-06',
    [string]$SpriteReportPath = 'assets/ember/map_assets_v001/sprite_validation_v001.json',
    [string]$FloorReportPath = 'assets/ember/map_assets_v001/floors/independent_validation_v001.json',
    [string]$GpuReportPath = 'assets/ember/map_assets_v001/floors/gpu_capture_v001.json',
    [string]$RegistrationReportPath = 'assets/ember/map_assets_v001/sprite_registration_v001.json',
    [string]$VisualReportPath = 'assets/ember/map_assets_v001/visual_review_v001.json',
    [string]$PlacementReportPath = 'assets/ember/map_assets_v001/map_placements_v001.json',
    [string]$SourceSpecsPath = 'art-source/ember/map-assets-v001/source_specs_v001.json',
    [string]$EvidenceConfigPath = '',
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$workspacePath = (Resolve-Path -LiteralPath $WorkspaceRoot).Path
if ([string]::IsNullOrWhiteSpace($ReviewRoot)) {
    $ReviewRoot = Join-Path $workspacePath 'art-source\ember\map-assets-v001\godot-review'
}
$reviewPath = (Resolve-Path -LiteralPath $ReviewRoot).Path.TrimEnd('\', '/')
$deliveriesPath = [IO.Path]::GetFullPath((Join-Path $workspacePath 'art-source\ember\deliveries'))
if ($DeliveryName -notmatch '^map_assets_v001_\d{4}-\d{2}-\d{2}$') {
    throw 'DeliveryName 必须为 map_assets_v001_YYYY-MM-DD，避免误清理其他交付。'
}
$deliveryPath = [IO.Path]::GetFullPath((Join-Path $deliveriesPath $DeliveryName))
$archivePath = $deliveryPath + '.zip'
$pendingArchivePath = $archivePath + '.pending'
$mainScene = 'scenes/ember/map_assets_tidal_port_v001.tscn'
$mapIds = @('tidal_port', 'dry_mine', 'overgrown_lab')

function Get-Field {
    param($Object, [string]$Name)
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Resolve-ReviewPath {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { throw '证据或资源路径为空。' }
    if ($Path.StartsWith('res://')) { $Path = $Path.Substring(6) }
    $resolved = if ([IO.Path]::IsPathRooted($Path)) { [IO.Path]::GetFullPath($Path) } else { [IO.Path]::GetFullPath((Join-Path $reviewPath $Path)) }
    if (-not $resolved.StartsWith($reviewPath + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "资源必须位于独立 review 内，不能依赖工作区外部文件：$Path"
    }
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) { throw "缺少必需文件：$resolved" }
    return $resolved
}

function Read-ReviewJson {
    param([string]$Path)
    return (Get-Content -LiteralPath (Resolve-ReviewPath $Path) -Raw | ConvertFrom-Json)
}

function Assert-Hash {
    param([string]$Path, [string]$Expected, [string]$Label)
    if ($Expected -notmatch '^[0-9a-fA-F]{64}$') { throw "$Label 缺少有效 SHA256：$Path" }
    $actual = (Get-FileHash -LiteralPath (Resolve-ReviewPath $Path) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Expected.ToLowerInvariant()) { throw "$Label 与当前文件不一致，请重新验收：$Path" }
    return $actual
}

$reportPaths = [ordered]@{sprite=$SpriteReportPath; floor=$FloorReportPath; gpu=$GpuReportPath; registration=$RegistrationReportPath; visual=$VisualReportPath; placements=$PlacementReportPath}
$hashBindings = @(
    @{report='registration'; field='tool_sha256'; path='tools/export_map_sprites_v001.gd'},
    @{report='registration'; field='source_specs_sha256'; path=$SourceSpecsPath},
    @{report='sprite'; field='validator_sha256'; path='tools/validate_map_sprites_v001.gd'},
    @{report='sprite'; field='registration_sha256'; path=$RegistrationReportPath},
    @{report='floor'; field='validator_sha256'; path='tools/validate_map_floors_v001.gd'},
    @{report='floor'; field='builder_sha256'; path='tools/build_map_assets_v001.gd'},
    @{report='floor'; field='painter_sha256'; path='scripts/ember/map_asset_painter_v001.gd'},
    @{report='floor'; field='compiler_sha256'; path='scripts/ember/reference_floor_compiler_v002.gd'},
    @{report='gpu'; field='tool_sha256'; path='tools/assemble_map_asset_previews_v001.gd'},
    @{report='gpu'; field='painter_sha256'; path='scripts/ember/map_asset_painter_v001.gd'},
    @{report='gpu'; field='compiler_sha256'; path='scripts/ember/reference_floor_compiler_v002.gd'},
    @{report='gpu'; field='source_specs_sha256'; path=$SourceSpecsPath},
    @{report='gpu'; field='sprite_registration_sha256'; path=$RegistrationReportPath},
    @{report='visual'; field='source_specs_sha256'; path=$SourceSpecsPath},
    @{report='placements'; field='tool_sha256'; path='tools/assemble_map_asset_previews_v001.gd'}
)
if (-not [string]::IsNullOrWhiteSpace($EvidenceConfigPath)) {
    $config = Get-Content -LiteralPath $EvidenceConfigPath -Raw | ConvertFrom-Json
    $configuredPaths = Get-Field $config 'report_paths'
    if ($null -ne $configuredPaths) {
        foreach ($key in @($reportPaths.Keys)) {
            $value = Get-Field $configuredPaths $key
            if ($null -ne $value) { $reportPaths[$key] = [string]$value }
        }
    }
    $configuredBindings = Get-Field $config 'hash_bindings'
    if ($null -ne $configuredBindings) { $hashBindings = @($configuredBindings) }
}
# 报告路径重定向后，引用注册报告的 SHA 也跟随同一份文件。
foreach ($binding in $hashBindings) {
    if ($binding.field -in @('registration_sha256', 'sprite_registration_sha256')) {
        $binding.path = $reportPaths.registration
    }
}
$reports = @{}
foreach ($key in $reportPaths.Keys) {
    $report = Read-ReviewJson $reportPaths[$key]
    $failures = Get-Field $report 'failures'
    if ((Get-Field $report 'status') -ne 'PASS' -or @($failures | Where-Object { $null -ne $_ }).Count -ne 0) {
        throw "$key 最终报告未完整 PASS：$($reportPaths[$key])"
    }
    $reports[$key] = $report
}
if ($hashBindings.Count -eq 0) { throw 'hash_bindings 不能为空；必须将验收证据绑定到实际工具和规格。' }
foreach ($binding in $hashBindings) {
    $reportKey = [string]$binding.report
    if (-not $reports.ContainsKey($reportKey)) { throw "未知报告绑定：$reportKey" }
    $hash = Assert-Hash -Path $binding.path -Expected ([string](Get-Field $reports[$reportKey] $binding.field)) -Label "$reportKey.$($binding.field)"
    # 当前根目录代码/规格存在时要求已同步，避免打包落后的隔离副本。
    $relativePath = [IO.Path]::GetRelativePath($reviewPath, (Resolve-ReviewPath $binding.path))
    $workspaceCounterpart = Join-Path $workspacePath $relativePath
    $isCurrentInput = $relativePath -match '\.gd$' -or $relativePath -match '(^|[\\/])source_specs_v001\.json$'
    if ($isCurrentInput -and (Test-Path -LiteralPath $workspaceCounterpart -PathType Leaf)) {
        $workspaceHash = (Get-FileHash -LiteralPath $workspaceCounterpart -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($workspaceHash -ne $hash) { throw "工作区与已验收 review 尚未一致：$relativePath" }
    }
}

$specs = Read-ReviewJson $SourceSpecsPath
$sourceEntries = @($specs.sprites) + @($specs.floors) + @($specs.backgrounds) + @($specs.pipe_kit)
$masterPaths = @($sourceEntries | ForEach-Object { [string]$_.source_path } | Sort-Object -Unique)
foreach ($path in $masterPaths) { Resolve-ReviewPath $path | Out-Null }
# 来源文档是独立包的一部分；同时检查提示词和 generation 记录，避免只带 PNG 丢失来源。
foreach ($path in @('assets/ember/map_assets_v001/README.md', 'art-source/ember/map-assets-v001/README.md')) {
    Resolve-ReviewPath $path | Out-Null
}
$generationManifest = Read-ReviewJson 'art-source/ember/map-assets-v001/generation_manifest_v001.json'
Assert-Hash $generationManifest.source_specs $generationManifest.source_specs_sha256 'generation manifest specification' | Out-Null
$manifestMasters = @{}
foreach ($source in @($generationManifest.sources)) {
    Assert-Hash $source.source $source.source_sha256 'generation manifest source' | Out-Null
    Assert-Hash $source.prompt $source.prompt_sha256 'generation manifest prompt' | Out-Null
    Assert-Hash $source.generation_record $source.generation_record_sha256 'generation manifest provenance' | Out-Null
    $manifestMasters[[string]$source.source] = $true
}
if ($manifestMasters.Count -ne $masterPaths.Count) { throw '来源清单与规格的唯一母稿数量不一致。' }
foreach ($path in $masterPaths) {
    if (-not $manifestMasters.ContainsKey($path)) { throw "来源清单缺少规格母稿：$path" }
}
$registeredIds = @{}
foreach ($entry in @($reports.registration.sprites)) {
    if ($entry.status -ne 'PASS') { throw "注册记录未 PASS：$($entry.id)" }
    $registeredIds[[string]$entry.id] = $true
    Assert-Hash $entry.source_path $entry.source_sha256 "sprite source $($entry.id)" | Out-Null
    Assert-Hash $entry.texture $entry.texture_sha256 "sprite texture $($entry.id)" | Out-Null
    Assert-Hash $entry.scene $entry.scene_sha256 "sprite scene $($entry.id)" | Out-Null
}
$expectedSpriteIds = @($specs.sprites | ForEach-Object { [string]$_.id }) + @($specs.pipe_kit.components)
foreach ($id in $expectedSpriteIds) {
    if (-not $registeredIds.ContainsKey([string]$id)) { throw "规格中的素材尚未注册：$id" }
}
if ([int]$reports.sprite.sprites_checked -ne $registeredIds.Count) { throw 'Sprite 验收数量与最终注册目录不一致。' }
$catalog = Read-ReviewJson 'assets/ember/map_assets_v001/floors/catalog.json'
foreach ($material in @($catalog.materials)) {
    Assert-Hash $material.texture $material.sha256 "floor material $($material.id)" | Out-Null
}
$sourceProcessing = Read-ReviewJson 'assets/ember/map_assets_v001/floors/source_processing_v001.json'
foreach ($entry in @($sourceProcessing.sources)) {
    Assert-Hash $entry.source $entry.source_sha256 'floor master' | Out-Null
    Resolve-ReviewPath $entry.output | Out-Null
}
$gpuMaps = @{}
foreach ($entry in @($reports.gpu.scene_entries)) {
    $gpuMaps[[string]$entry.map_id] = $true
    Assert-Hash $entry.scene $entry.scene_sha256 "GPU scene $($entry.map_id)" | Out-Null
    Assert-Hash $entry.screenshot $entry.screenshot_sha256 "GPU screenshot $($entry.map_id)" | Out-Null
}
foreach ($id in $mapIds) {
    if (-not $gpuMaps.ContainsKey($id)) { throw "GPU 报告缺少地图：$id" }
    Resolve-ReviewPath ('scenes/ember/map_assets_' + $id + '_v001.tscn') | Out-Null
}
# 视觉审阅必须针对最终截图，不能只保留前一版 NEEDS_VISUAL_FIX 或已过期的 PASS。
$issuesProperty = $reports.visual.PSObject.Properties['issues']
# 直接检查属性：PowerShell 函数会展开空数组，不能把合法的 [] 误判为缺字段。
if ($null -eq $issuesProperty -or -not ($issuesProperty.Value -is [Array]) -or @($issuesProperty.Value).Count -ne 0) {
    throw '最终视觉报告缺少空 issues 数组，或仍有需要修正的问题。'
}
$visuallyCheckedFiles = @{}
foreach ($entry in @($reports.visual.screenshots)) {
    $path = [string]$entry.path
    if (-not $path.StartsWith('res://') -and -not $path.StartsWith('assets/')) {
        $path = 'assets/ember/map_assets_v001/' + $path
    }
    Assert-Hash $path $entry.sha256 'final visual screenshot' | Out-Null
    $visuallyCheckedFiles[(Resolve-ReviewPath $path)] = $true
}
foreach ($entry in @($reports.gpu.scene_entries)) {
    if (-not $visuallyCheckedFiles.ContainsKey((Resolve-ReviewPath $entry.screenshot))) {
        throw "最终视觉报告未覆盖 GPU 地图截图：$($entry.map_id)"
    }
}
Resolve-ReviewPath 'project.godot' | Out-Null
Write-Output "PACKAGE_GATES_PASS: $($masterPaths.Count) masters; $($registeredIds.Count) sprites; $($mapIds.Count) maps"
if ($CheckOnly) { return }

# 递归清理前验证最终绝对目录为 deliveries 的直属、指定名称子目录，并拒绝链接。
if ([IO.Path]::GetDirectoryName($deliveryPath) -ne $deliveriesPath -or [IO.Path]::GetFileName($deliveryPath) -ne $DeliveryName) {
    throw '交付目录越界，拒绝重建。'
}
if (Test-Path -LiteralPath $deliveriesPath) {
    if (((Get-Item -LiteralPath $deliveriesPath).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'deliveries 是链接，拒绝写入。' }
}
if (Test-Path -LiteralPath $deliveryPath) {
    $linkedItems = @((Get-Item -LiteralPath $deliveryPath)) + @(Get-ChildItem -LiteralPath $deliveryPath -Recurse -Force)
    if (@($linkedItems | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count -gt 0) { throw '交付目录包含链接，拒绝递归清理。' }
    Remove-Item -LiteralPath $deliveryPath -Recurse -Force
}
New-Item -ItemType Directory -Path $deliveryPath -Force | Out-Null
function Copy-DeliveryTree {
    param([string]$Source, [string]$Target)
    foreach ($item in Get-ChildItem -LiteralPath $Source -Force) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw "review 包含链接，无法保证独立运行：$($item.FullName)" }
        if ($item.PSIsContainer) {
            if ($item.Name -in @('.godot', '.import', '.git', 'godot-review', 'validation-logs', '__pycache__', 'cache', '.cache')) { continue }
            Copy-DeliveryTree $item.FullName (Join-Path $Target $item.Name)
        } elseif ($item.Extension -notin @('.import', '.log', '.tmp', '.pyc') -and $item.Name -ne 'file_hashes.json') {
            New-Item -ItemType Directory -Path $Target -Force | Out-Null
            Copy-Item -LiteralPath $item.FullName -Destination (Join-Path $Target $item.Name) -Force
        }
    }
}
Copy-DeliveryTree $reviewPath $deliveryPath
$deliveryProjectPath = Join-Path $deliveryPath 'project.godot'
$projectText = Get-Content -LiteralPath $deliveryProjectPath -Raw
$projectText = [regex]::Replace($projectText, '(?m)^config/name=.*$', 'config/name="Map Assets v001"')
$projectText = [regex]::Replace($projectText, '(?m)^run/main_scene=.*$', ('run/main_scene="res://' + $mainScene + '"'))
Set-Content -LiteralPath $deliveryProjectPath -Value $projectText -Encoding utf8 -NoNewline

$materialLines = @($catalog.materials | Sort-Object id | ForEach-Object { '- ' + $_.id + '：' + $_.name }) -join "`n"
$readme = @"
# 新地图素材 v001

这是完整独立 Godot 工程，建议 Godot 4.7.2。默认地图为潮汐物流港；另含干旱采矿站、废弃生态研究站。三张地图由实际 Floor / Bridge / FloorMaterials 和注册 Sprite2D 素材组成。

Windows 双击 **Start.cmd** 启动。若默认 Godot 路径不存在，在 PowerShell 执行：

``````powershell
.\run_showcase.ps1 -GodotPath 'D:\Godot\godot.exe' -Map tidal_port
.\run_showcase.ps1 -GodotPath 'D:\Godot\godot.exe' -Map dry_mine
.\run_showcase.ps1 -GodotPath 'D:\Godot\godot.exe' -Map overgrown_lab
``````

也可在 Godot 项目管理器导入本目录的 project.godot。首次启动需要导入资源，ZIP 不携带本机 .godot 缓存。

铺刷：1 地板、2 双格桥、3 单格桥；左键刷、右键擦；[ / ] 切换材质。4–9 / 0 对应前七种材质，F1–F6 对应后六种；Ctrl+Z/Y 撤销/重做，Ctrl+S/L 保存/载入布局。保存位于 Godot user://，不会改写本包源文件。

材质编号：

$materialLines

主要入口：

- scenes/ember/map_assets_tidal_port_v001.tscn
- scenes/ember/map_assets_dry_mine_v001.tscn
- scenes/ember/map_assets_overgrown_lab_v001.tscn
- assets/ember/map_assets_v001/：透明素材、Sprite2D 场景、地板与验收报告。
- art-source/ember/map-assets-v001/：规格、提示词与 $($masterPaths.Count) 份真实生成母稿。
- file_hashes.json：全包文件 SHA256 清单（不包含清单自身）。

世界格32，纹理格128，图层scale0.25；南向短立面、8world压顶、默认桥体40world。材质交界共享外轮廓结构。技术验收 PASS 证明已记录的结构与实际拼装检查，艺术效果仍以用户审阅为准。此包未包含新增碰撞、导航、动画或完整玩法。

运行 .\run_validation.ps1 -GodotPath 'D:\Godot\godot.exe' 可复验 Sprite / Floor 两项；历史基线资源是本包的可复用依赖。原始报告保留在素材目录，后续复验会更新对应报告。来源记录仅用于追溯；不以整张概念图作为可走地面。

已记录的技术检查：27 个 Sprite 注册；156 个材质交界、36 个桥口、21 次增量/全量 RGBA 比较、9 次撤销及 9 次重做。GPU 每图连续改刷 2 次，每次 3 个样点、合计 6 个样点，最大 RGB8 误差为 0。visual_review_v001.json 是针对本包最终截图的独立视觉检查，用户的艺术选择另记。
"@
Set-Content -LiteralPath (Join-Path $deliveryPath 'README.md') -Value $readme -Encoding utf8
$showcaseScript = @'
param(
    [string]$GodotPath = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe',
    [ValidateSet('tidal_port','dry_mine','overgrown_lab')][string]$Map = 'tidal_port'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $GodotPath -PathType Leaf)) { throw '请使用 -GodotPath 指定 Godot 4.7.2 可执行文件。' }
$logFolder = Join-Path $PSScriptRoot 'validation-logs'
New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
$stderr = Join-Path $logFolder 'showcase_import.stderr.log'
$task = Start-Process -FilePath $GodotPath -ArgumentList @('--headless','--import','--path',('"' + $PSScriptRoot + '"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logFolder 'showcase_import.stdout.log') -RedirectStandardError $stderr
if ($task.ExitCode -ne 0 -or (Select-String -LiteralPath $stderr -Pattern 'SCRIPT ERROR|ERROR:' -Quiet)) { throw '首次导入失败，请查看 validation-logs。' }
& $GodotPath --path $PSScriptRoot ('res://scenes/ember/map_assets_' + $Map + '_v001.tscn')
'@
Set-Content -LiteralPath (Join-Path $deliveryPath 'run_showcase.ps1') -Value $showcaseScript -Encoding utf8
$validationScript = @'
param([string]$GodotPath = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe')
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $GodotPath -PathType Leaf)) { throw '请使用 -GodotPath 指定 Godot 4.7.2 可执行文件。' }
$logFolder = Join-Path $PSScriptRoot 'validation-logs'
New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
foreach ($stage in @('import','sprites','floors')) {
    $arguments = @('--headless','--path',('"' + $PSScriptRoot + '"'))
    if ($stage -eq 'import') { $arguments += '--import' } else { $arguments += @('--script',('res://tools/validate_map_' + $stage + '_v001.gd')) }
    $stderr = Join-Path $logFolder ($stage + '.stderr.log')
    $task = Start-Process -FilePath $GodotPath -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logFolder ($stage + '.stdout.log')) -RedirectStandardError $stderr
    if ($task.ExitCode -ne 0 -or (Select-String -LiteralPath $stderr -Pattern 'SCRIPT ERROR|ERROR:' -Quiet)) { throw ($stage + ' 验证失败，请查看 validation-logs。') }
}
Write-Output 'MAP_ASSETS_LOCAL_VALIDATION_PASS'
'@
Set-Content -LiteralPath (Join-Path $deliveryPath 'run_validation.ps1') -Value $validationScript -Encoding utf8
Set-Content -LiteralPath (Join-Path $deliveryPath 'Start.cmd') -Encoding ascii -Value @'
@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_showcase.ps1" %*
if errorlevel 1 pause
'@

$hashEntries = @(Get-ChildItem -LiteralPath $deliveryPath -Recurse -File | Sort-Object FullName | ForEach-Object {
    @{path=[IO.Path]::GetRelativePath($deliveryPath,$_.FullName).Replace([char]92,[char]47); sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); bytes=$_.Length}
})
$manifest = @{revision='map_assets_v001'; files=$hashEntries; evidence_paths=$reportPaths; source_masters=$masterPaths.Count; registered_sprites=$registeredIds.Count}
Set-Content -LiteralPath (Join-Path $deliveryPath 'file_hashes.json') -Value ($manifest | ConvertTo-Json -Depth 6) -Encoding utf8
Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path -LiteralPath $pendingArchivePath) {
    if (((Get-Item -LiteralPath $pendingArchivePath).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw '临时 ZIP 是链接，拒绝覆盖。' }
    Remove-Item -LiteralPath $pendingArchivePath -Force
}
[IO.Compression.ZipFile]::CreateFromDirectory($deliveryPath, $pendingArchivePath, [IO.Compression.CompressionLevel]::Optimal, $false)
# ZIP 内部逐项核验，包含 file_hashes.json 自身；不只检查顶层 ZIP 哈希。
$expectedZipFiles = @{}
foreach ($entry in $hashEntries) { $expectedZipFiles[$entry.path] = $entry }
$manifestPath = Join-Path $deliveryPath 'file_hashes.json'
$expectedZipFiles['file_hashes.json'] = @{bytes=(Get-Item -LiteralPath $manifestPath).Length; sha256=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$archive = [IO.Compression.ZipFile]::OpenRead($pendingArchivePath)
try {
    $seen = @{}
    foreach ($entry in $archive.Entries) {
        if ($entry.Name.Length -eq 0) { continue }
        $name = $entry.FullName.Replace('\','/')
        if ($seen.ContainsKey($name) -or -not $expectedZipFiles.ContainsKey($name)) { throw "ZIP 出现额外或重复项：$name" }
        $seen[$name] = $true
        $expected = $expectedZipFiles[$name]
        if ($entry.Length -ne $expected.bytes) { throw "ZIP 字节数不符：$name" }
        $stream = $entry.Open()
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $actual = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose(); $stream.Dispose() }
        if ($actual -ne $expected.sha256) { throw "ZIP SHA256 不符：$name" }
    }
    if ($seen.Count -ne $expectedZipFiles.Count) { throw 'ZIP 缺少清单文件。' }
} finally { $archive.Dispose() }
if (Test-Path -LiteralPath $archivePath) {
    if (((Get-Item -LiteralPath $archivePath).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw '最终 ZIP 是链接，拒绝覆盖。' }
}
Move-Item -LiteralPath $pendingArchivePath -Destination $archivePath -Force
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
$packageReport = @{revision='map_assets_v001'; status='PASS'; delivery=$deliveryPath; archive=$archivePath; archive_sha256=$archiveHash; files=$expectedZipFiles.Count; manifest_sha256=$expectedZipFiles['file_hashes.json'].sha256; zip_entries_verified=$seen.Count; cold_start_validation='NOT_RUN_BY_PACKAGER'}
Set-Content -LiteralPath (Join-Path $workspacePath 'art-source/ember/map-assets-v001/package_validation_v001.json') -Value ($packageReport | ConvertTo-Json -Depth 5) -Encoding utf8
Write-Output "DELIVERY_SAVED: $deliveryPath"
Write-Output "ARCHIVE_SAVED: $archivePath"
Write-Output "FILES: $($expectedZipFiles.Count); ARCHIVE_SHA256: $archiveHash"
