# 发布模板：sync脚本复制到独立工程根目录后执行；可用-GodotPath指定其它电脑的Godot。
param([string]$GodotPath = 'E:\steam\steamapps\common\Godot Engine\godot.windows.opt.tools.64.exe')
if (-not (Test-Path -LiteralPath $GodotPath)) { throw '请用 -GodotPath 指定 Godot 可执行文件。' }
$taskProject = $PSScriptRoot
$logFolder = Join-Path $taskProject 'validation-logs'
New-Item -ItemType Directory -Path $logFolder -Force | Out-Null
# 冷启动先导入PNG和脚本，然后只运行独立结构验收。
$importTask = Start-Process -FilePath $GodotPath -ArgumentList @('--headless','--import','--path',('"' + $taskProject + '"')) -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logFolder 'import.stdout.log') -RedirectStandardError (Join-Path $logFolder 'import.stderr.log')
if ($importTask.ExitCode -ne 0) { throw 'Godot import failed; inspect validation-logs/import.stderr.log.' }
$validationTask = Start-Process -FilePath $GodotPath -ArgumentList @('--headless','--path',('"' + $taskProject + '"'),'--script','res://tools/validate_reference_floor_v004.gd') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput (Join-Path $logFolder 'validation.stdout.log') -RedirectStandardError (Join-Path $logFolder 'validation.stderr.log')
Get-Content -LiteralPath (Join-Path $logFolder 'validation.stdout.log')
Get-Content -LiteralPath (Join-Path $logFolder 'validation.stderr.log')
if ($validationTask.ExitCode -ne 0) { throw "Structural validation failed, exit $($validationTask.ExitCode)." }
