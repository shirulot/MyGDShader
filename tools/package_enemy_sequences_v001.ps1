#requires -Version 7.0
<#
四款敌人正向五动作的完整 TA 审阅候选包，定位 PLAYABLE_VISUAL_SAMPLES / TA_REVIEW。
先核对规格、来源及实际播放证据，再复制精确选中的文件；不生成或修改美术。
-CheckOnly 不写入交付目录。资料未齐时停止，不产出残缺 ZIP。
技术闸门通过不会覆盖美术需修订结论，不将本包标为正式生产可用。
#>
[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,90}$')]
    [string]$DeliveryName = 'enemy_sequences_v001_2026-10-06',
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$workspacePath = [IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd([char[]]@('\', '/'))
$sourceRelative = 'art-source/ember/enemy-sequences-v001'
$assetRelative = 'assets/ember/characters/enemies_v001'
$sourcePath = Join-Path $workspacePath $sourceRelative
$assetPath = Join-Path $workspacePath $assetRelative
$specPath = Join-Path $sourcePath 'sequence_specs_v001.json'
$standardRelative = 'docs/shader-learning/ember-enemy-animation-standard-v001.md'
$taStandardRelative = 'docs/shader-learning/ta-art-review-standard-v001.md'
$selectedFiles = [ordered]@{}
$missingFiles = [Collections.Generic.List[string]]::new()

function Read-Json {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "缺少文件：$Path" }
    return Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json -Depth 100
}

function Get-Field {
    param($Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -ne $property) { return $property.Value }
    return $null
}

$specs = Read-Json $specPath
# 绝对路径是来源记录的一部分；重打包时将原工作区前缀重定位到当前工作区。
$originalSource = [string]$specs.source_directory
$originalWorkspace = [IO.Path]::GetFullPath((Join-Path $originalSource '../../..')).TrimEnd([char[]]@('\', '/'))

function Resolve-WorkspaceFile {
    param([string]$Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { throw '规格或报告引用了空路径。' }
    $normalized = $Path.Replace('/', [IO.Path]::DirectorySeparatorChar)
    if ($Path.StartsWith('res://')) {
        $absolute = Join-Path $workspacePath $Path.Substring(6)
    } elseif ([IO.Path]::IsPathRooted($normalized)) {
        $oldPrefix = $originalWorkspace + [IO.Path]::DirectorySeparatorChar
        if ($normalized.StartsWith($oldPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            $absolute = Join-Path $workspacePath $normalized.Substring($oldPrefix.Length)
        } else {
            $absolute = $normalized
        }
    } else {
        $absolute = Join-Path $workspacePath $normalized
    }
    $absolute = [IO.Path]::GetFullPath($absolute)
    $prefix = $workspacePath + [IO.Path]::DirectorySeparatorChar
    if (-not $absolute.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "文件超出工作区，拒绝收集：$absolute"
    }
    return $absolute
}

function Assert-NoLink {
    param([string]$Path)
    # 包括父级目录，防止路径名在工作区中而真实目标在工作区之外。
    $cursor = $Path
    while ($cursor -and $cursor -ne $workspacePath) {
        if (Test-Path -LiteralPath $cursor) {
            if (((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "路径包含链接，无法保证独立交付：$cursor"
            }
        }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
}

function Add-DeliveryFile {
    param([string]$Path, [string]$Destination = '')
    $absolute = Resolve-WorkspaceFile $Path
    if (-not (Test-Path -LiteralPath $absolute -PathType Leaf)) {
        $missingFiles.Add($absolute)
        return
    }
    Assert-NoLink $absolute
    if ([string]::IsNullOrEmpty($Destination)) {
        $Destination = [IO.Path]::GetRelativePath($workspacePath, $absolute).Replace('\', '/')
    }
    $Destination = $Destination.Replace('\', '/')
    if ($Destination.StartsWith('/') -or $Destination.Split('/') -contains '..' -or $Destination -match '(^|/)\.(godot|git|import|logs)(/|$)' -or $Destination -match '\.(import|zip|log|tmp|pyc)$' -or [IO.Path]::GetFileName($Destination) -eq 'preview_server.json') {
        throw "不允许的交付路径：$Destination"
    }
    if ($selectedFiles.Contains($Destination) -and $selectedFiles[$Destination] -ne $absolute) {
        throw "交付路径发生冲突：$Destination"
    }
    $selectedFiles[$Destination] = $absolute
}

function Assert-Hash {
    param([string]$Path, [string]$Expected, [string]$Label)
    $absolute = Resolve-WorkspaceFile $Path
    if (-not (Test-Path -LiteralPath $absolute -PathType Leaf)) { throw "$Label 缺少文件：$absolute" }
    if ($Expected -notmatch '^[0-9a-fA-F]{64}$') { throw "$Label 缺少有效 SHA256。" }
    $actual = (Get-FileHash -LiteralPath $absolute -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Expected.ToLowerInvariant()) { throw "$Label 已改变，需要重新验证：$absolute" }
    return $actual
}

function Assert-PassReport {
    param($Report, [string]$Name, [string]$StatusField = 'status')
    # PowerShell 函数会展开空数组为 $null；先滤掉 null，不能把合法 [] 误判为失败。
    if ((Get-Field $Report $StatusField) -ne 'PASS' -or @((Get-Field $Report 'failures') | Where-Object { $null -ne $_ }).Count -gt 0) {
        throw "$Name 报告尚未完整 PASS。"
    }
}

# 这批固定是四款 × 五动作 × down，不接受部分导出被误当成完整包。
$expectedClips = @($specs.clips)
if (@($specs.units).Count -ne 4 -or $expectedClips.Count -ne 20 -or ($expectedClips | Measure-Object frame_count -Sum).Sum -ne 120) {
    throw '本批规格必须为 4 款、20 条序列、120 帧。'
}
if ((@($specs.canvas_px) -join ',') -ne '128,128' -or (@($specs.pivot_px) -join ',') -ne '64,104') {
    throw '画布或锚点与本批 128×128 / (64,104) 规范不一致。'
}
if (@($expectedClips | Where-Object direction -ne 'down').Count -ne 0) { throw '本包仅包含 down 正向首批。' }

Add-DeliveryFile $specPath
Add-DeliveryFile (Join-Path $sourcePath 'README.md')
Add-DeliveryFile $standardRelative
Add-DeliveryFile $taStandardRelative
Add-DeliveryFile 'tools/export_enemy_sequences_v001.gd'
Add-DeliveryFile 'tools/build_enemy_sequence_preview_v001.gd'
Add-DeliveryFile 'tools/package_enemy_sequences_v001.ps1'

# 只收规格当前选中的母稿，不递归复制 masters，旧 v001 替换稿不会混入。
foreach ($clip in $expectedClips) {
    Add-DeliveryFile ([string]$clip.master_path)
    Add-DeliveryFile ([string]$clip.prompt_path)
    Add-DeliveryFile ([string]$clip.template_path)
    $generationPath = [IO.Path]::ChangeExtension((Resolve-WorkspaceFile ([string]$clip.master_path)), '.generation.json')
    Add-DeliveryFile $generationPath
    if (Test-Path -LiteralPath $generationPath -PathType Leaf) {
        $generation = Read-Json $generationPath
        $revisionPrompt = [string](Get-Field $generation 'prompt_path')
        if (-not [string]::IsNullOrEmpty($revisionPrompt)) { Add-DeliveryFile $revisionPrompt }
    }
}
foreach ($unit in @($specs.units)) {
    foreach ($field in @('reference_master', 'reference_three_views', 'reference_parts', 'reference_scale_example')) {
        Add-DeliveryFile ([string](Get-Field $unit $field))
    }
    Add-DeliveryFile (Join-Path $sourcePath ('templates/' + $unit.id + '_canonical_down_v001.png'))
}

$catalogPath = Join-Path $assetPath 'sequence_catalog_v001.json'
$requiredQa = @('sequence_export_v001.json', 'sequence_resource_validation_v001.json', 'sequence_preview_assembly_v001.json', 'sequence_gpu_playback_v001.json', 'sequence_frame_contacts_v001.json', 'visual_art_review_v001.json')
Add-DeliveryFile $catalogPath
foreach ($name in $requiredQa) { Add-DeliveryFile (Join-Path $sourcePath ('qa/' + $name)) }
$htmlPath = Join-Path $sourcePath 'previews/enemy_sequences_player_v001.html'
Add-DeliveryFile $htmlPath
Add-DeliveryFile (Join-Path $sourcePath 'preview-project/project.godot') 'project.godot'
Add-DeliveryFile (Join-Path $sourcePath 'preview-project/enemy_preview_controller.gd') 'enemy_preview_controller.gd'
Add-DeliveryFile (Join-Path $sourcePath 'preview-project/scenes/enemy_sequences_review_v001.tscn') 'scenes/enemy_sequences_review_v001.tscn'
Add-DeliveryFile (Join-Path $sourcePath 'preview-project/prepare_templates.gd')
Add-DeliveryFile (Join-Path $assetPath 'previews/enemy_sequences_contact_sheet_v001.png')

if ($missingFiles.Count -gt 0) {
    throw ("批次尚未完整，不打包。缺少 $($missingFiles.Count) 项：`n" + ($missingFiles -join "`n"))
}

$catalog = Read-Json $catalogPath
Assert-PassReport $catalog '总目录' 'technical_status'
if (-not $catalog.batch_complete -or @($catalog.clips).Count -ne 20 -or @($catalog.unit_resources).Count -ne 4) {
    throw '导出总目录不是完整的四款二十动作。'
}
Assert-Hash $specPath ([string]$catalog.source_specs_sha256) '已验收规格' | Out-Null
Assert-Hash 'tools/export_enemy_sequences_v001.gd' ([string]$catalog.tool_sha256) '已验收导出工具' | Out-Null
$exportReport = Read-Json (Join-Path $sourcePath 'qa/sequence_export_v001.json')
Assert-PassReport $exportReport '导出报告' 'technical_status'
if ((Get-FileHash -LiteralPath $catalogPath -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath (Join-Path $sourcePath 'qa/sequence_export_v001.json') -Algorithm SHA256).Hash) {
    throw '资产总目录与最终导出报告不一致。'
}
$catalogById = @{}
$frameTotal = 0
foreach ($entry in @($catalog.clips)) {
    if ($catalogById.ContainsKey([string]$entry.id)) { throw "重复序列 ID：$($entry.id)" }
    $catalogById[[string]$entry.id] = $entry
}
foreach ($clip in $expectedClips) {
    if (-not $catalogById.ContainsKey([string]$clip.id)) { throw "导出总目录缺少动作：$($clip.id)" }
    $entry = $catalogById[[string]$clip.id]
    Assert-PassReport $entry ([string]$clip.id) 'technical_status'
    foreach ($field in @('unit_id', 'action', 'direction', 'frame_count', 'columns', 'rows', 'fps', 'loop')) {
        if ((Get-Field $entry $field) -ne (Get-Field $clip $field)) { throw "$($clip.id) 的 $field 与规格不一致。" }
    }
    if ((@($entry.canvas_px) -join ',') -ne '128,128' -or (@($entry.pivot_px) -join ',') -ne '64,104') { throw "固定画布或锚点错误：$($clip.id)" }
    if ((Get-Field $entry 'registration_status') -ne 'EXPLICIT_CLIP_COMMON_TRANSFORM' -or $null -eq (Get-Field $clip 'registration')) {
        throw "动作缺少明确共同注册：$($clip.id)"
    }
    Assert-Hash ([string]$clip.master_path) ([string]$entry.source_sha256) ($clip.id + ' 母稿') | Out-Null
    if ((Resolve-WorkspaceFile ([string]$entry.source_master)) -ne (Resolve-WorkspaceFile ([string]$clip.master_path))) { throw "验收来源不是当前选中的母稿：$($clip.id)" }
    Assert-Hash ([string]$entry.atlas) ([string]$entry.atlas_sha256) ($clip.id + ' 图集') | Out-Null
    Add-DeliveryFile ([string]$entry.atlas)
    Add-DeliveryFile (Join-Path $assetPath ($clip.unit_id + '/' + $clip.action + '_down_metadata_v001.json'))
    if (@($entry.frames).Count -ne [int]$clip.frame_count -or @($entry.frame_metrics).Count -ne [int]$clip.frame_count) { throw "逐帧记录数量错误：$($clip.id)" }
    for ($index = 0; $index -lt [int]$clip.frame_count; $index++) {
        $frame = $entry.frames[$index]
        if ([int]$frame.frame -ne $index) { throw "帧顺序错误：$($clip.id) f$index" }
        $expectedFramePath = Join-Path $assetPath ($clip.unit_id + '/frames/' + $clip.action + '_down/' + ('f{0:d2}.png' -f $index))
        if ((Resolve-WorkspaceFile ([string]$frame.path)) -ne [IO.Path]::GetFullPath($expectedFramePath)) { throw "逐帧路径不一致：$($clip.id) f$index" }
        Assert-Hash ([string]$frame.path) ([string]$frame.sha256) ($clip.id + ' f' + $index) | Out-Null
        Add-DeliveryFile ([string]$frame.path)
        $frameTotal++
    }
}
if ($frameTotal -ne 120) { throw '最终目录必须包含 120 帧。' }
foreach ($unit in @($catalog.unit_resources)) {
    if ([int]$unit.animation_count -ne 5) { throw "单位资源不是完整五动作：$($unit.unit_id)" }
    Assert-Hash ([string]$unit.sprite_frames) ([string]$unit.sprite_frames_sha256) ($unit.unit_id + ' SpriteFrames') | Out-Null
    Assert-Hash ([string]$unit.scene) ([string]$unit.scene_sha256) ($unit.unit_id + ' AnimatedSprite2D') | Out-Null
    Add-DeliveryFile ([string]$unit.sprite_frames)
    Add-DeliveryFile ([string]$unit.scene)
}

$resourceReport = Read-Json (Join-Path $sourcePath 'qa/sequence_resource_validation_v001.json')
$assemblyReport = Read-Json (Join-Path $sourcePath 'qa/sequence_preview_assembly_v001.json')
$gpuReport = Read-Json (Join-Path $sourcePath 'qa/sequence_gpu_playback_v001.json')
Assert-PassReport $resourceReport 'Godot 资源'
Assert-PassReport $assemblyReport '独立预览装配'
Assert-PassReport $gpuReport '实际 GPU 播放'
if (@($resourceReport.records).Count -ne 20 -or [int]$assemblyReport.clips_available -ne 20) { throw '预览报告尚未覆盖完整二十动作。' }
foreach ($record in @($resourceReport.records)) {
    if (-not $catalogById.ContainsKey([string]$record.clip_id)) { throw "资源报告出现未知动作：$($record.clip_id)" }
    $entry = $catalogById[[string]$record.clip_id]
    if ($record.animation -ne $entry.animation -or [int]$record.frames -ne [int]$entry.frame_count -or $record.fps -ne $entry.fps -or $record.loop -ne $entry.loop) { throw "资源报告与目录不一致：$($record.clip_id)" }
}
$playbackRecords = @($gpuReport.playback_records.PSObject.Properties)
if ($playbackRecords.Count -ne 20 -or $gpuReport.resource_validation_status -ne 'PASS' -or @($gpuReport.captures).Count -eq 0) { throw '实际播放报告尚未覆盖完整二十动作。' }
foreach ($property in $playbackRecords) {
    if (-not $catalogById.ContainsKey([string]$property.Name)) { throw "播放报告出现未知动作：$($property.Name)" }
    $entry = $catalogById[[string]$property.Name]
    $record = $property.Value
    if (@($record.frames_seen | Sort-Object -Unique).Count -ne [int]$entry.frame_count) { throw "实际播放没有遍历全部帧：$($entry.id)" }
    if ($entry.loop -and [int]$record.looped_count -lt 1) { throw "循环动作未实际循环：$($entry.id)" }
    if (-not $entry.loop -and [int]$record.finished_count -lt 1) { throw "单次动作未实际结束：$($entry.id)" }
}
foreach ($capture in @($gpuReport.captures)) {
    Assert-Hash ([string]$capture.png) ([string]$capture.sha256) 'GPU 截图' | Out-Null
    Add-DeliveryFile ([string]$capture.png)
}

# TA 审阅与技术 PASS 分开。视觉报告可以 NEEDS_REVISION，但必须针对当前固定版本。
$visualReportPath = Join-Path $sourcePath 'qa/visual_art_review_v001.json'
$visualReport = Read-Json $visualReportPath
$visualStatus = [string](Get-Field $visualReport 'status')
if ([string]::IsNullOrWhiteSpace($visualStatus)) { throw '视觉审阅报告缺少明确 status，不能用技术 PASS 代替。' }
$fixedReviewBatch = Get-Field $visualReport 'fixed_review_batch'
Assert-Hash $catalogPath ([string](Get-Field $fixedReviewBatch 'catalog_sha256')) '视觉审阅目录版本' | Out-Null
Assert-Hash $specPath ([string](Get-Field $fixedReviewBatch 'spec_sha256')) '视觉审阅规格版本' | Out-Null

# 全帧 1x/4x 联系图必须来自当前目录，覆盖全部120帧，不能只交首帧或静态拼图。
$contactReportPath = Join-Path $sourcePath 'qa/sequence_frame_contacts_v001.json'
$contactReport = Read-Json $contactReportPath
Assert-PassReport $contactReport '全帧联系图'
Assert-Hash $catalogPath ([string]$contactReport.catalog_sha256) '全帧联系图目录版本' | Out-Null
if ([int]$contactReport.exact_rgba_identity_checks -ne 120 -or @($contactReport.sheets).Count -ne 4 -or [int]$contactReport.magnification -ne 4 -or (@($contactReport.native_cell_px) -join ',') -ne '128,128') {
    throw '全帧联系图尚未覆盖四款120帧或放大参数不正确。'
}
$contactUnits = @{}
foreach ($sheet in @($contactReport.sheets)) {
    if ($contactUnits.ContainsKey([string]$sheet.unit_id) -or @($sheet.cells).Count -ne 30) { throw "全帧联系图重复或缺帧：$($sheet.unit_id)" }
    $contactUnits[[string]$sheet.unit_id] = $true
    Assert-Hash ([string]$sheet.native) ([string]$sheet.native_sha256) ($sheet.unit_id + ' 1x 全帧图') | Out-Null
    Assert-Hash ([string]$sheet.nearest_x4) ([string]$sheet.nearest_x4_sha256) ($sheet.unit_id + ' 4x 全帧图') | Out-Null
    Add-DeliveryFile ([string]$sheet.native)
    Add-DeliveryFile ([string]$sheet.nearest_x4)
    $seenCells = @{}
    foreach ($cell in @($sheet.cells)) {
        if (-not $catalogById.ContainsKey([string]$cell.clip_id)) { throw "联系图出现未知动作：$($cell.clip_id)" }
        $entry = $catalogById[[string]$cell.clip_id]
        $key = [string]$cell.clip_id + ':' + [string]$cell.frame
        if ($seenCells.ContainsKey($key) -or $entry.unit_id -ne $sheet.unit_id -or [int]$cell.frame -lt 0 -or [int]$cell.frame -ge [int]$entry.frame_count -or $cell.source_atlas_sha256 -ne $entry.atlas_sha256) { throw "联系图格引用或来源不一致：$key" }
        $seenCells[$key] = $true
    }
}
foreach ($unit in @($specs.units)) {
    if (-not $contactUnits.ContainsKey([string]$unit.id)) { throw "联系图缺少单位：$($unit.id)" }
}
Add-DeliveryFile ([string]$contactReport.patrol_move_strip_native)
Add-DeliveryFile ([string]$contactReport.patrol_move_strip_x4)
Add-DeliveryFile (Join-Path $assetPath 'previews/sequence_frame_contacts_v001.json')
Add-DeliveryFile (Join-Path $assetPath 'previews/sequence_gpu_playback_v001.json')

# 自包含 HTML 必须内嵌当前的二十个已验收图集，而非链接本机绝对路径。
$html = Get-Content -LiteralPath $htmlPath -Raw
$embeddedMatch = [regex]::Match($html, '(?s)const\s+clips\s*=\s*(\[.*?\])\s*;\s*const\s+labels\s*=')
if (-not $embeddedMatch.Success) { throw '无法读取 HTML 播放器的内嵌动作清单。' }
$embedded = @($embeddedMatch.Groups[1].Value | ConvertFrom-Json -Depth 100)
if ($embedded.Count -ne 20 -or @($embedded.id | Sort-Object -Unique).Count -ne 20) { throw 'HTML 播放器不是完整二十动作。' }
foreach ($item in $embedded) {
    if (-not $catalogById.ContainsKey([string]$item.id) -or -not ([string]$item.image_data).StartsWith('data:image/png;base64,')) { throw "HTML 动作或内嵌图像无效：$($item.id)" }
    $bytes = [Convert]::FromBase64String(([string]$item.image_data).Substring('data:image/png;base64,'.Length))
    $embeddedHash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
    if ($embeddedHash -ne [string]$catalogById[[string]$item.id].atlas_sha256) { throw "HTML 图集不是当前验收版本：$($item.id)" }
}

# 收录诊断与最终 QA；旧包的 package report 会在本次打包后重新写，不能混入。
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $sourcePath 'qa') -Recurse -File) {
    if ($file.Extension -in @('.json', '.md', '.png') -and $file.Name -notin @('package_validation_v001.json', 'preview_server.json')) { Add-DeliveryFile $file.FullName }
}
if ($missingFiles.Count -gt 0) { throw ("缺少交付文件：`n" + ($missingFiles -join "`n")) }
Write-Output "ENEMY_PACKAGE_GATES_PASS: TA_REVIEW; 20 clips; $frameTotal frames; 4 SpriteFrames; 4 sample scenes; $($selectedFiles.Count) selected files; visual_status=$visualStatus; production_ready=false"
if ($CheckOnly) { return }

$deliveriesPath = [IO.Path]::GetFullPath((Join-Path $workspacePath 'art-source/ember/deliveries'))
$deliveryPath = [IO.Path]::GetFullPath((Join-Path $deliveriesPath $DeliveryName))
$archivePath = [IO.Path]::GetFullPath((Join-Path $deliveriesPath ($DeliveryName + '.zip')))
if ([IO.Path]::GetDirectoryName($deliveryPath) -ne $deliveriesPath -or [IO.Path]::GetFileName($deliveryPath) -ne $DeliveryName) { throw '交付目录越界。' }
Assert-NoLink $deliveriesPath
if ((Test-Path -LiteralPath $deliveryPath) -or (Test-Path -LiteralPath $archivePath)) { throw '已有同名交付，指定新的 -DeliveryName；本工具不删除旧包。' }
New-Item -ItemType Directory -Path $deliveryPath -Force | Out-Null
foreach ($destination in $selectedFiles.Keys) {
    $target = Join-Path $deliveryPath $destination
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null
    Copy-Item -LiteralPath $selectedFiles[$destination] -Destination $target
}

# 包根采用独立预览工程的设置，并共享唯一一套候选导出资源；不重复复制 120 帧。
$packageProject = Join-Path $deliveryPath 'project.godot'
$projectText = Get-Content -LiteralPath $packageProject -Raw
$projectText = [regex]::Replace($projectText, '(?m)^run/main_scene=.*\r?\n?', '')
$projectText = [regex]::Replace($projectText, '(?m)^config/name=.*$', 'config/name="Ember enemy sequence samples"')
$projectText = $projectText.Replace('[application]', "[application]`nrun/main_scene=`"res://scenes/enemy_sequences_review_v001.tscn`"")
Set-Content -LiteralPath $packageProject -Value $projectText -Encoding utf8NoBOM -NoNewline
$rootReadme = @'
# Ember 敌人正向动作候选 · TA 审阅 v001

四款敌人 × 待机/移动/攻击/受击/死亡，共20条序列、120帧。所有帧128×128，锚点(64,104)，Nearest。交付定位PLAYABLE_VISUAL_SAMPLES / TA_REVIEW，仅供逐帧审阅与返修，不称正式生产可用。本包没有敌人AI、碰撞或伤害逻辑。

浏览器离线播放：打开 `art-source/ember/enemy-sequences-v001/previews/enemy_sequences_player_v001.html`。

Godot：导入本目录 `project.godot` 直接运行；或 PowerShell 执行 `./run_preview.ps1 -GodotPath 'D:\Godot\godot.exe'`。建议使用Godot4.7.2。空格暂停/继续，R重播，Esc关闭。

攻击、受击、死亡资源不循环，预览控制器在结尾停留后重播；死亡末帧展示停留1.25秒。所有原始母稿RGBA均保留，只做共同注册的固定网格切图与最近邻缩放，不逐帧居中。

实体像素正式标准为二值Alpha；本候选保留连续Alpha，相关美术返修由视觉审阅报告明确登记。技术播放与包完整性通过不等于TA放行。全帧1x/4x联系图和巡逻兵移动条带位于 `assets/ember/characters/enemies_v001/previews/`，四款各五动作，先审巡逻兵移动循环。

视觉报告：`art-source/ember/enemy-sequences-v001/qa/visual_art_review_v001.json`；TA规范：`docs/shader-learning/ta-art-review-standard-v001.md`。root、安装侧、挂接、叶形、死亡落地等问题以绑定本版本哈希的报告为准。

完整参数、文件说明、生产规范和后续四向范围：[制作说明](art-source/ember/enemy-sequences-v001/README.md)。原始工作区路径与工具临时路径保留在来源记录中用于追溯，播放入口不依赖这些路径。

资源入口：`assets/ember/characters/enemies_v001/sequence_catalog_v001.json`；每款包含SpriteFrames、AnimatedSprite2D场景、5个图集和30个独立帧。`file_hashes.json` 是全包文件SHA256清单，不含清单自身。

ZIP不含`.godot`和`.import`缓存、旧版替换母稿或另一个ZIP；首次导入由Godot在本包内建立缓存。
'@
$rootReadme += "`n当前视觉审阅状态：$visualStatus；交付阶段：TA_REVIEW；production_ready=false。`n"
Set-Content -LiteralPath (Join-Path $deliveryPath 'README.md') -Value $rootReadme -Encoding utf8NoBOM
$launcher = @'
param([string]$GodotPath = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe')
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $GodotPath -PathType Leaf)) { throw '请使用 -GodotPath 指定 Godot 4.7.2 可执行文件。' }
$logPath = Join-Path $PSScriptRoot 'validation-logs'
New-Item -ItemType Directory -Path $logPath -Force | Out-Null
$stderr = Join-Path $logPath 'preview_import.stderr.log'
$task = Start-Process -FilePath $GodotPath -ArgumentList @('--headless','--editor','--path',('"' + $PSScriptRoot + '"'),'--import','--quit') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logPath 'preview_import.stdout.log') -RedirectStandardError $stderr
if ($task.ExitCode -ne 0 -or (Select-String -LiteralPath $stderr -Pattern 'SCRIPT ERROR|ERROR:' -Quiet)) { throw '首次导入失败，请查看 validation-logs。' }
& $GodotPath --path $PSScriptRoot 'res://scenes/enemy_sequences_review_v001.tscn'
'@
# Start.cmd 使用系统 Windows PowerShell；BOM 让其正确读取中文错误提示。
Set-Content -LiteralPath (Join-Path $deliveryPath 'run_preview.ps1') -Value $launcher -Encoding utf8BOM
Set-Content -LiteralPath (Join-Path $deliveryPath 'Start.cmd') -Encoding ascii -Value @'
@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_preview.ps1" %*
if errorlevel 1 pause
'@

$hashEntries = @(Get-ChildItem -LiteralPath $deliveryPath -Recurse -File | Sort-Object FullName | ForEach-Object {
    @{path=[IO.Path]::GetRelativePath($deliveryPath, $_.FullName).Replace('\', '/'); sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); bytes=$_.Length}
})
$manifest = @{revision='enemy_sequences_v001'; delivery_kind='PLAYABLE_VISUAL_SAMPLES'; submission_stage='TA_REVIEW'; production_ready=$false; clips=20; frames=120; atlases=20; units=4; selected_masters=@($expectedClips | ForEach-Object { [IO.Path]::GetRelativePath($workspacePath, (Resolve-WorkspaceFile ([string]$_.master_path))).Replace('\','/') }); technical_status='PASS'; visual_acceptance=$visualStatus; visual_review_path=($sourceRelative + '/qa/visual_art_review_v001.json'); files=$hashEntries}
$manifestPath = Join-Path $deliveryPath 'file_hashes.json'
Set-Content -LiteralPath $manifestPath -Value ($manifest | ConvertTo-Json -Depth 8) -Encoding utf8NoBOM
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($deliveryPath, $archivePath, [IO.Compression.CompressionLevel]::Optimal, $false)

# ZIP解压流逐项核对清单，自身也另算SHA；同时检查额外、重复和缺失条目。
$expectedZip = @{}
foreach ($entry in $hashEntries) { $expectedZip[$entry.path] = $entry }
$expectedZip['file_hashes.json'] = @{bytes=(Get-Item -LiteralPath $manifestPath).Length; sha256=(Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$zip = [IO.Compression.ZipFile]::OpenRead($archivePath)
$seen = @{}
try {
    foreach ($entry in $zip.Entries) {
        if ($entry.Name.Length -eq 0) { continue }
        $name = $entry.FullName.Replace('\', '/')
        if ($seen.ContainsKey($name) -or -not $expectedZip.ContainsKey($name)) { throw "ZIP有额外或重复条目：$name" }
        $seen[$name] = $true
        $expected = $expectedZip[$name]
        if ($entry.Length -ne $expected.bytes) { throw "ZIP字节数不一致：$name" }
        $stream = $entry.Open()
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $actual = [Convert]::ToHexString($sha.ComputeHash($stream)).ToLowerInvariant() } finally { $sha.Dispose(); $stream.Dispose() }
        if ($actual -ne $expected.sha256) { throw "ZIP内容SHA256不一致：$name" }
    }
    if ($seen.Count -ne $expectedZip.Count) { throw 'ZIP缺少清单中的文件。' }
} finally { $zip.Dispose() }
$report = @{revision='enemy_sequences_v001'; status='PASS'; status_scope='PACKAGE_INTEGRITY'; delivery_kind='PLAYABLE_VISUAL_SAMPLES'; submission_stage='TA_REVIEW'; production_ready=$false; delivery=$deliveryPath; archive=$archivePath; archive_sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant(); zip_entries_verified=$seen.Count; source_masters=20; atlas_count=20; frame_count=120; sprite_frames_count=4; reusable_scene_count=4; source_rgba_modified=$false; cold_start_validation='NOT_RUN_BY_PACKAGER'; visual_acceptance=$visualStatus; failures=@()}
Set-Content -LiteralPath (Join-Path $sourcePath 'qa/package_validation_v001.json') -Value ($report | ConvertTo-Json -Depth 8) -Encoding utf8NoBOM
Write-Output "DELIVERY_SAVED: $deliveryPath"
Write-Output "ARCHIVE_SAVED: $archivePath"
Write-Output "ZIP_ENTRIES_VERIFIED: $($seen.Count); ARCHIVE_SHA256: $($report.archive_sha256)"
