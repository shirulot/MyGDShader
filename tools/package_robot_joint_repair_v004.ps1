# 机器人 v004 的独立交付：保留好帧原路径/字节，仅替换关节修复帧，逐文件验证 ZIP。
# 本脚本不导入主工程，不改旧素材；暂存使用独立临时目录，避免覆盖旧 review。
[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$EvidenceConfigPath = 'art-source/ember/robot-joint-repair-v004/package_evidence_v004.json',
    [string]$DeliveryName = 'robot_joint_repair_v004_2026-10-06',
    [switch]$CheckOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$taskWorkspace = (Resolve-Path -LiteralPath $WorkspaceRoot).Path.TrimEnd('\', '/')
$taskSource = 'art-source/ember/robot-joint-repair-v004'
$taskCatalogPath = 'assets/ember/characters/robot/robot_frames_catalog_v004.json'
$taskOldCatalogPath = 'assets/ember/characters/robot/robot_frames_catalog_v003.json'
$taskNativeManifestPath = $taskSource + '/frame_manifest_v004.json'
$taskScene = 'scenes/ember/robot_animation_sandbox_v004.tscn'
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

function Assert-SameAnimations {
    param($Current, $Original, [string]$Label)
    # 按字段比较，避免 JSON 属性顺序变化被误报为动作修改；frame_ids 顺序必须相同。
    if (@($Current).Count -ne 12 -or @($Original).Count -ne 12) { throw "$Label 必须有12段动作。" }
    $originalClips = @{}
    foreach ($clip in @($Original)) { $originalClips[[string]$clip.id] = $clip }
    foreach ($clip in @($Current)) {
        if (-not $originalClips.ContainsKey([string]$clip.id)) { throw "$Label 增加未知动作：$($clip.id)" }
        $old = $originalClips[[string]$clip.id]
        if ([string]$clip.direction -cne [string]$old.direction -or [string]$clip.state -cne [string]$old.state -or [double]$clip.fps -ne [double]$old.fps -or [bool]$clip.loop -ne [bool]$old.loop -or (@($clip.frame_ids) -join '|') -cne (@($old.frame_ids) -join '|')) { throw "$Label 改动动作方向、时序或帧序：$($clip.id)" }
    }
}

$taskCatalog = Get-Content -LiteralPath (Resolve-SourceFile $taskCatalogPath) -Raw | ConvertFrom-Json
if (@($taskCatalog.canvas).Count -ne 2 -or $taskCatalog.canvas[0] -ne 64 -or $taskCatalog.canvas[1] -ne 96) { throw '机器人画布必须为 64×96。' }
if (@($taskCatalog.anchor).Count -ne 2 -or $taskCatalog.anchor[0] -ne 32 -or $taskCatalog.anchor[1] -ne 80) { throw '机器人脚底锚点必须为 (32,80)。' }
if (@($taskCatalog.frames).Count -ne 40 -or @($taskCatalog.animations).Count -ne 12) { throw 'v004 必须包含原来的 40 张原生帧与 12 段动作。' }
$taskOldCatalog = Get-Content -LiteralPath (Resolve-SourceFile $taskOldCatalogPath) -Raw | ConvertFrom-Json
$taskNativeManifest = Get-Content -LiteralPath (Resolve-SourceFile $taskNativeManifestPath) -Raw | ConvertFrom-Json
$taskProtectedBeforePath = $taskSource + '/protected_sources_before_v004.json'
$taskProtectedBefore = Get-Content -LiteralPath (Resolve-SourceFile $taskProtectedBeforePath) -Raw | ConvertFrom-Json
if (@($taskProtectedBefore.files).Count -lt 40) { throw '修复开始前必须冻结旧角色资源和工程文件，不能只在结尾声称旧文件未改。' }
foreach ($entry in $taskProtectedBefore.files) {
    $path = Get-Field $entry 'file'
    if ($null -eq $path) { $path = Get-Field $entry 'path' }
    Assert-SourceHash ([string]$path) ([string]$entry.sha256) | Out-Null
}
Add-SourceFile $taskProtectedBeforePath
if ($taskNativeManifest.status -ne 'PASS' -or ($null -ne (Get-Field $taskNativeManifest 'errors') -and @(Get-Field $taskNativeManifest 'errors').Count -ne 0) -or @($taskNativeManifest.frames).Count -ne 40) { throw '完整40帧修复 manifest 未通过。' }
Assert-SameAnimations $taskCatalog.animations $taskOldCatalog.animations 'v004目录'
Assert-SameAnimations $taskNativeManifest.animations $taskOldCatalog.animations '原生修复manifest'
$taskOldFrames = @{}
$taskManifestFrames = @{}
foreach ($frame in $taskOldCatalog.frames) {
    $taskOldFrames[[string]$frame.id] = $frame
    # 包内保留修复前PNG，既能重现修复对照，也让只读 runtime 验证真正检查旧基准。
    Assert-SourceHash ([string]$frame.file) ([string]$frame.sha256) | Out-Null
    Add-SourceFile ([string]$frame.file)
}
foreach ($frame in $taskNativeManifest.frames) {
    if ($taskManifestFrames.ContainsKey([string]$frame.id)) { throw "修复 manifest 重复 ID：$($frame.id)" }
    $taskManifestFrames[[string]$frame.id] = $frame
}
if ($taskOldFrames.Count -ne 40 -or $taskManifestFrames.Count -ne 40) { throw '基准目录和修复 manifest 必须各有40个唯一姿态。' }
$taskFrameIds = @{}
$taskFramePaths = @{}
$taskChangedCount = 0
$taskPreservedCount = 0
$taskPreservation = @()
foreach ($frame in $taskCatalog.frames) {
    if ($taskFrameIds.ContainsKey([string]$frame.id)) { throw "重复帧 ID：$($frame.id)" }
    $path = Get-RelativePath ([string]$frame.file)
    if ($taskFramePaths.ContainsKey($path)) { throw "目录帧重复引用同一 PNG：$path" }
    if (-not $path.EndsWith('.png')) { throw "帧文件必须为 PNG：$path" }
    $taskFrameIds[[string]$frame.id] = $frame
    $taskFramePaths[$path] = $true
    Assert-SourceHash $path ([string]$frame.sha256) | Out-Null
    Add-SourceFile $path
    $id = [string]$frame.id
    if (-not $taskOldFrames.ContainsKey($id) -or -not $taskManifestFrames.ContainsKey($id)) { throw "v004 帧不属于原有40姿态：$id" }
    $old = $taskOldFrames[$id]
    $native = $taskManifestFrames[$id]
    if ([string](Get-Field $native 'original_file') -cne [string]$old.file -or [string](Get-Field $native 'original_sha256') -cne [string]$old.sha256) { throw "原始帧来源缺失或不匹配：$id" }
    if ([string]$native.file -cne [string]$frame.file -or [string]$native.sha256 -cne [string]$frame.sha256) { throw "修复 manifest 与实际目录帧不匹配：$id" }
    $changed = [string]$frame.sha256 -cne [string]$old.sha256
    if ($null -eq (Get-Field $native 'changed') -or [bool]$native.changed -ne $changed) { throw "changed 标记与原 PNG SHA 不一致：$id" }
    if ([bool]$frame.joint_repair_changed -ne $changed -or [bool]$frame.preserved_v003_source -eq $changed) { throw "目录的保留/修复标记不一致：$id" }
    if ($changed) {
        if (-not $path.StartsWith('assets/ember/characters/robot/repairs_v004/')) { throw "修复必须写入新版本目录：$id" }
        $taskChangedCount++
    } else {
        if ([string]$frame.file -cne [string]$old.file) { throw "无断裂帧必须保留原文件路径：$id" }
        $taskPreservedCount++
    }
    $taskPreservation += @{id=$id; changed=$changed; original_file=$old.file; original_sha256=$old.sha256; file=$frame.file; sha256=$frame.sha256}
    foreach ($sourcePair in @(@('pose_file','pose_sha256'), @('source_rig','source_rig_sha256'))) {
        $sourcePath = Get-Field $frame $sourcePair[0]
        if ($null -ne $sourcePath) {
            Assert-SourceHash ([string]$sourcePath) ([string](Get-Field $frame $sourcePair[1])) | Out-Null
            Add-SourceFile ([string]$sourcePath)
        }
    }
}
if ($taskChangedCount -le 0 -or $taskPreservedCount -le 0 -or $taskChangedCount + $taskPreservedCount -ne 40) { throw '本轮须同时保留无断裂原帧和写出有问题的修复帧。' }
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
    $taskOldCatalogPath,
    $taskNativeManifestPath,
    'assets/ember/characters/robot/robot_sprite_frames_v004.tres',
    'scripts/ember/robot_action_preview_v004.gd',
    $taskScene,
    'tools/build_robot_animation_v004.gd',
    'tools/package_robot_joint_repair_v004.ps1',
    'tools/validate_robot_joint_repair_package_v004.ps1',
    'docs/shader-learning/robot-joint-repair-v004.md'
)) { Add-SourceFile $path }

