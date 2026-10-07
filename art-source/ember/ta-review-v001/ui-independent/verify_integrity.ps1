$ErrorActionPreference = 'Stop'
$uiProjectRoot = 'E:/dev/shader/godot-shader/godot-shader-simple'
$uiReviewRoot = Join-Path $uiProjectRoot 'art-source/ember/ta-review-v001/ui-independent'
$uiArchive = Join-Path $uiProjectRoot 'art-source/ember/deliveries/ui_edge_components_v002_2026-10-06.zip'
$uiExtractRoot = Join-Path $uiReviewRoot 'cold-project'
if (Test-Path -LiteralPath $uiExtractRoot) { throw 'Review extraction directory already exists.' }
Expand-Archive -LiteralPath $uiArchive -DestinationPath $uiExtractRoot
$uiManifest = Get-Content -LiteralPath (Join-Path $uiProjectRoot 'art-source/ember/ui-edge-v001/package-manifest.json') -Raw | ConvertFrom-Json
$uiValidation = Get-Content -LiteralPath (Join-Path $uiProjectRoot 'art-source/ember/ui-edge-v001/validation-report.json') -Raw | ConvertFrom-Json
$uiGpu = Get-Content -LiteralPath (Join-Path $uiProjectRoot 'art-source/ember/ui-edge-v001/gpu-validation.json') -Raw | ConvertFrom-Json
$uiChecks = [System.Collections.Generic.List[object]]::new()
foreach ($uiItem in $uiManifest.files) {
    foreach ($uiScope in @('workspace', 'archive')) {
        $uiScopeRoot = if ($uiScope -eq 'workspace') { $uiProjectRoot } else { $uiExtractRoot }
        $uiItemPath = Join-Path $uiScopeRoot $uiItem.path
        $uiActualHash = (Get-FileHash -LiteralPath $uiItemPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $uiChecks.Add([ordered]@{scope=$uiScope;path=$uiItem.path;pass=($uiActualHash -eq $uiItem.sha256);sha256=$uiActualHash})
    }
}
foreach ($uiProperty in $uiValidation.source_sha256.PSObject.Properties) {
    $uiRelativePath = $uiProperty.Name -replace '^res://', ''
    $uiActualHash = (Get-FileHash -LiteralPath (Join-Path $uiProjectRoot $uiRelativePath) -Algorithm SHA256).Hash.ToLowerInvariant()
    $uiChecks.Add([ordered]@{scope='validation_sources';path=$uiRelativePath;pass=($uiActualHash -eq $uiProperty.Value);sha256=$uiActualHash})
}
foreach ($uiItem in $uiValidation.protected_existing_sources) {
    $uiActualHash = (Get-FileHash -LiteralPath (Join-Path $uiProjectRoot $uiItem.path) -Algorithm SHA256).Hash.ToLowerInvariant()
    $uiChecks.Add([ordered]@{scope='protected_sources';path=$uiItem.path;pass=($uiActualHash -eq $uiItem.sha256);sha256=$uiActualHash})
}
foreach ($uiItem in $uiGpu.captures) {
    $uiRelativePath = $uiItem.file -replace '^res://', ''
    $uiActualHash = (Get-FileHash -LiteralPath (Join-Path $uiProjectRoot $uiRelativePath) -Algorithm SHA256).Hash.ToLowerInvariant()
    $uiChecks.Add([ordered]@{scope='gpu_captures';path=$uiRelativePath;pass=($uiActualHash -eq $uiItem.sha256);sha256=$uiActualHash})
}
$uiReferenceHash = (Get-FileHash -LiteralPath (Join-Path $uiProjectRoot 'art-source/ember/ui-edge-v001/selected_reference.png') -Algorithm SHA256).Hash.ToLowerInvariant()
$uiChecks.Add([ordered]@{scope='reference';path='selected_reference.png';pass=($uiReferenceHash -eq $uiValidation.reference_sha256);sha256=$uiReferenceHash})
$uiFailures = @($uiChecks | Where-Object { -not $_.pass })
$uiReport = [ordered]@{archive_sha256=(Get-FileHash -LiteralPath $uiArchive -Algorithm SHA256).Hash.ToLowerInvariant();manifest_count=$uiManifest.files.Count;check_count=$uiChecks.Count;failures=$uiFailures;checks=$uiChecks}
$uiReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $uiReviewRoot 'integrity-report.json') -Encoding utf8
[ordered]@{archive_sha256=$uiReport.archive_sha256;manifest_count=$uiReport.manifest_count;check_count=$uiReport.check_count;failure_count=$uiFailures.Count} | ConvertTo-Json
