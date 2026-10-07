param([Parameter(Mandatory)][string]$BatchDirectory,[Parameter(Mandatory)][string]$ColdName,[string]$ReceiptVersion='v001')
# Cold unpacking writes only to a new task QA directory. Existing packages stay immutable.
$ErrorActionPreference='Stop'
$batchRoot=(Resolve-Path -LiteralPath $BatchDirectory).Path
$receipt=Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $batchRoot "qa/submission_receipt_$ReceiptVersion.json")|ConvertFrom-Json
$coldParent=[IO.Path]::GetFullPath((Join-Path $batchRoot '../qa-cold'))
$coldRoot=[IO.Path]::GetFullPath((Join-Path $coldParent $ColdName))
if(-not $coldRoot.StartsWith($coldParent+[IO.Path]::DirectorySeparatorChar)){throw 'Cold target is outside QA workspace'}
if(Test-Path -LiteralPath $coldRoot){throw 'Cold destination already exists'}
if((Get-FileHash -Algorithm SHA256 -LiteralPath $receipt.zip).Hash.ToLower() -ne $receipt.zip_sha256){throw 'ZIP hash mismatch'}
Expand-Archive -LiteralPath $receipt.zip -DestinationPath $coldRoot
$manifest=Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $coldRoot 'manifest.json')|ConvertFrom-Json
foreach($entry in $manifest.files.PSObject.Properties){
 if((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $coldRoot $entry.Name)).Hash.ToLower() -ne $entry.Value.sha256){throw "Manifest mismatch: $($entry.Name)"}
}
$godotExe='E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe'
foreach($phase in @('import','verify','capture')){
 $runArgs=if($phase -eq 'import'){@('--headless','--editor','--path',$coldRoot,'--quit')}else{@('--path',$coldRoot,'--script',"res://$phase.gd")}
 $run=Start-Process -FilePath $godotExe -ArgumentList $runArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $batchRoot "qa/cold_$phase.stdout.log") -RedirectStandardError (Join-Path $batchRoot "qa/cold_$phase.stderr.log")
 if(-not $run.WaitForExit(30000)){$run.Kill();Get-Content (Join-Path $batchRoot "qa/cold_$phase.stderr.log");throw "Own cold $phase timed out"}
 $run.Refresh()
 if($run.ExitCode -ne 0){Get-Content (Join-Path $batchRoot "qa/cold_$phase.stderr.log");throw "Cold $phase exit $($run.ExitCode)"}
 Get-Content (Join-Path $batchRoot "qa/cold_$phase.stdout.log")|Select-Object -Last 2
}
$coreCount=0
foreach($entry in $manifest.files.PSObject.Properties){
 if(-not $entry.Name.StartsWith('qa/')){
  if((Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $coldRoot $entry.Name)).Hash.ToLower() -ne $entry.Value.sha256){throw "Core changed: $($entry.Name)"}
  $coreCount++
 }
}
$gpu=Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $coldRoot 'qa/gpu_roundtrip.json')|ConvertFrom-Json
$runtime=Get-Content -Raw -Encoding utf8 -LiteralPath (Join-Path $coldRoot 'qa/runtime.json')|ConvertFrom-Json
if($gpu.status -ne 'PASS' -or $runtime.status -ne 'PASS'){throw 'Cold QA failed'}
$result=@{status='PASS';zip_sha256=$receipt.zip_sha256;cold_project=$coldRoot;payloads=@($manifest.files.PSObject.Properties).Count;core_files_unchanged=$coreCount;import='PASS';gpu=$gpu.status;runtime=$runtime.status}
$result|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $batchRoot "qa/cold_receipt_$ReceiptVersion.json") -Encoding utf8
$result|ConvertTo-Json
