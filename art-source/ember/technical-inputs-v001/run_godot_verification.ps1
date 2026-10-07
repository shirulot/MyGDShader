# 用实际进程退出码和stderr验收；隐藏测试窗口，保持学习者场景不变。
param([string]$Godot = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe', [switch]$ResumeAfterImport, [switch]$RebuildSandbox)
$ErrorActionPreference = 'Stop'
$workspaceRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$proofRoot = $PSScriptRoot
$stageResults = [System.Collections.Generic.List[object]]::new()
function Invoke-VerifiedGodot([string]$Stage, [string[]]$Arguments) {
    $stdoutPath = Join-Path $proofRoot ($Stage + '.stdout.log')
    $stderrPath = Join-Path $proofRoot ($Stage + '.stderr.log')
    $processResult = Start-Process -FilePath $Godot -ArgumentList $Arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $stderrLength = (Get-Item -LiteralPath $stderrPath).Length
    $stageResults.Add(@{stage=$Stage; arguments=$Arguments; exit_code=$processResult.ExitCode; stderr_bytes=$stderrLength})
    $stageResults | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $proofRoot 'godot-stage-exit-codes.json') -Encoding utf8
    if ($processResult.ExitCode -ne 0 -or $stderrLength -ne 0) {
        Get-Content -LiteralPath $stderrPath
        throw ('Godot stage failed: ' + $Stage)
    }
}

if (-not $ResumeAfterImport) {
    Invoke-VerifiedGodot 'import' @('--headless','--editor','--path',$workspaceRoot,'--import')
    $catalog = Get-Content -LiteralPath (Join-Path $workspaceRoot 'assets/ember/data/technical_inputs_catalog_v001.json') -Raw | ConvertFrom-Json
    foreach ($asset in $catalog.assets) {
        # 只调整40张本批技术图，尤其禁止对Mask透明边缘自动填色。
        $importPath = Join-Path $workspaceRoot ($asset.file.Replace('res://','') + '.import')
        $importText = Get-Content -LiteralPath $importPath -Raw
        $mipmapValue = if ($asset.mipmaps) { 'true' } else { 'false' }
        $importText = [regex]::Replace($importText, 'mipmaps/generate=(true|false)', ('mipmaps/generate=' + $mipmapValue))
        # 枚举含义不同：normal_map 的 0 是 Detect，2 才是 Disabled。
        # 禁止编辑器根据使用方式自动压缩法线或处理粗糙度 Mipmaps。
        $numericOptions = @{'compress/mode'=0; 'compress/normal_map'=2; 'roughness/mode'=1; 'detect_3d/compress_to'=0}
        foreach ($option in $numericOptions.Keys) {
            $pattern = [regex]::Escape($option) + '=\d+'
            if ([regex]::Matches($importText, $pattern).Count -ne 1) { throw ('Missing or duplicate import option: ' + $option) }
            $importText = [regex]::Replace($importText, $pattern, ($option + '=' + $numericOptions[$option]))
        }
        foreach ($option in @('process/fix_alpha_border','process/premult_alpha','process/normal_map_invert_y')) {
            $importText = [regex]::Replace($importText, ([regex]::Escape($option) + '=(true|false)'), ($option + '=false'))
        }
        Set-Content -LiteralPath $importPath -Value $importText -Encoding utf8 -NoNewline
    }
    Invoke-VerifiedGodot 'import-settings' @('--headless','--editor','--path',$workspaceRoot,'--import')
} else {
    foreach ($previous in @(Get-Content -LiteralPath (Join-Path $proofRoot 'godot-stage-exit-codes.json') -Raw | ConvertFrom-Json)) {
        if ($previous.stage -in @('import','import-settings') -and $previous.exit_code -eq 0 -and $previous.stderr_bytes -eq 0) { $stageResults.Add($previous) }
    }
    if ($stageResults.Count -ne 2) { throw 'Missing two successful import stages' }
}
$buildArguments = @('--headless','--path',$workspaceRoot,'--script','res://tools/build_ember_technical_inputs.gd','--')
if ($RebuildSandbox) { $buildArguments += '--rebuild-sandbox' }
Invoke-VerifiedGodot 'build' $buildArguments
Invoke-VerifiedGodot 'verify' @('--headless','--path',$workspaceRoot,'--script','res://tools/build_ember_technical_inputs.gd','--','--verify-only',('--report=' + (Join-Path $proofRoot 'godot-verify-only.json')))
Invoke-VerifiedGodot 'render' @('--path',$workspaceRoot,'--position','-2000,-2000','--script','res://tools/build_ember_technical_inputs.gd','--','--verify-only',('--screenshots=' + (Join-Path $proofRoot 'render')),('--report=' + (Join-Path $proofRoot 'godot-render.json')))

