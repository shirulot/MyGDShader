# 在实际Godot进程与无原缓存工程中验证交付；所有测试窗口隐藏，旧主场景不替换。
param([string]$Godot = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe', [switch]$ResumeFromBuild)
$ErrorActionPreference = 'Stop'
$workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$proofRoot = $PSScriptRoot
$stageResults = [System.Collections.Generic.List[object]]::new()
if ($ResumeFromBuild) {
    # 修复构建器后复用已成功的两次导入；不重复与本次修改无关的检查。
    $previousStages = @(Get-Content -LiteralPath (Join-Path $proofRoot 'godot-stage-exit-codes.json') -Raw | ConvertFrom-Json)
    foreach ($previousStage in $previousStages) {
        if ($previousStage.stage -in @('import','import-settings')) {
            if ($previousStage.exit_code -ne 0 -or $previousStage.stderr_bytes -ne 0) { throw 'Previous import did not pass' }
            $stageResults.Add($previousStage)
        }
    }
    if ($stageResults.Count -ne 2) { throw 'Missing two successful import stages' }
}

function Invoke-VerifiedGodot([string]$Stage, [string[]]$Arguments) {
    $stdoutPath = Join-Path $proofRoot ($Stage + '.stdout.log')
    $stderrPath = Join-Path $proofRoot ($Stage + '.stderr.log')
    $processResult = Start-Process -FilePath $Godot -ArgumentList $Arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $stderrLength = (Get-Item -LiteralPath $stderrPath).Length
    $stageResults.Add(@{ stage=$Stage; arguments=$Arguments; exit_code=$processResult.ExitCode; stderr_bytes=$stderrLength })
    $stageResults | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $proofRoot 'godot-stage-exit-codes.json') -Encoding utf8
    if ($processResult.ExitCode -ne 0 -or $stderrLength -ne 0) {
        Get-Content -LiteralPath $stderrPath
        throw ('Godot stage failed: ' + $Stage)
    }
}

# 3D保留mipmaps；2D仍以原生Nearest显示。只改变本批新PNG的.import参数。
if (-not $ResumeFromBuild) {
Invoke-VerifiedGodot 'import' @('--headless','--editor','--path',$workspaceRoot,'--import')
$catalog = Get-Content -LiteralPath (Join-Path $workspaceRoot 'assets/ember/ember_additional_catalog_v001.json') -Raw | ConvertFrom-Json
foreach ($asset in $catalog.assets) {
    $importPath = Join-Path $workspaceRoot ($asset.file.Replace('res://','') + '.import')
    $importText = Get-Content -LiteralPath $importPath -Raw
    $mipmapValue = if ($asset.manifest_id.StartsWith('X')) { 'true' } else { 'false' }
    $importText = [regex]::Replace($importText, 'mipmaps/generate=(true|false)', ('mipmaps/generate=' + $mipmapValue))
    # PNG底图使用Lossless，技术纹理类型与源通道由catalog独立登记。
    $importText = [regex]::Replace($importText, 'compress/mode=\d+', 'compress/mode=0')
    Set-Content -LiteralPath $importPath -Value $importText -Encoding utf8 -NoNewline
}
Invoke-VerifiedGodot 'import-settings' @('--headless','--editor','--path',$workspaceRoot,'--import')
}
Invoke-VerifiedGodot 'build' @('--headless','--path',$workspaceRoot,'--script','res://tools/build_ember_asset_library.gd','--')
Invoke-VerifiedGodot 'verify' @('--headless','--path',$workspaceRoot,'--script','res://tools/build_ember_asset_library.gd','--','--verify-only',('--report=' + (Join-Path $proofRoot 'godot-verify-only-v001.json')))
Invoke-VerifiedGodot 'render' @('--path',$workspaceRoot,'--position','-2000,-2000','--script','res://tools/build_ember_asset_library.gd','--','--verify-only',('--screenshots=' + (Join-Path $proofRoot 'render')),('--report=' + (Join-Path $proofRoot 'godot-render-v001.json')))

