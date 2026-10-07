# 在独立项目已有导入策略之后运行；只保存本目录里的真实GPU截图和日志。
$ErrorActionPreference = 'Stop'
$bankReviewRoot = $PSScriptRoot
$bankEnginePath = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
$bankOutputLog = Join-Path $bankReviewRoot 'logs/bank-gpu.stdout.log'
$bankErrorLog = Join-Path $bankReviewRoot 'logs/bank-gpu.stderr.log'
$bankArguments = @('--path',$bankReviewRoot,'--script','res://capture_bank.gd')
$bankProcess = Start-Process -FilePath $bankEnginePath -ArgumentList $bankArguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $bankOutputLog -RedirectStandardError $bankErrorLog
[ordered]@{
    stage='bank-gpu'
    exit_code=$bankProcess.ExitCode
    stdout_log='logs/bank-gpu.stdout.log'
    stderr_log='logs/bank-gpu.stderr.log'
    stderr_bytes=(Get-Item -LiteralPath $bankErrorLog).Length
    stdout_sha256=(Get-FileHash -LiteralPath $bankOutputLog -Algorithm SHA256).Hash.ToLowerInvariant()
    stderr_sha256=(Get-FileHash -LiteralPath $bankErrorLog -Algorithm SHA256).Hash.ToLowerInvariant()
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $bankReviewRoot 'bank-stage-exit.json') -Encoding utf8
if ($bankProcess.ExitCode -ne 0 -or (Get-Item -LiteralPath $bankErrorLog).Length -ne 0) {
    Get-Content -LiteralPath $bankErrorLog
    throw 'Bank GPU capture failed.'
}
Get-Content -LiteralPath $bankOutputLog
