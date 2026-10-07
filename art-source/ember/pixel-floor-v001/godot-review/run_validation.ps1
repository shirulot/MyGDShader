# 原生 Godot 4.7 验证；所有副本、日志与 GPU 截图位于本隔离目录。
# 不读取主项目 Game autoload，不修改原来课程状态。
param([switch]$SkipCapture)
$ErrorActionPreference = 'Stop'
$reviewRoot = $PSScriptRoot
$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $reviewRoot '../../../..')).Path
$enginePath = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
$assetRelative = 'assets/ember/environment/pixel_floor_v001'
$assetSource = Join-Path $workspaceRoot $assetRelative
$assetParent = Join-Path $reviewRoot 'assets/ember/environment'
$logsRoot = Join-Path $reviewRoot 'logs'
New-Item -ItemType Directory -Force -Path $assetParent, $logsRoot, (Join-Path $reviewRoot 'tools'), (Join-Path $reviewRoot 'scripts/ember'), (Join-Path $reviewRoot 'scenes/ember') | Out-Null
Copy-Item -LiteralPath $assetSource -Destination $assetParent -Recurse -Force
Copy-Item -LiteralPath (Join-Path $workspaceRoot 'tools/build_pixel_floor_v001.gd') -Destination (Join-Path $reviewRoot 'tools/build_pixel_floor_v001.gd') -Force
Copy-Item -LiteralPath (Join-Path $workspaceRoot 'scripts/ember/pixel_floor_painter_v001.gd') -Destination (Join-Path $reviewRoot 'scripts/ember/pixel_floor_painter_v001.gd') -Force
Copy-Item -LiteralPath (Join-Path $workspaceRoot 'scenes/ember/pixel_floor_sandbox_v001.tscn') -Destination (Join-Path $reviewRoot 'scenes/ember/pixel_floor_sandbox_v001.tscn') -Force
$stageRecords = [System.Collections.Generic.List[object]]::new()

function Run-PixelFloorStage([string]$stageName, [string[]]$engineArguments) {
    $stdoutPath = Join-Path $logsRoot ($stageName + '.stdout.log')
    $stderrPath = Join-Path $logsRoot ($stageName + '.stderr.log')
    $process = Start-Process -FilePath $enginePath -ArgumentList $engineArguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $stageRecords.Add([ordered]@{
        stage=$stageName
        arguments=$engineArguments
        exit_code=$process.ExitCode
        stdout_log=$stdoutPath.Substring($reviewRoot.Length+1).Replace('\','/')
        stderr_log=$stderrPath.Substring($reviewRoot.Length+1).Replace('\','/')
        stderr_bytes=(Get-Item -LiteralPath $stderrPath).Length
    })
    $stageRecords | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $reviewRoot 'stage-exits.json') -Encoding utf8
    Write-Output ($stageName + ' exit=' + $process.ExitCode)
    if ($process.ExitCode -ne 0 -or (Get-Item -LiteralPath $stderrPath).Length -ne 0) {
        Get-Content -LiteralPath $stderrPath
        throw ('Godot verification failed: ' + $stageName)
    }
}

Run-PixelFloorStage 'builder-syntax' @('--headless','--path',$reviewRoot,'--script','res://tools/build_pixel_floor_v001.gd','--check-only')
Run-PixelFloorStage 'painter-syntax' @('--headless','--path',$reviewRoot,'--script','res://scripts/ember/pixel_floor_painter_v001.gd','--check-only')
Run-PixelFloorStage 'headless-validation' @('--headless','--path',$reviewRoot,'--script','res://tools/build_pixel_floor_v001.gd')
if (-not $SkipCapture) {
    Run-PixelFloorStage 'gpu-validation' @('--path',$reviewRoot,'--script','res://tools/build_pixel_floor_v001.gd','--','--capture')
}
$isolatedAssets = Join-Path $reviewRoot $assetRelative
Get-ChildItem -LiteralPath $isolatedAssets -File | Where-Object { $_.Name -match '_terrain_v001\.tres$|^engine_validation\.json$|^gpu_.*\.png$|^validation_layout_v001\.json$' } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $assetSource $_.Name) -Force
}
Copy-Item -LiteralPath (Join-Path $reviewRoot 'scenes/ember/pixel_floor_sandbox_v001.tscn') -Destination (Join-Path $workspaceRoot 'scenes/ember/pixel_floor_sandbox_v001.tscn') -Force
$report = Get-Content -LiteralPath (Join-Path $assetSource 'engine_validation.json') -Raw | ConvertFrom-Json
Write-Output ($report.status + ' checked_cells=' + $report.checked_cells + ' landing_cases=' + $report.landing_cases + ' GPU=' + $report.gpu_captures.Count)
