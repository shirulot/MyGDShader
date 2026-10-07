# 新地图素材的隔离同步入口。默认仅复制输入；只有显式 -FullSync 才覆盖成品资源和场景。
# 示例：.\tools\sync_map_assets_review_v001.ps1 -InputsOnly
# 最终成品同步：.\tools\sync_map_assets_review_v001.ps1 -FullSync
[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$InputsOnly,
    [switch]$FullSync
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($InputsOnly -and $FullSync) {
    throw '-InputsOnly 与 -FullSync 不能同时使用。'
}

$workspacePath = (Resolve-Path -LiteralPath $WorkspaceRoot).Path
$sourceRoot = Join-Path $workspacePath 'art-source\ember\map-assets-v001'
$reviewRoot = Join-Path $sourceRoot 'godot-review'
$projectPath = Join-Path $reviewRoot 'project.godot'
$baselineZip = Join-Path $workspacePath 'art-source\ember\deliveries\reference_floor_v006_2026-10-06.zip'
$baselineSha256 = '7f8bc265cdab09b28e1197a3c7e25c24c115834b7bfaf1985cb33230e6008ef7'
$script:copiedFiles = 0

if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    throw "新素材输入目录不存在：$sourceRoot"
}
# 已存在的 review 绝不重新解压，避免覆盖独立构建或验证的中间产物。
if (-not (Test-Path -LiteralPath $reviewRoot)) {
    if (-not (Test-Path -LiteralPath $baselineZip -PathType Leaf)) {
        throw "已验证基线 ZIP 不存在：$baselineZip"
    }
    $actualSha256 = (Get-FileHash -LiteralPath $baselineZip -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualSha256 -ne $baselineSha256) {
        throw "基线 ZIP SHA256 不匹配；未初始化 review。实际值：$actualSha256"
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($baselineZip, $reviewRoot)
}
if (-not (Test-Path -LiteralPath $projectPath -PathType Leaf)) {
    throw "review 已存在但缺少 project.godot，请检查该目录；脚本不会覆盖或删除它：$reviewRoot"
}

function Copy-ReviewFile {
    param([string]$Source, [string]$Target)
    New-Item -ItemType Directory -Path (Split-Path -Parent $Target) -Force | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Target -Force
    $script:copiedFiles++
}

function Copy-ReviewTree {
    param([string]$SourceDirectory, [string]$TargetDirectory)
    if (-not (Test-Path -LiteralPath $SourceDirectory -PathType Container)) { return }
    # 在递归前排除 review，而不是先 -Recurse 再过滤，防止把目标目录复制进自身。
    foreach ($item in Get-ChildItem -LiteralPath $SourceDirectory -Force) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { continue }
        if ($item.PSIsContainer) {
            if ($item.Name -in @('godot-review', '.godot', '.import')) { continue }
            Copy-ReviewTree -SourceDirectory $item.FullName -TargetDirectory (Join-Path $TargetDirectory $item.Name)
        } elseif ($item.Extension -notin @('.import', '.log')) {
            Copy-ReviewFile -Source $item.FullName -Target (Join-Path $TargetDirectory $item.Name)
        }
    }
}

# 输入包含规格、提示词、真实母稿和来源记录；新母稿尚未全部到齐时也可反复执行。
Copy-ReviewTree -SourceDirectory $sourceRoot -TargetDirectory (Join-Path $reviewRoot 'art-source\ember\map-assets-v001')
foreach ($group in @('scripts\ember', 'tools')) {
    foreach ($item in Get-ChildItem -LiteralPath (Join-Path $workspacePath $group) -File) {
        if ($item.Name -match 'map_.*v001.*\.gd(?:\.uid)?$') {
            Copy-ReviewFile -Source $item.FullName -Target (Join-Path (Join-Path $reviewRoot $group) $item.Name)
        }
    }
}
# 新 painter 使用这份共享编译器；只复制到隔离工程，不改动主工程旧版本文件。
foreach ($dependency in @('scripts\ember\reference_floor_compiler_v002.gd', 'scripts\ember\reference_floor_compiler_v002.gd.uid')) {
    $dependencyPath = Join-Path $workspacePath $dependency
    if (Test-Path -LiteralPath $dependencyPath -PathType Leaf) {
        Copy-ReviewFile -Source $dependencyPath -Target (Join-Path $reviewRoot $dependency)
    }
}

if ($FullSync) {
    # 此分支仅用于主线程明确通知的最终同步；默认调用及 -InputsOnly 均不会进入。
    Copy-ReviewTree -SourceDirectory (Join-Path $workspacePath 'assets\ember\map_assets_v001') -TargetDirectory (Join-Path $reviewRoot 'assets\ember\map_assets_v001')
    foreach ($item in Get-ChildItem -LiteralPath (Join-Path $workspacePath 'scenes\ember') -File) {
        if ($item.Name -match '^map_assets_.*_v001\.tscn(?:\.uid)?$') {
            Copy-ReviewFile -Source $item.FullName -Target (Join-Path $reviewRoot ('scenes\ember\' + $item.Name))
        }
    }
}

$projectText = Get-Content -LiteralPath $projectPath -Raw
if ($projectText -notmatch '(?m)^config/name=') { throw 'review project.godot 缺少 config/name。' }
$renamedProjectText = [regex]::Replace($projectText, '(?m)^config/name=.*$', 'config/name="Map Assets v001"')
if ($renamedProjectText -ne $projectText) {
    Set-Content -LiteralPath $projectPath -Value $renamedProjectText -Encoding utf8 -NoNewline
}
# 新地图资源尚未生成时，沿用 ZIP 内有效的 v006 主场景，不触碰主工程启动入口。
$modeName = if ($FullSync) { 'FULL_SYNC' } else { 'INPUTS_ONLY' }
Write-Output "MAP_ASSETS_REVIEW_READY: $reviewRoot"
Write-Output "MODE: $modeName; COPIED_FILES: $script:copiedFiles"
