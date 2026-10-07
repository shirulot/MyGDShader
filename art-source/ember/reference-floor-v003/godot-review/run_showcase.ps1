param(
    [string]$GodotPath = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe',
    [ValidateSet('mixed','control','service','rust')][string]$Map = 'mixed'
)
if (-not (Test-Path -LiteralPath $GodotPath)) { throw '请用 -GodotPath 指定 Godot 可执行文件。' }
# ZIP 不携带 .godot；等待首次资源导入结束，再打开交互场景。
$logFolder = Join-Path $PSScriptRoot 'validation-logs'
New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
$importTask = Start-Process -FilePath $GodotPath -ArgumentList @('--headless','--import','--path',('"' + $PSScriptRoot + '"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logFolder 'showcase_import.stdout.log') -RedirectStandardError (Join-Path $logFolder 'showcase_import.stderr.log')
if ($importTask.ExitCode -ne 0) { throw '首次导入失败；请检查 validation-logs/showcase_import.stderr.log。' }
$scenePath = if ($Map -eq 'mixed') { 'res://scenes/ember/reference_floor_sandbox_v003.tscn' } else { 'res://scenes/ember/reference_floor_' + $Map + '_sandbox_v003.tscn' }
# 用户执行启动脚本时打开选定地图供实际铺刷。
& $GodotPath --path $PSScriptRoot $scenePath
