param([ValidatePattern('^v[0-9]{3}$')][string]$Version, [ValidatePattern('^(r[0-9]+)?$')][string]$Revision = '')
$ErrorActionPreference = 'Stop'
# 只新增指定版本交付；固定包存在时拒绝覆盖。
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sourceRoot = Join-Path $workspaceRoot ('art-source/ember/enemy-patrol-move-' + $Version)
$deliveryTag = $Version + $(if ($Revision) { '_' + $Revision } else { '' })
$deliveryRoot = Join-Path $workspaceRoot ('art-source/ember/deliveries/enemy_patrol_move_' + $deliveryTag + '_2026-10-06')
$archivePath = $deliveryRoot + '.zip'
if ((Test-Path -LiteralPath $deliveryRoot) -or (Test-Path -LiteralPath $archivePath)) { throw '已有固定版本；使用新版本号。' }
$catalog = Get-Content -LiteralPath ($sourceRoot + '/output/catalog_' + $Version + '.json') -Raw | ConvertFrom-Json
$gpu = Get-Content -LiteralPath ($sourceRoot + '/qa/gpu_playback.json') -Raw | ConvertFrom-Json
if ($catalog.frame_count -ne 8 -or $gpu.status -ne 'PASS' -or $gpu.atlas_sha256 -ne $catalog.atlas_sha256) { throw '八帧实际播放报告没有绑定当前图集。' }
# 把独立端点重算和实际GPU往返对照作为打包前置条件，不能仅看报告标题。
$endpoints = Get-Content -LiteralPath ($sourceRoot+'/qa/endpoint_mapping.json') -Raw | ConvertFrom-Json
$roundtrip = Get-Content -LiteralPath ($sourceRoot+'/qa/render_roundtrip.json') -Raw | ConvertFrom-Json
$catalogHash = (Get-FileHash -LiteralPath ($sourceRoot+'/output/catalog_'+$Version+'.json') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($endpoints.status -ne 'PASS' -or $endpoints.records.Count -ne 32 -or $endpoints.catalog_sha256 -ne $catalogHash -or $endpoints.max_endpoint_error_px -ge 0.0001) { throw '独立端点报告缺失、过期或失败。' }
if ($roundtrip.status -ne 'PASS' -or $roundtrip.records.Count -ne 16 -or $roundtrip.atlas_sha256 -ne $catalog.atlas_sha256 -or @($roundtrip.records | Where-Object { $_.differing_channels -ne 0 }).Count -gt 0) { throw '实际GPU导出对照未通过。' }
New-Item -ItemType Directory -Path $deliveryRoot -Force | Out-Null
$sourceFiles = Get-ChildItem -LiteralPath $sourceRoot -Recurse -File | Where-Object {
    $_.FullName -notmatch '[\\/]\.godot[\\/]' -and $_.Extension -notin @('.log','.uid') -and $_.Name -notmatch '^package_'
}
foreach ($sourceFile in $sourceFiles) {
    $relative = [IO.Path]::GetRelativePath($sourceRoot,$sourceFile.FullName)
    $target = Join-Path $deliveryRoot $relative
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null
    Copy-Item -LiteralPath $sourceFile.FullName -Destination $target
}
# .import参数文件保留以固定导入语义；实际缓存不打包。
$files = @(Get-ChildItem -LiteralPath $deliveryRoot -Recurse -File | ForEach-Object {
    [pscustomobject]@{path=[IO.Path]::GetRelativePath($deliveryRoot,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length}
})
[pscustomobject]@{version=$Version;revision=$Revision;status='PENDING_TA';production_ready=$false;files=$files} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($deliveryRoot+'/file_hashes.json') -Encoding utf8NoBOM
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($deliveryRoot,$archivePath)
$zip = [IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    foreach ($file in $files) {
        $entry = $zip.GetEntry($file.path)
        if ($null -eq $entry -or $entry.Length -ne $file.bytes) { throw ('条目缺失或大小错误：'+$file.path) }
        $stream=$entry.Open(); $hasher=[Security.Cryptography.SHA256]::Create()
        try { $actual=[Convert]::ToHexString($hasher.ComputeHash($stream)).ToLowerInvariant() } finally { $stream.Dispose();$hasher.Dispose() }
        if ($actual -ne $file.sha256) { throw ('条目哈希错误：'+$file.path) }
    }
    $entryCount=$zip.Entries.Count
} finally {$zip.Dispose()}
$report=[pscustomobject]@{version=$Version;status='PASS_PACKAGE_INTEGRITY_ONLY';production_ready=$false;path=$archivePath;sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant();verified_manifest_files=$files.Count;zip_entries=$entryCount;bytes=(Get-Item -LiteralPath $archivePath).Length}
$report | ConvertTo-Json | Set-Content -LiteralPath ($sourceRoot+'/qa/package_'+$deliveryTag+'.json') -Encoding utf8NoBOM
$report | ConvertTo-Json
