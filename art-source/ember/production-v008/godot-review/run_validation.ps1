# 仅操作当前独立目录；GUI Godot隐藏启动，仍保存真实GPU读回。
$ErrorActionPreference = 'Stop'
$reviewRoot = $PSScriptRoot
$enginePath = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
$logRoot = Join-Path $reviewRoot 'logs'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$stageRecords = [System.Collections.Generic.List[object]]::new()

function Run-ReviewStage([string]$stageName, [string[]]$engineArguments) {
    $stdoutPath = Join-Path $logRoot ($stageName + '.stdout.log')
    $stderrPath = Join-Path $logRoot ($stageName + '.stderr.log')
    $process = Start-Process -FilePath $enginePath -ArgumentList $engineArguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $stageRecords.Add([ordered]@{
        stage=$stageName
        engine_arguments=$engineArguments
        exit_code=$process.ExitCode
        stdout_log=($stdoutPath.Substring($reviewRoot.Length+1).Replace('\','/'))
        stderr_log=($stderrPath.Substring($reviewRoot.Length+1).Replace('\','/'))
        stdout_sha256=(Get-FileHash -LiteralPath $stdoutPath -Algorithm SHA256).Hash.ToLowerInvariant()
        stderr_sha256=(Get-FileHash -LiteralPath $stderrPath -Algorithm SHA256).Hash.ToLowerInvariant()
        stderr_bytes=(Get-Item -LiteralPath $stderrPath).Length
    })
    $stageRecords | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $reviewRoot 'stage-exits.json') -Encoding utf8
    if ($process.ExitCode -ne 0) {
        Get-Content -LiteralPath $stderrPath
        throw ('Godot stage failed: ' + $stageName)
    }
    if ((Get-Item -LiteralPath $stderrPath).Length -ne 0) {
        Get-Content -LiteralPath $stderrPath
        throw ('Godot stage emitted stderr: ' + $stageName)
    }
}

Run-ReviewStage 'initial-import' @('--headless','--path',$reviewRoot,'--editor','--import')
# 导入策略仅在独立副本的.import上修改，不给official源文件增加sidecar。
$importFiles = Get-ChildItem -LiteralPath (Join-Path $reviewRoot 'inputs') -Filter '*.png.import'
$policy = [ordered]@{
    'compress/mode'='0'
    'compress/normal_map'='2'
    'roughness/mode'='1'
    'detect_3d/compress_to'='0'
    'mipmaps/generate'='false'
    'process/fix_alpha_border'='false'
    'process/premult_alpha'='false'
    'process/normal_map_invert_y'='false'
}
foreach ($importFile in $importFiles) {
    $content = Get-Content -LiteralPath $importFile.FullName -Raw
    foreach ($key in $policy.Keys) {
        $pattern = '(?m)^' + [regex]::Escape($key) + '=.*$'
        if ([regex]::Matches($content,$pattern).Count -ne 1) { throw ('Unexpected import key: ' + $key) }
        $content = [regex]::Replace($content,$pattern,($key + '=' + $policy[$key]))
    }
    [System.IO.File]::WriteAllText($importFile.FullName,$content,[System.Text.UTF8Encoding]::new($false))
}
Run-ReviewStage 'policy-import' @('--headless','--path',$reviewRoot,'--editor','--import')
Run-ReviewStage 'syntax' @('--headless','--path',$reviewRoot,'--script','res://validate.gd','--check-only')
Run-ReviewStage 'gpu-validation' @('--path',$reviewRoot,'--script','res://validate.gd','--','--capture')
$report = Get-Content -LiteralPath (Join-Path $reviewRoot 'validation.json') -Raw | ConvertFrom-Json
Write-Output ($report.status + ' checked_cells=' + $report.checked_cells + ' GPU=' + $report.gpu_captures.Count)
