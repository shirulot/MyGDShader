$ErrorActionPreference = 'Stop'
# 从固定ZIP内读取manifest，避免误用后来被更新的工作区清单。
$taRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$taNewPath = Join-Path $taRoot 'art-source/ember/deliveries/ui_edge_components_v003_2026-10-06.zip'
$taOldPath = Join-Path $taRoot 'art-source/ember/deliveries/ui_edge_components_v002_2026-10-06.zip'
$taChecks = [System.Collections.Generic.List[object]]::new()
function Read-ZipText($archive, [string]$path) {
    $entry = $archive.GetEntry($path)
    if ($null -eq $entry) { throw "Missing ZIP entry: $path" }
    $reader = [System.IO.StreamReader]::new($entry.Open())
    try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
}
function Get-ZipHash($archive, [string]$path) {
    $entry = $archive.GetEntry($path)
    if ($null -eq $entry) { throw "Missing ZIP entry: $path" }
    $stream = $entry.Open()
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return [Convert]::ToHexString($sha.ComputeHash($stream)).ToLowerInvariant() }
    finally { $stream.Dispose(); $sha.Dispose() }
}
function Add-HashCheck([string]$scope, [string]$path, [string]$actual, [string]$expected) {
    $taChecks.Add([ordered]@{scope=$scope;path=$path;pass=($actual -eq $expected);sha256=$actual;expected=$expected})
}
$taNew = [System.IO.Compression.ZipFile]::OpenRead($taNewPath)
$taOld = [System.IO.Compression.ZipFile]::OpenRead($taOldPath)
try {
    Add-HashCheck 'archive' 'v003.zip' ((Get-FileHash -LiteralPath $taNewPath).Hash.ToLowerInvariant()) '24def0986879b32e87c862561639140898b6fb21c6d4127f376fcb6cddd6dc49'
    Add-HashCheck 'archive' 'v002.zip' ((Get-FileHash -LiteralPath $taOldPath).Hash.ToLowerInvariant()) 'f2c47d6b377df9fbb3f64f29a9bf3a97e0ddff27197ee4ea36ff666b7bd2c586'
    $taManifest = Read-ZipText $taNew 'art-source/ember/ui-edge-v001/package-manifest.json' | ConvertFrom-Json
    foreach ($item in $taManifest.files) {
        Add-HashCheck 'zip_manifest' $item.path (Get-ZipHash $taNew $item.path) $item.sha256
        Add-HashCheck 'workspace_manifest' $item.path ((Get-FileHash -LiteralPath (Join-Path $taRoot $item.path)).Hash.ToLowerInvariant()) $item.sha256
    }
    $taValidation = Read-ZipText $taNew 'art-source/ember/ui-edge-v001/validation-report.json' | ConvertFrom-Json
    foreach ($property in $taValidation.source_sha256.PSObject.Properties) {
        $relative = $property.Name -replace '^res://', ''
        Add-HashCheck 'bound_source' $relative (Get-ZipHash $taNew $relative) $property.Value
    }
    foreach ($item in $taValidation.protected_existing_sources) {
        Add-HashCheck 'protected_workspace' $item.path ((Get-FileHash -LiteralPath (Join-Path $taRoot $item.path)).Hash.ToLowerInvariant()) $item.sha256
    }
    # 直接比较两个固定ZIP中的像素和场景，不只相信“画面未变”的汇总字段。
    $taVisualEntries = @($taNew.Entries | Where-Object {
        $_.FullName -match '^assets/ember/ui_edge_v001/.*\.png$' -or
        $_.FullName -match '^scenes/ember/ui_edge_v001/components/.*\.tscn$' -or
        $_.FullName -match '^art-source/ember/ui-edge-v001/previews/.*\.png$' -or
        $_.FullName -eq 'art-source/ember/ui-edge-v001/selected_reference.png'
    })
    foreach ($entry in $taVisualEntries) {
        Add-HashCheck 'v002_visual_equality' $entry.FullName (Get-ZipHash $taNew $entry.FullName) (Get-ZipHash $taOld $entry.FullName)
    }
    $taChangedSources = @($taNew.Entries | Where-Object { $_.FullName -match '^scripts/ember/(ui_edge_v001/.*|ui_edge_binding_v001)\.gd$' } | ForEach-Object {
        if ((Get-ZipHash $taNew $_.FullName) -ne (Get-ZipHash $taOld $_.FullName)) { $_.FullName }
    })
    $taFailures = @($taChecks | Where-Object { -not $_.pass })
    $taSummary = [ordered]@{
        status=$(if($taFailures.Count -eq 0){'PASS'}else{'FAIL'});
        manifest_entries=$taManifest.files.Count;check_count=$taChecks.Count;
        visual_entries=$taVisualEntries.Count;changed_sources=$taChangedSources;
        failure_count=$taFailures.Count;failures=$taFailures;checks=$taChecks
    }
    $taSummary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'integrity-v003.json') -Encoding utf8
    [pscustomobject]$taSummary | Select-Object status,manifest_entries,check_count,visual_entries,changed_sources,failure_count | ConvertTo-Json -Depth 4
    if ($taFailures.Count -gt 0) { exit 1 }
}
finally { $taNew.Dispose(); $taOld.Dispose() }