# 新工程没有原项目缓存和Autoload。复制实际生产资源和预览，核对复用结果。
$freshVersion = 1
do { $freshRoot = Join-Path $proofRoot ('fresh-project-v{0:000}' -f $freshVersion); $freshVersion++ } while (Test-Path -LiteralPath $freshRoot)
New-Item -ItemType Directory -Path $freshRoot | Out-Null
$copied = @{}
foreach ($folder in @('assets/ember','scenes/ember')) {
    foreach ($sourceFile in Get-ChildItem -LiteralPath (Join-Path $workspaceRoot $folder) -Recurse -File) {
        $relativePath = [IO.Path]::GetRelativePath($workspaceRoot,$sourceFile.FullName)
        $destination = Join-Path $freshRoot $relativePath
        New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($destination)) -Force | Out-Null
        Copy-Item -LiteralPath $sourceFile.FullName -Destination $destination
        $copied[$relativePath.Replace('\','/')] = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$relativePath = 'tools/build_ember_technical_inputs.gd'
New-Item -ItemType Directory -Path (Join-Path $freshRoot 'tools') | Out-Null
Copy-Item -LiteralPath (Join-Path $workspaceRoot $relativePath) -Destination (Join-Path $freshRoot $relativePath)
$copied[$relativePath] = (Get-FileHash -LiteralPath (Join-Path $freshRoot $relativePath) -Algorithm SHA256).Hash.ToLowerInvariant()
@'
config_version=5
[application]
config/name="EmberTechnicalReuse"
[rendering]
renderer/rendering_method="gl_compatibility"
'@ | Set-Content -LiteralPath (Join-Path $freshRoot 'project.godot') -Encoding utf8
if (Test-Path -LiteralPath (Join-Path $freshRoot '.godot')) { throw 'Unexpected cache in fresh project' }
@{fresh_project=$freshRoot; godot_cache_present_before_import=$false; autoload_present=$false; files=$copied} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $proofRoot 'fresh-copy-manifest.json') -Encoding utf8
Invoke-VerifiedGodot 'fresh-import' @('--headless','--editor','--path',$freshRoot,'--import')
Invoke-VerifiedGodot 'fresh-verify' @('--headless','--path',$freshRoot,'--script','res://tools/build_ember_technical_inputs.gd','--','--verify-only',('--report=' + (Join-Path $proofRoot 'godot-fresh-verify.json')))
Invoke-VerifiedGodot 'fresh-render' @('--path',$freshRoot,'--position','-2000,-2000','--script','res://tools/build_ember_technical_inputs.gd','--','--verify-only',('--screenshots=' + (Join-Path $proofRoot 'fresh-render')),('--report=' + (Join-Path $proofRoot 'godot-fresh-render.json')))
$changed = @($copied.Keys | Where-Object { (Get-FileHash -LiteralPath (Join-Path $freshRoot $_) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $copied[$_] })
if ($changed.Count -gt 0) { throw ('Fresh files changed: ' + ($changed -join ', ')) }
@{status='GODOT_TECHNICAL_AND_FRESH_REUSE_PASS'; stages=$stageResults; copied_file_count=$copied.Count; fresh_files_changed=$changed; fresh_project=$freshRoot} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $proofRoot 'godot-delivery-summary.json') -Encoding utf8
Write-Output ('Godot technical + fresh reuse PASS, stages: ' + $stageResults.Count)