# 可编辑旧 rig、步行标注和v003新动作标注是修复来源；只复制 JSON，不夹带旧预览或生成母稿。
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $taskWorkspace 'art-source/ember/robot-repair-v002/annotations') -Filter '*.json' -File) { Add-SourceFile $file.FullName }
foreach ($file in Get-ChildItem -LiteralPath (Join-Path $taskWorkspace 'art-source/ember/robot-actions-v003/poses') -Filter '*.json' -File) { Add-SourceFile $file.FullName }

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
foreach ($id in @('manifest','repair','runtime','gpu','visual','encoding')) {
    if (-not $taskReports.ContainsKey($id)) { throw "缺少最终证据：$id" }
}
# 原生报告记录实际RGBA差异和每个关节修改；好帧不能重新编码，坏帧不能仅更改PNG文件元数据。
$repair = $taskReports['repair']
Assert-SourceHash $taskNativeManifestPath ([string]$repair.source_manifest_sha256) | Out-Null
Assert-SourceHash $taskOldCatalogPath ([string]$repair.old_catalog_sha256) | Out-Null
Assert-SourceHash ($taskSource + '/joint_overlay_plan_v004.json') ([string]$repair.plan_sha256) | Out-Null
Assert-SourceHash 'tools/repair_robot_joints_v004.gd' ([string]$repair.repair_tool_sha256) | Out-Null
Add-SourceFile 'tools/repair_robot_joints_v004.gd'
Assert-SourceHash ([string]$taskNativeManifest.source_catalog) ([string]$taskNativeManifest.source_catalog_sha256) | Out-Null
Assert-SourceHash ([string]$taskNativeManifest.joint_overlay_plan) ([string]$taskNativeManifest.joint_overlay_plan_sha256) | Out-Null
# v003 目录整体作为原40帧基准保留。它的历史v002描述不是v004活动依赖，
# 不递归沿用该历史描述中的旧SHA；当前活动来源必须明确绑定source_catalog=v003。
if ([int]$repair.changed_count -ne $taskChangedCount -or [int]$repair.preserved_count -ne $taskPreservedCount -or @($repair.frames).Count -ne 40) { throw '原生修复报告的40帧/保留计数与目录不符。' }
$taskRepairIds = @{}
foreach ($item in $repair.frames) {
    $id = [string]$item.id
    if (-not $taskFrameIds.ContainsKey($id) -or $taskRepairIds.ContainsKey($id)) { throw "原生修复报告的帧ID未知或重复：$id" }
    $taskRepairIds[$id] = $true
    $current = $taskFrameIds[$id]
    $old = $taskOldFrames[$id]
    if ([string]$item.file -cne [string]$current.file -or [string]$item.sha256 -cne [string]$current.sha256 -or [string]$item.original_file -cne [string]$old.file -or [string]$item.original_sha256 -cne [string]$old.sha256 -or [bool]$item.changed -ne [bool]$current.joint_repair_changed) { throw "原生修复报告未绑定原/新PNG：$id" }
    if ([bool]$item.changed) {
        if ([int]$item.visible_rgba_changed -le 0 -or @($item.changed_pixels).Count -ne [int]$item.visible_rgba_changed -or @($item.edited_joints).Count -eq 0 -or @($item.patches).Count -eq 0 -or -not [bool]$item.outside_declared_pixels_unchanged -or -not [bool]$item.feet_unchanged -or -not [bool]$item.head_mask_unchanged -or -not [bool]$item.runtime_windows_unchanged -or -not [bool]$item.bbox_unchanged) { throw "修复超出关节范围或只有编码变化：$id" }
    } elseif ([int]$item.visible_rgba_changed -ne 0) { throw "标记保留的帧仍改动像素：$id" }
}
foreach ($id in @('runtime','gpu')) {
    if (-not $taskReports.ContainsKey($id)) { throw "缺少最终运行证据：$id" }
    $observed = $taskReports[$id].observed
    foreach ($dependencyPath in @($taskNativeManifestPath,$taskOldCatalogPath,$taskCatalogPath,[string]$taskCatalog.sheet.texture,'assets/ember/characters/robot/robot_sprite_frames_v004.tres',$taskScene,'scripts/ember/robot_action_preview_v004.gd','tools/build_robot_animation_v004.gd')) {
        $key = 'res://' + (Get-RelativePath $dependencyPath)
        Assert-SourceHash $dependencyPath ([string](Get-Field $taskReports[$id].dependencies_sha256 $key)) | Out-Null
    }
    # runtime_playback 是以场景节点路径为键的 JSON 对象；其值不是数组。
    # 数属性才能核对十二个独立 AnimatedSprite2D，而不是把整个对象误算成一项。
    $playbackCount = @($observed.runtime_playback.PSObject.Properties).Count
    if ($taskReports[$id].phase -ne 'verify' -or @($observed.source_frames).Count -ne 40 -or @($observed.resource_frames).Count -ne 40 -or $observed.atlas_regions_rgba_equal -ne 40 -or @($observed.clip_dependencies).Count -ne 12 -or $playbackCount -ne 12 -or @($observed.control_state_cases).Count -ne 4) { throw "运行证据没有覆盖完整 40 帧/12 动作/4 方向控制：$id" }
    if ([int]$observed.changed_pose_count -ne $taskChangedCount -or [int]$observed.preserved_pose_count -ne $taskPreservedCount) { throw "运行证据的保留/修复计数与原PNG不符：$id" }
    if (@($observed.original_v003_source_frames).Count -ne 40) { throw "运行证据没有核验全部40张修复前PNG：$id" }
    $originalIds = @{}
    foreach ($item in $observed.original_v003_source_frames) {
        if (-not $taskOldFrames.ContainsKey([string]$item.id) -or $originalIds.ContainsKey([string]$item.id)) { throw "运行证据的原帧ID未知或重复：$id / $($item.id)" }
        $old = $taskOldFrames[[string]$item.id]
        if ([string]$item.file -cne [string]$old.file -or [string]$item.sha256 -cne [string]$old.sha256 -or [string]$item.expected_sha256 -cne [string]$old.sha256 -or -not [bool]$item.unchanged) { throw "修复前原PNG未按SHA保留：$id / $($item.id)" }
        $originalIds[[string]$item.id] = $true
    }
    foreach ($item in $observed.source_frames) {
        if (-not $taskFrameIds.ContainsKey([string]$item.id)) { throw "运行证据含未知帧：$id / $($item.id)" }
        $frame = $taskFrameIds[[string]$item.id]
        if ([string]$item.file -cne [string]$frame.file -or [string]$item.sha256 -cne [string]$frame.sha256 -or -not [bool]$item.binary_alpha) { throw "运行证据未绑定当前源PNG：$id / $($item.id)" }
    }
    Assert-SameAnimations $observed.clip_dependencies $taskOldCatalog.animations "运行证据$id"
}
$gpuObserved = $taskReports['gpu'].observed
if ($gpuObserved.gpu_case_count -ne 80 -or @($gpuObserved.gpu_cases).Count -ne 80) { throw 'GPU 报告缺少完整 80 项读回。' }
$taskGpuPairs = @{}
foreach ($item in $gpuObserved.gpu_cases) {
    if ($item.alpha_changed -ne 0 -or $item.visible_rgb_changed -ne 0) { throw 'GPU 读回仍有 Alpha 或角色色差异。' }
    if (-not $taskFrameIds.ContainsKey([string]$item.id) -or [string]$item.source_sha256 -cne [string]$taskFrameIds[[string]$item.id].sha256 -or $item.factor -notin @(1,4)) { throw 'GPU 读回没有绑定当前PNG或整数缩放。' }
    $pair = [string]$item.id + '/' + [string]$item.factor
    if ($taskGpuPairs.ContainsKey($pair)) { throw "GPU重复读回：$pair" }
    $taskGpuPairs[$pair] = $true
}
if ($taskReports.ContainsKey('protected')) {
    Assert-SourceHash $taskProtectedBeforePath ([string]$taskReports['protected'].source_baseline_sha256) | Out-Null
    foreach ($entry in $taskReports['protected'].files) {
        $path = Get-Field $entry 'path'
        if ($null -eq $path) { $path = Get-Field $entry 'file' }
        $hash = Get-Field $entry 'sha256_after'
        if ($null -eq $hash) { $hash = Get-Field $entry 'after_sha256' }
        if ($null -eq $hash) { $hash = Get-Field $entry 'sha256' }
        Assert-SourceHash ([string]$path) ([string]$hash) | Out-Null
        if (-not [bool]$entry.unchanged) { throw "旧资源被改写：$path" }
    }
}
foreach ($pair in @(@($taskNativeManifestPath,'source_manifest_sha256'),@($taskCatalogPath,'catalog_sha256'),@('assets/ember/characters/robot/robot_sprite_frames_v004.tres','frames_resource_sha256'),@([string]$taskCatalog.sheet.texture,'atlas_sha256'))) {
    Assert-SourceHash $pair[0] ([string](Get-Field $taskReports['visual'] $pair[1])) | Out-Null
}
$visual = $taskReports['visual']
Assert-SourceHash ($taskSource + '/joint_repair_v004.json') ([string]$visual.native_report_sha256) | Out-Null
foreach ($pair in @(@('independent_findings_file','independent_findings_sha256'),@('independent_sha_checks_file','independent_sha_checks_sha256'))) {
    $path = $taskSource + '/' + [string](Get-Field $visual $pair[0])
    Assert-SourceHash $path ([string](Get-Field $visual $pair[1])) | Out-Null
    Add-SourceFile $path
}
if (@($visual.frames).Count -ne 40 -or [int]$visual.changed_count -ne $taskChangedCount -or [int]$visual.preserved_count -ne $taskPreservedCount) { throw '人工/独立视觉审查没有覆盖全部当前40帧。' }
$taskVisualIds = @{}
foreach ($item in $visual.frames) {
    if (-not $taskFrameIds.ContainsKey([string]$item.id) -or $taskVisualIds.ContainsKey([string]$item.id)) { throw "视觉审查帧ID未知或重复：$($item.id)" }
    $taskVisualIds[[string]$item.id] = $true
    $current = $taskFrameIds[[string]$item.id]
    if ([string]$item.file -cne [string]$current.file -or [string]$item.sha256 -cne [string]$current.sha256 -or [bool]$item.changed -ne [bool]$current.joint_repair_changed -or @($item.issues).Count -ne 0) { throw "视觉审查没有绑定当前帧或仍有未解决关节问题：$($item.id)" }
}
if (-not [bool]$visual.timeline_review.pose_joints_continuous -or -not [bool]$visual.timeline_review.head_feet_tool_position_preserved -or @($visual.timeline_review.source_frames).Count -ne 12) { throw '视觉审查缺少完整12项实际播放时轴。' }
foreach ($entry in $visual.timeline_review.source_frames) {
    Assert-SourceHash ($taskSource + '/previews/animation_frames/' + [string]$entry.file) ([string]$entry.sha256) | Out-Null
}
if (-not $taskReports.ContainsKey('encoding') -or -not $taskReports['encoding'].webp_exact_rgba -or $taskReports['encoding'].gif_native_palette_mismatch -ne 0 -or $taskReports['encoding'].native_palette_samples -le 0) { throw '动画预览没有通过无损/角色色检查。' }
foreach ($entry in $taskReports['encoding'].source_frames) {
    Assert-SourceHash ($taskSource + '/previews/animation_frames/' + [string]$entry.file) ([string]$entry.sha256) | Out-Null
}
foreach ($name in @('webp','gif')) {
    $output = Get-Field $taskReports['encoding'].outputs $name
    if ($null -eq $output -or [string]::IsNullOrWhiteSpace([string]$output.file)) { throw "编码报告缺少预览输出：$name" }
    $path = $taskSource + '/previews/' + [string]$output.file
    Assert-SourceHash $path ([string]$output.sha256) | Out-Null
    Add-SourceFile $path
}
if (-not (Test-Path -LiteralPath (Join-Path $taskWorkspace ($taskSource + '/previews/.gdignore')) -PathType Leaf)) { throw '浏览器媒体目录必须使用.gdignore，避免Godot导入动画WebP。' }
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

