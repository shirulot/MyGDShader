# 自包含交付：只复制已保存文件，排除本机 .godot / PNG 导入缓存。
# 必须先完成结构验收与 GPU 实拼审阅，再运行本脚本。
param([string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot))
$reviewRoot = Join-Path $WorkspaceRoot 'art-source\ember\reference-floor-v003\godot-review'
$deliveryRoot = Join-Path $WorkspaceRoot 'art-source\ember\deliveries\reference_floor_v003_2026-10-06'
$archivePath = $deliveryRoot + '.zip'
$reportPath = Join-Path $reviewRoot 'assets\ember\environment\reference_floor_v003\independent_validation_v003.json'
if (-not (Test-Path -LiteralPath $reportPath)) { throw '缺少独立验收结果；不打包未验证的候选资源。' }
$validationResult = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
if ($validationResult.status -ne 'PASS' -or $validationResult.failures.Count -ne 0) { throw '独立验收尚未完整通过；先修复再打包。' }
$gpuReportPath = Join-Path $reviewRoot 'assets\ember\environment\reference_floor_v003\gpu_capture_v003.json'
if (-not (Test-Path -LiteralPath $gpuReportPath)) { throw '缺少实际GPU动态刷擦结果。' }
$gpuResult = Get-Content -LiteralPath $gpuReportPath -Raw | ConvertFrom-Json
if ($gpuResult.status -ne 'PASS') { throw '实际GPU动态刷擦尚未通过；不打包未完成验证的资源。' }
# 仅重建本脚本生成的交付目录；源工程始终保留在 reviewRoot。
# 再次运行时清掉冷启动验证产生的缓存，避免把它们写进ZIP和哈希清单。
$resolvedDeliveryParent = [IO.Path]::GetFullPath((Join-Path $WorkspaceRoot 'art-source\ember\deliveries'))
$resolvedDeliveryRoot = [IO.Path]::GetFullPath($deliveryRoot)
if ([IO.Path]::GetDirectoryName($resolvedDeliveryRoot) -ne $resolvedDeliveryParent -or [IO.Path]::GetFileName($resolvedDeliveryRoot) -ne 'reference_floor_v003_2026-10-06') { throw '交付目录越界，拒绝重建。' }
if (Test-Path -LiteralPath $resolvedDeliveryRoot) {
    if ((Get-Item -LiteralPath $resolvedDeliveryRoot).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw '交付目录是链接，拒绝递归清理。' }
    Remove-Item -LiteralPath $resolvedDeliveryRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $deliveryRoot -Force | Out-Null
$copiedCount = 0
Get-ChildItem -LiteralPath $reviewRoot -Recurse -File | Where-Object {
    $relativeName = [IO.Path]::GetRelativePath($reviewRoot,$_.FullName)
    $relativeName -notmatch '(^|[\\/])\.godot([\\/]|$)' -and
    $relativeName -notmatch '(^|[\\/])validation-logs([\\/]|$)' -and
    $_.Extension -notin @('.import','.log')
} | ForEach-Object {
    $relativeName = [IO.Path]::GetRelativePath($reviewRoot,$_.FullName)
    $targetPath = Join-Path $deliveryRoot $relativeName
    New-Item -ItemType Directory -Path (Split-Path -Parent $targetPath) -Force | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $targetPath -Force
    $copiedCount++
}
$hashEntries = @(Get-ChildItem -LiteralPath $deliveryRoot -Recurse -File | Where-Object { $_.Name -ne 'file_hashes.json' } | ForEach-Object {
    @{path=([IO.Path]::GetRelativePath($deliveryRoot,$_.FullName) -replace '\\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower();bytes=$_.Length}
})
@{revision='reference_floor_v003';files=$hashEntries} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $deliveryRoot 'file_hashes.json') -Encoding utf8
Compress-Archive -LiteralPath @(Get-ChildItem -LiteralPath $deliveryRoot | Select-Object -ExpandProperty FullName) -DestinationPath $archivePath -CompressionLevel Optimal -Force
$archiveHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLower()
Write-Output "DELIVERY_SAVED: $deliveryRoot"
Write-Output "ARCHIVE_SAVED: $archivePath"
Write-Output "FILES: $copiedCount; ARCHIVE_SHA256: $archiveHash"

