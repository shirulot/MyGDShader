# 冻结已经在独立冷工程验证的交付。旧版本永不覆盖；返修时使用新的Revision。
param([ValidatePattern('^v[0-9]{3}$')][string]$Revision = 'v004')
$ErrorActionPreference = 'Stop'
$uiRoot = (Get-Location).Path
$uiEvidence = Join-Path $uiRoot 'art-source/ember/ui-interactions-v004'
$uiStage = Join-Path $uiEvidence "review-build-$Revision"
$uiNewEvidence = Join-Path $uiStage 'art-source/ember/ui-interactions-v004'
$uiOldEvidence = Join-Path $uiStage 'art-source/ember/ui-edge-v001'
$uiInputs = Get-Content -LiteralPath (Join-Path $uiStage 'input-manifest.json') -Raw | ConvertFrom-Json
# 源码改变必须重新准备和验证；不得只换zip哈希复用旧证据。
foreach ($item in $uiInputs.inputs) {
    if ([IO.Path]::GetExtension($item.path) -in @('.gd','.tscn','.png')) {
        foreach ($rootPath in @($uiRoot,$uiStage)) {
            if ((Get-FileHash -LiteralPath (Join-Path $rootPath $item.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw "Input changed: $($item.path)" }
        }
    }
}
$uiChecks = 0
foreach ($name in @('logic-validation.json','reuse-validation-v002.json','lifecycle-validation-v003.json','ta-regression-v003.json','widget-audit-v002.json')) {
    $report = Get-Content -LiteralPath (Join-Path $uiOldEvidence $name) -Raw | ConvertFrom-Json
    if ($report.status -ne 'PASS') { throw "Failed regression: $name" }
    $uiChecks += $report.check_count
}
$uiInteractions = Get-Content -LiteralPath (Join-Path $uiNewEvidence 'interaction-validation.json') -Raw | ConvertFrom-Json
$uiLayout = Get-Content -LiteralPath (Join-Path $uiOldEvidence 'layout-audit-v002.json') -Raw | ConvertFrom-Json
$uiGpu = Get-Content -LiteralPath (Join-Path $uiNewEvidence 'gpu-validation.json') -Raw | ConvertFrom-Json
$uiNavigation = Get-Content -LiteralPath (Join-Path $uiNewEvidence 'navigation-supplement.json') -Raw | ConvertFrom-Json
$uiFocus = Get-Content -LiteralPath (Join-Path $uiNewEvidence 'slider-focus-validation.json') -Raw | ConvertFrom-Json
if ($uiFocus.status -ne 'PASS' -or $uiFocus.changed_pixels -le 0) { throw 'Slider focus lacks GPU evidence' }
if ($uiNavigation.status -ne 'PASS' -or $uiNavigation.ui_source_sha256 -ne (Get-FileHash -LiteralPath (Join-Path $uiStage 'scripts/ember/ui_edge_v004/interaction_ui.gd') -Algorithm SHA256).Hash.ToLowerInvariant()) { throw 'Navigation supplement failed or stale' }
$uiChecks += $uiNavigation.check_count
if ($uiInteractions.status -ne 'PASS' -or $uiLayout.tested_layout_result -ne 'PASS' -or $uiGpu.status -ne 'PASS') { throw 'New interaction, layout or GPU evidence failed.' }
foreach ($property in $uiInteractions.source_sha256.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path $uiStage $property.Name.Replace('res://','')) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $property.Value) { throw 'Stale source evidence' }
}
foreach ($capture in $uiGpu.captures) {
    if ((Get-FileHash -LiteralPath (Join-Path $uiStage $capture.path.Replace('res://','')) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $capture.sha256) { throw 'Stale capture evidence' }
}
$errors = @(Get-ChildItem -LiteralPath $uiStage -Filter '*error.log' | Where-Object Length -gt 0)
if ($errors.Count -gt 0) { throw 'Cold validation has stderr output.' }
$uiProtected = Get-Content -LiteralPath (Join-Path $uiRoot 'art-source/ember/ui-edge-v001/protected-source-baseline.json') -Raw | ConvertFrom-Json
foreach ($property in $uiProtected.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path $uiRoot $property.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $property.Value.ToLowerInvariant()) { throw "Protected source changed: $($property.Name)" }
}
$uiSummary = [ordered]@{revision=$Revision;production_validation='PASS';ta_review='PENDING';runtime_checks=($uiChecks+$uiInteractions.check_count);interaction_checks=$uiInteractions.check_count;layout_samples=$uiLayout.sample_count;layout_geometry_errors=$uiLayout.geometry_error_count;legacy_safe_elision_notes=$uiLayout.limitation_count;gpu_captures=@($uiGpu.captures).Count;cold_import='PASS';stderr_bytes=0;protected_source_hashes=$uiProtected;source_sha256=$uiInteractions.source_sha256;scope='Horizontal life and complete declared UI flows in a real map preview; M0 teaching scene unchanged.'}
if (Test-Path -LiteralPath (Join-Path $uiNewEvidence 'inherited-validation.json')) {
    $uiSummary['inherited_evidence'] = Get-Content -LiteralPath (Join-Path $uiNewEvidence 'inherited-validation.json') -Raw | ConvertFrom-Json
    $uiSummary['fresh_runtime_checks'] = $uiInteractions.check_count + $uiNavigation.check_count
}
$uiSummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $uiNewEvidence 'validation-summary.json') -Encoding utf8
Copy-Item -LiteralPath (Join-Path $uiNewEvidence 'validation-summary.json') -Destination (Join-Path $uiEvidence 'validation-summary.json') -Force
foreach($name in @('interaction-validation.json','gpu-validation.json','navigation-supplement.json','slider-focus-validation.json')) { Copy-Item -LiteralPath (Join-Path $uiNewEvidence $name) -Destination (Join-Path $uiEvidence $name) -Force }
Get-ChildItem -LiteralPath (Join-Path $uiStage 'assets/ember/ui_final/previews') -Filter '*.png' | Copy-Item -Destination (Join-Path $uiRoot 'assets/ember/ui_final/previews') -Force
$uiZip = Join-Path $uiRoot "art-source/ember/deliveries/ui_edge_interactions_${Revision}_2026-10-06.zip"
if (Test-Path -LiteralPath $uiZip) { throw 'Frozen delivery already exists; use a new revision.' }
$uiFiles = @(Get-ChildItem -LiteralPath $uiStage -File -Recurse | Where-Object { $_.FullName -notlike "$uiStage\.godot\*" -and $_.Name -ne 'package-manifest.json' -and ($_.Name -ne '.gdignore' -or $_.FullName -eq (Join-Path $uiStage 'assets/ember/ui_final/previews/.gdignore')) })
$uiManifest = @($uiFiles | ForEach-Object { [pscustomobject]@{path=$_.FullName.Substring($uiStage.Length+1).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()} })
[ordered]@{version=$Revision;files=$uiManifest} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $uiStage 'package-manifest.json') -Encoding utf8
Add-Type -AssemblyName System.IO.Compression
$archive = [IO.Compression.ZipFile]::Open($uiZip,[IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($item in $uiManifest) { [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,(Join-Path $uiStage $item.path),$item.path,[IO.Compression.CompressionLevel]::Optimal) | Out-Null }
    [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive,(Join-Path $uiStage 'package-manifest.json'),'package-manifest.json',[IO.Compression.CompressionLevel]::Optimal) | Out-Null
} finally { $archive.Dispose() }
$delivery = [ordered]@{revision=$Revision;path=$uiZip;bytes=(Get-Item -LiteralPath $uiZip).Length;sha256=(Get-FileHash -LiteralPath $uiZip -Algorithm SHA256).Hash.ToLowerInvariant();manifest_files=$uiManifest.Count;ta_review='PENDING'}
$delivery | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $uiEvidence "delivery-$Revision.json") -Encoding utf8
$delivery | ConvertTo-Json