if ($DeliveryName -notmatch '^robot_joint_repair_v004_\d{4}-\d{2}-\d{2}$') { throw 'DeliveryName 必须是 robot_joint_repair_v004_YYYY-MM-DD。' }
$taskDeliveries = [IO.Path]::GetFullPath((Join-Path $taskWorkspace 'art-source/ember/deliveries'))
if (Test-Path -LiteralPath $taskDeliveries) {
    if (((Get-Item -LiteralPath $taskDeliveries).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'deliveries 为链接，拒绝写入。' }
} else { New-Item -ItemType Directory -Path $taskDeliveries | Out-Null }
$taskArchive = Join-Path $taskDeliveries ($DeliveryName + '.zip')
$taskStage = Join-Path ([IO.Path]::GetTempPath()) ('CodexRobotJointRepairV004-' + [guid]::NewGuid().ToString('N'))
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
config/name="Ember Robot Joint Repair v004"
run/main_scene="res://scenes/ember/robot_animation_sandbox_v004.tscn"
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
# 机器人关节修复 v004

这是可独立启动的 Godot 4.7.2 素材审阅工程。双击 Start.cmd，或在 Godot 导入本目录的 project.godot。

原生画布 64×96，固定虚拟脚底 (32,80)。四方向各含 2 帧 idle、4 帧 walk、4 帧 collect，共 40 个姿态、12 段动作。v004 保留没有断裂的原 PNG 路径和 SHA，只把需要修复的关节写入 repairs_v004/；动作顺序、FPS、循环方式和工具手不变。

快捷键和逐帧修复记录见 docs/shader-learning/robot-joint-repair-v004.md。修复计划、关节标注、原帧/新帧 SHA 和差异预览保留于 art-source/ember/robot-joint-repair-v004/。修复前 40 个原 PNG 同时保留，便于逐项对照与回退。

可复用入口：assets/ember/characters/robot/robot_sprite_frames_v004.tres 和 robot_frames_catalog_v004.json；目录记录了每个姿态应使用的 PNG，不能只复制 repairs_v004/。展示场景使用整数缩放与 Nearest；本包没有主项目 Game autoload。

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
& $GodotPath --path $PSScriptRoot 'res://scenes/ember/robot_animation_sandbox_v004.tscn'
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
$taskManifest = @{revision='robot_joint_repair_v004'; frame_count=40; changed_pose_count=$taskChangedCount; preserved_pose_count=$taskPreservedCount; animation_count=12; canvas=@(64,96); anchor=@(32,80); main_scene=$taskScene; files=$taskEntries; frame_preservation=$taskPreservation; cold_verify=$verify}
$taskManifestPath = Join-Path $taskStage 'file_hashes.json'
Set-Content -LiteralPath $taskManifestPath -Value ($taskManifest | ConvertTo-Json -Depth 9) -Encoding utf8
$taskExpected = @{}
foreach ($entry in $taskEntries) { $taskExpected[$entry.path] = $entry }
$taskExpected['file_hashes.json'] = @{bytes=(Get-Item -LiteralPath $taskManifestPath).Length; sha256=(Get-FileHash -LiteralPath $taskManifestPath -Algorithm SHA256).Hash.ToLowerInvariant()}
$taskPending = Join-Path ([IO.Path]::GetTempPath()) ('CodexRobotJointRepairV004-' + [guid]::NewGuid().ToString('N') + '.zip')
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
$taskPackageReport = @{status='PASS'; revision='robot_joint_repair_v004'; archive=$taskArchive; archive_sha256=(Get-FileHash -LiteralPath $taskArchive -Algorithm SHA256).Hash.ToLowerInvariant(); stage_root=$taskStage; files=$taskExpected.Count; manifest_files=$taskEntries.Count; zip_entries_verified=$seen.Count; frame_count=40; changed_pose_count=$taskChangedCount; preserved_pose_count=$taskPreservedCount; animation_count=12; original_catalog_sha256=(Get-FileHash -LiteralPath (Resolve-SourceFile $taskOldCatalogPath) -Algorithm SHA256).Hash.ToLowerInvariant(); frame_manifest_sha256=(Get-FileHash -LiteralPath (Resolve-SourceFile $taskNativeManifestPath) -Algorithm SHA256).Hash.ToLowerInvariant(); frame_preservation=$taskPreservation; evidence_config_sha256=(Get-FileHash -LiteralPath $taskEvidencePath -Algorithm SHA256).Hash.ToLowerInvariant(); tool_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant(); cold_start_validation='NOT_RUN_BY_PACKAGER'}
Set-Content -LiteralPath (Join-Path $sourceRoot 'package_validation_v004.json') -Value ($taskPackageReport | ConvertTo-Json -Depth 6) -Encoding utf8
Write-Output ('ROBOT_ARCHIVE_SAVED: ' + $taskArchive)
Write-Output ('ROBOT_ARCHIVE_SHA256: ' + $taskPackageReport.archive_sha256)

