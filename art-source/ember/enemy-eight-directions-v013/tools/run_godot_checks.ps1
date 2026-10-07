param([Parameter(Mandatory=$true)][string]$BatchDirectory,[Parameter(Mandatory=$true)][string[]]$Scripts)
$ErrorActionPreference = 'Stop'
$batch = (Resolve-Path -LiteralPath $BatchDirectory).Path
$engine = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe'
foreach ($script in $Scripts) {
    $label = [IO.Path]::GetFileNameWithoutExtension($script)
    $stdout = Join-Path $batch "qa/$label-stdout.log"
    $stderr = Join-Path $batch "qa/$label-stderr.log"
    $process = Start-Process -FilePath $engine -ArgumentList @('--path', $batch, '--script', "res://$script") -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if (-not $process.WaitForExit(30000)) {
        Stop-Process -Id $process.Id
        throw "Timed out: $script (stopped only this process)"
    }
    Get-Content -LiteralPath $stdout -Tail 3
    $errors = Get-Content -LiteralPath $stderr -Raw
    if ($errors) { Write-Output $errors }
    if ($process.ExitCode -ne 0 -or $errors -match 'SCRIPT ERROR|Parse Error') { throw "Godot failed: $script" }
}
