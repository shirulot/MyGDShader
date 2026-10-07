param([ValidatePattern('^v[0-9]{3}$')][string]$Version='v012')
$ErrorActionPreference='Stop'
$workspaceRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sourceRoot=Join-Path $workspaceRoot ('art-source/ember/enemy-sequences-'+$Version)
$archivePath=Join-Path $workspaceRoot ('art-source/ember/deliveries/enemy_sequences_'+$Version+'_2026-10-06.zip')
if(Test-Path -LiteralPath $archivePath){throw '固定汇总包已存在，不能覆盖。'}
# 最终封包必须有20条明确TA回执，不能用汇总技术测试替代美术批准。
$acceptance=Get-Content ($sourceRoot+'/TA_ACCEPTANCE.json') -Raw|ConvertFrom-Json
if($acceptance.status -ne 'PASS' -or $acceptance.approved_clip_count -ne 20 -or @($acceptance.clips).Count -ne 20){throw '20条TA验收尚未完成。'}
if(@($acceptance.clips|Where-Object {$_.verdict -ne 'PASS'}).Count -ne 0){throw '存在未通过动作。'}
if(@($acceptance.clips|ForEach-Object {$_.unit+'/'+$_.action}|Sort-Object -Unique).Count -ne 20){throw '动作范围重复或缺失。'}
$recipePath=$sourceRoot+'/assembly_recipe.json'
$recipeHash=(Get-FileHash $recipePath).Hash.ToLowerInvariant()
foreach($reportName in @('assembly_integrity','assembly_runtime')){
 $report=Get-Content ($sourceRoot+'/qa/'+$reportName+'.json') -Raw|ConvertFrom-Json
 if($report.status -ne 'PASS' -or $report.recipe_sha256 -ne $recipeHash){throw ('汇总验证过期或失败：'+$reportName)}
}
$recipe=Get-Content $recipePath -Raw|ConvertFrom-Json
foreach($clip in $recipe.clips){
 $actual=(Get-FileHash ($sourceRoot+'/'+$clip.atlas.Replace('res://',''))).Hash.ToLowerInvariant()
 if($actual -ne $clip.atlas_sha256){throw ('汇总图集像素已改动：'+$clip.unit+'/'+$clip.action)}
 $actual=(Get-FileHash ($sourceRoot+'/reviewed_packages/'+$clip.reviewed_zip)).Hash.ToLowerInvariant()
 if($actual -ne $clip.reviewed_zip_sha256){throw '来源固定ZIP已变化。'}
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$files=@(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File|Where-Object {$_.FullName -notmatch '[\\/]\.godot[\\/]' -and $_.Extension -notin @('.log','.uid') -and $_.Name -notmatch '^(file_hashes|package_receipt)'}|ForEach-Object{
 [pscustomobject]@{path=[IO.Path]::GetRelativePath($sourceRoot,$_.FullName).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash.ToLowerInvariant();bytes=$_.Length}
})
@{version=$Version;scope='4 units x 5 down actions; 120 frames; art assets only';ta_status='PASS';files=$files}|ConvertTo-Json -Depth 10|Set-Content ($sourceRoot+'/file_hashes.json') -Encoding utf8NoBOM
$zip=[IO.Compression.ZipFile]::Open($archivePath,[IO.Compression.ZipArchiveMode]::Create)
try{
 foreach($file in $files){[IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,(Join-Path $sourceRoot $file.path),$file.path,[IO.Compression.CompressionLevel]::Optimal)|Out-Null}
 [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip,($sourceRoot+'/file_hashes.json'),'file_hashes.json',[IO.Compression.CompressionLevel]::Optimal)|Out-Null
}finally{$zip.Dispose()}
# 逐项打开ZIP流核对，避免只验证封包前目录。
$zip=[IO.Compression.ZipFile]::OpenRead($archivePath)
try{
 if($zip.Entries.Count -ne $files.Count+1){throw 'ZIP条目数错误。'}
 foreach($file in $files){
  $entry=$zip.GetEntry($file.path)
  if($null -eq $entry -or $entry.Length -ne $file.bytes){throw ('ZIP条目不完整：'+$file.path)}
  $stream=$entry.Open();$hasher=[Security.Cryptography.SHA256]::Create()
  try{$hash=[Convert]::ToHexString($hasher.ComputeHash($stream)).ToLowerInvariant()}finally{$stream.Dispose();$hasher.Dispose()}
  if($hash -ne $file.sha256){throw ('ZIP内容校验失败：'+$file.path)}
 }
}finally{$zip.Dispose()}
$receipt=[ordered]@{status='TA_APPROVED_ART_ASSEMBLY';scope='down/front only, 20 clips, 120 frames';version=$Version;zip=$archivePath;zip_sha256=(Get-FileHash $archivePath).Hash.ToLowerInvariant();manifest_files=$files.Count;zip_entries=$files.Count+1}
$receipt|ConvertTo-Json -Depth 8|Set-Content ($sourceRoot+'/qa/package_receipt.json') -Encoding utf8
$receipt|ConvertTo-Json -Depth 8
