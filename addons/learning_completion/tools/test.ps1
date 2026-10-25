param([Parameter(Mandatory = $true)][string]$GodotPath)
$ErrorActionPreference = 'Stop'
$testDir = Join-Path ([IO.Path]::GetTempPath()) ('learning-completion-test-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path "$testDir/addons/integration_runner" -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot '..') -Destination "$testDir/addons/learning_completion" -Recurse
@'
config_version=5
[application]
config/name="Learning Completion Tests"
[editor_plugins]
enabled=PackedStringArray("res://addons/learning_completion/plugin.cfg", "res://addons/integration_runner/plugin.cfg")
[rendering]
renderer/rendering_method="gl_compatibility"
'@ | Set-Content "$testDir/project.godot"
@'
[plugin]
name="Integration Runner"
description="Temporary test harness"
author="Shader Learning"
version="1.0"
script="runner.gd"
'@ | Set-Content "$testDir/addons/integration_runner/plugin.cfg"
Copy-Item (Join-Path $PSScriptRoot '../tests/editor_integration.gd') "$testDir/addons/integration_runner/runner.gd"
'extends Node' | Set-Content "$testDir/fixture.gd"

function Invoke-GodotTest([string]$Name, [string[]]$TestArguments) {
    $stdout = Join-Path $testDir "$Name.log"
    $stderr = Join-Path $testDir "$Name-errors.log"
    # 隐藏临时测试进程，避免抢占正在上课的编辑器窗口。
    $process = Start-Process -FilePath $GodotPath -ArgumentList $TestArguments -WorkingDirectory $testDir -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if (-not $process.WaitForExit(45000)) {
        $process.Kill()
        throw "$Name timed out. Logs: $testDir"
    }
    $process.WaitForExit()
    Get-Content $stdout
    Get-Content $stderr
    if ($process.ExitCode -ne 0 -or (Select-String -Path $stderr -Pattern 'SCRIPT ERROR:|ERROR:' -Quiet)) {
        throw "$Name failed. Logs: $testDir"
    }
}
Invoke-GodotTest 'provider' @('--headless', '--path', $testDir, '--script', 'res://addons/learning_completion/tests/test_provider.gd')
Invoke-GodotTest 'editor' @('--headless', '--editor', '--path', $testDir)
Write-Output "All tests passed. Logs: $testDir"
