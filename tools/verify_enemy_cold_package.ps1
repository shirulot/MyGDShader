param([ValidatePattern('^v[0-9]{3}$')][string]$Version, [ValidateSet('patrol','heavy','cutter','drone')][string]$Unit='patrol', [ValidatePattern('^r[0-9]+$')][string]$Revision)
$ErrorActionPreference='Stop'
$workspaceRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sourceSuffix=if($Revision){'-'+$Revision}else{''}
$deliverySuffix=if($Revision){'_'+$Revision}else{''}
$sourceRoot=Join-Path $workspaceRoot ('art-source/ember/enemy-'+$Unit+'-actions-'+$Version+$sourceSuffix)
$coldRoot=Join-Path $workspaceRoot ('art-source/ember/enemy-'+$Unit+'-actions-'+$Version+$sourceSuffix+'-coldcheck')
$archivePath=Join-Path $workspaceRoot ('art-source/ember/deliveries/enemy_'+$Unit+'_actions_'+$Version+$deliverySuffix+'_2026-10-06.zip')
if(Test-Path -LiteralPath $coldRoot){throw '冷检目录已存在；保留旧证据，不覆盖。'}
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::ExtractToDirectory($archivePath,$coldRoot)
$qaRoot=$sourceRoot+'/qa'
$logs=@()
foreach($stage in @('import','capture')){
    $arguments=if($stage -eq 'import'){@('--headless','--path',$coldRoot,'--editor','--import')}else{@('--path',$coldRoot,'--script','res://capture.gd')}
    # 超时仅终止此处新建的子进程，避免错误脚本让审阅过程无限等待。
    $process=Start-Process -FilePath 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe' -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput ($qaRoot+'/cold_'+$stage+'.log') -RedirectStandardError ($qaRoot+'/cold_'+$stage+'.stderr.log')
    if(-not $process.WaitForExit(30000)){$process.Kill();throw ('冷检超时：'+$stage)}
    if($process.ExitCode -ne 0 -or (Get-Item -LiteralPath ($qaRoot+'/cold_'+$stage+'.stderr.log')).Length -gt 0){throw ('冷检失败，请查看日志：'+$stage)}
    foreach($suffix in @('.log','.stderr.log')){
        $path=$qaRoot+'/cold_'+$stage+$suffix
        $logs+=[pscustomobject]@{path=$path;bytes=(Get-Item -LiteralPath $path).Length;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
    }
}
$gpuPath=$coldRoot+'/qa/gpu_playback.json'
$gpu=Get-Content -LiteralPath $gpuPath -Raw | ConvertFrom-Json
$catalogHash=(Get-FileHash -LiteralPath ($coldRoot+'/output/catalog_'+$Version+'.json') -Algorithm SHA256).Hash.ToLowerInvariant()
if($gpu.status -ne 'PASS' -or $gpu.catalog_sha256 -ne $catalogHash){throw '实际冷播放未通过或未绑定当前catalog。'}
$manifest=Get-Content -LiteralPath ($coldRoot+'/file_hashes.json') -Raw | ConvertFrom-Json
$core=@()
foreach($file in $manifest.files){
    if($file.path -like 'qa/*' -or $file.path.EndsWith('.import')){continue}
    $actual=(Get-FileHash -LiteralPath ($coldRoot+'/'+$file.path) -Algorithm SHA256).Hash.ToLowerInvariant()
    if($actual -ne $file.sha256){throw ('运行后核心源/资源变动：'+$file.path)}
    $core+=[pscustomobject]@{path=$file.path;sha256=$actual;zip_manifest_equal=$true}
}
$report=[pscustomobject]@{status='PASS';scope='Fresh ZIP directory import and real GPU playback; producer evidence only';cold_workspace=$coldRoot;zip_path=$archivePath;zip_sha256=(Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant();import_exit=0;capture_exit=0;actual_playback_report=$gpuPath;playback_report_sha256=(Get-FileHash -LiteralPath $gpuPath -Algorithm SHA256).Hash.ToLowerInvariant();gpu=$gpu;core_files=$core;logs=$logs}
$reportPath=$qaRoot+'/cold_receipt_'+$Version+'.json'
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding utf8NoBOM
[pscustomobject]@{status='PASS';receipt=$reportPath;sha256=(Get-FileHash -LiteralPath $reportPath -Algorithm SHA256).Hash.ToLowerInvariant();verified_core_files=$core.Count} | ConvertTo-Json
