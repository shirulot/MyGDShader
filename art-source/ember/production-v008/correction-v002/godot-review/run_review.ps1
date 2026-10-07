# 独立项目导入与真实GPU检查；所有日志与.import只写当前目录。
$ErrorActionPreference = 'Stop'
$reviewRoot = $PSScriptRoot
$enginePath = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
$logRoot = Join-Path $reviewRoot 'logs'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$records = [System.Collections.Generic.List[object]]::new()

function Run-PilotStage([string]$stageName, [string[]]$engineArguments) {
    $stdoutPath = Join-Path $logRoot ($stageName + '.stdout.log')
    $stderrPath = Join-Path $logRoot ($stageName + '.stderr.log')
    $process = Start-Process -FilePath $enginePath -ArgumentList $engineArguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $records.Add([ordered]@{stage=$stageName; exit_code=$process.ExitCode; stderr_bytes=(Get-Item -LiteralPath $stderrPath).Length; engine_arguments=$engineArguments})
    $records | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $reviewRoot 'stage-exits.json') -Encoding utf8
    if ($process.ExitCode -ne 0 -or (Get-Item -LiteralPath $stderrPath).Length -ne 0) {
        Get-Content -LiteralPath $stderrPath
        throw ('Godot stage failed: ' + $stageName)
    }
}

Run-PilotStage 'initial-import' @('--headless','--path',$reviewRoot,'--editor','--import')
$importPath = Join-Path $reviewRoot 'inputs/pilot_samples.png.import'
$content = Get-Content -LiteralPath $importPath -Raw
$policy = [ordered]@{'compress/mode'='0'; 'compress/normal_map'='2'; 'roughness/mode'='1'; 'detect_3d/compress_to'='0'; 'mipmaps/generate'='false'; 'process/fix_alpha_border'='false'; 'process/premult_alpha'='false'}
foreach ($key in $policy.Keys) {
    $pattern = '(?m)^' + [regex]::Escape($key) + '=.*$'
    if ([regex]::Matches($content, $pattern).Count -ne 1) { throw ('Unexpected import key: ' + $key) }
    $content = [regex]::Replace($content, $pattern, ($key + '=' + $policy[$key]))
}
[System.IO.File]::WriteAllText($importPath, $content, [System.Text.UTF8Encoding]::new($false))
Run-PilotStage 'policy-import' @('--headless','--path',$reviewRoot,'--editor','--import')
Run-PilotStage 'syntax' @('--headless','--path',$reviewRoot,'--script','res://review.gd','--check-only')
Run-PilotStage 'gpu-capture' @('--path',$reviewRoot,'--','--capture')
Get-Content -LiteralPath (Join-Path $reviewRoot 'validation.json') -Raw