# 不删除旧测试目录；若同名目录已有缓存，使用新版本目录重新证明无缓存导入。
$freshVersion = 1
do {
    $freshRoot = Join-Path $proofRoot ('fresh-project-v{0:000}' -f $freshVersion)
    $freshVersion++
} while (Test-Path -LiteralPath $freshRoot)
New-Item -ItemType Directory -Path $freshRoot | Out-Null
$copied = @{}
foreach ($folder in @('assets/ember','scenes/ember')) {
    $originFolder = Join-Path $workspaceRoot $folder
    foreach ($sourceFile in Get-ChildItem -LiteralPath $originFolder -Recurse -File) {
        $relativePath = [IO.Path]::GetRelativePath($workspaceRoot,$sourceFile.FullName)
        $destination = Join-Path $freshRoot $relativePath
        New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destination)) -Force | Out-Null
        Copy-Item -LiteralPath $sourceFile.FullName -Destination $destination
        $copied[$relativePath.Replace('\','/')] = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
foreach ($builder in @('build_ember_tilesets.gd','build_ember_robot_animation.gd','build_ember_asset_library.gd')) {
    $relativePath = 'tools/' + $builder
    $destination = Join-Path $freshRoot $relativePath
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destination)) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $workspaceRoot $relativePath) -Destination $destination
    $copied[$relativePath] = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
}
@'
config_version=5
[application]
config/name="EmberFullAssetReuse"
[rendering]
renderer/rendering_method="gl_compatibility"
'@ | Set-Content -LiteralPath (Join-Path $freshRoot 'project.godot') -Encoding utf8
if (Test-Path -LiteralPath (Join-Path $freshRoot '.godot')) { throw 'Fresh project unexpectedly has cache' }
@{ fresh_project=$freshRoot; godot_cache_present_before_import=$false; autoload_present=$false; files=$copied } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $proofRoot 'fresh-copy-manifest.json') -Encoding utf8
Invoke-VerifiedGodot 'fresh-import' @('--headless','--editor','--path',$freshRoot,'--import')
Invoke-VerifiedGodot 'fresh-library' @('--headless','--path',$freshRoot,'--script','res://tools/build_ember_asset_library.gd','--','--verify-only',('--report=' + (Join-Path $proofRoot 'godot-fresh-library-v001.json')))
Invoke-VerifiedGodot 'fresh-tilesets' @('--headless','--path',$freshRoot,'--script','res://tools/build_ember_tilesets.gd','--','--verify-only')
Invoke-VerifiedGodot 'fresh-robot' @('--headless','--path',$freshRoot,'--script','res://tools/build_ember_robot_animation.gd','--','--verify-only',('--report=' + (Join-Path $proofRoot 'godot-fresh-robot-v001.json')))
Invoke-VerifiedGodot 'fresh-render' @('--path',$freshRoot,'--position','-2000,-2000','--script','res://tools/build_ember_asset_library.gd','--','--verify-only',('--screenshots=' + (Join-Path $proofRoot 'fresh-render')),('--report=' + (Join-Path $proofRoot 'godot-fresh-render-v001.json')))
$changed = @($copied.Keys | Where-Object { (Get-FileHash -LiteralPath (Join-Path $freshRoot $_) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $copied[$_] })
if ($changed.Count -gt 0) { throw ('Fresh files changed: ' + ($changed -join ', ')) }
@{ status='GODOT_FULL_ART_AND_FRESH_REUSE_PASS'; stages=$stageResults; copied_file_count=$copied.Count; fresh_files_changed=$changed; fresh_project=$freshRoot } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $proofRoot 'godot-delivery-summary-v001.json') -Encoding utf8
Write-Output ('Godot full art + fresh reuse PASS, stages: ' + $stageResults.Count)
