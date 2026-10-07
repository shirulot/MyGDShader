param([ValidatePattern('^v[0-9]{3}$')][string]$Version, [ValidateSet('patrol','heavy','cutter','drone')][string]$Unit='patrol', [ValidatePattern('^r[0-9]+$')][string]$Revision)
$ErrorActionPreference='Stop'
$workspaceRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sourceSuffix=if($Revision){'-'+$Revision}else{''}
$deliverySuffix=if($Revision){'_'+$Revision}else{''}
$sourceRoot=Join-Path $workspaceRoot ('art-source/ember/enemy-'+$Unit+'-actions-'+$Version+$sourceSuffix)
$deliveryRoot=Join-Path $workspaceRoot ('art-source/ember/deliveries/enemy_'+$Unit+'_actions_'+$Version+$deliverySuffix+'_2026-10-06')
$archivePath=$deliveryRoot+'.zip'
if((Test-Path -LiteralPath $deliveryRoot) -or (Test-Path -LiteralPath $archivePath)){throw '固定交付已存在，不得覆盖。'}
$catalogPath=$sourceRoot+'/output/catalog_'+$Version+'.json'
$catalog=Get-Content -LiteralPath $catalogPath -Raw | ConvertFrom-Json
$catalogHash=(Get-FileHash -LiteralPath $catalogPath -Algorithm SHA256).Hash.ToLowerInvariant()
foreach($reportName in @('verification','gpu_playback')){
    $report=Get-Content -LiteralPath ($sourceRoot+'/qa/'+$reportName+'.json') -Raw | ConvertFrom-Json
    if($report.status -ne 'PASS' -or $report.catalog_sha256 -ne $catalogHash){throw ('检查失败或版本过期：'+$reportName)}
}
# 技术PASS只验证运行/表示，正式美术状态必须由独立回执更新。
foreach($property in $catalog.actions.PSObject.Properties){
    $clip=$property.Value
    $actual=(Get-FileHash -LiteralPath ($sourceRoot+'/output/'+$property.Name+'_'+$Version+'.png') -Algorithm SHA256).Hash.ToLowerInvariant()
    if($actual -ne $clip.atlas_sha256){throw '图集已变动。'}
    if(@($clip.pixel_reports | Where-Object {$_.partial_alpha -ne 0 -or $_.edge_pixels -ne 0 -or $_.visible -eq 0}).Count -gt 0){throw '像素格式或边界检查失败。'}
}
New-Item -ItemType Directory -Path $deliveryRoot | Out-Null
Get-ChildItem -LiteralPath $sourceRoot -Recurse -File | Where-Object { $_.FullName -notmatch '[\\/]\.godot[\\/]' -and $_.Extension -notin @('.log','.uid') -and $_.Name -notmatch '^package_|^ta_submission_' } | ForEach-Object {
    $target=Join-Path $deliveryRoot ([IO.Path]::GetRelativePath($sourceRoot,$_.FullName))
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $target
}
$files=@(Get-ChildItem -LiteralPath $deliveryRoot -Recurse -File | ForEach-Object { [pscustomobject]@{path=[IO.Path]::GetRelativePath($deliveryRoot,$_.FullName).Replace('\','/');sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant();bytes=$_.Length} })
[pscustomobject]@{version=$Version;status='PENDING_TA';production_ready=$false;files=$files} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath ($deliveryRoot+'/file_hashes.json') -Encoding utf8NoBOM
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($deliveryRoot,$archivePath)
$zip=[IO.Compression.ZipFile]::OpenRead($archivePath)
try{
    foreach($file in $files){
        $entry=$zip.GetEntry($file.path)
        if($null -eq $entry -or $entry.Length -ne $file.bytes){throw 'ZIP条目缺失或大小错误。'}
        $stream=$entry.Open();$hasher=[Security.Cryptography.SHA256]::Create()
        try{$actual=[Convert]::ToHexString($hasher.ComputeHash($stream)).ToLowerInvariant()}finally{$stream.Dispose();$hasher.Dispose()}
        if($actual -ne $file.sha256){throw 'ZIP条目哈希不匹配。'}
    }
}finally{$zip.Dispose()}
$result=[pscustomobject]@{status='PASS_PACKAGE_INTEGRITY_ONLY';version=$Version;path=$archivePath;sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant();manifest_files=$files.Count;production_ready=$false}
$result | ConvertTo-Json | Set-Content -LiteralPath ($sourceRoot+'/qa/package_'+$Version+'.json') -Encoding utf8NoBOM
$result | ConvertTo-Json
