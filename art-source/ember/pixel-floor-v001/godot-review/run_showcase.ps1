# 独立实际场景展示：设备保持原生 Sprite 尺寸，不加载主游戏 autoload。
$ErrorActionPreference = 'Stop'
$reviewRoot = $PSScriptRoot
$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $reviewRoot '../../../..')).Path
$enginePath = 'E:/steam/steamapps/common/Godot Engine/godot.windows.opt.tools.64.exe'
$assetRelative = 'assets/ember/environment/pixel_floor_v001'
$assetSource = Join-Path $workspaceRoot $assetRelative
$assetParent = Join-Path $reviewRoot 'assets/ember/environment'
Copy-Item -LiteralPath $assetSource -Destination $assetParent -Recurse -Force
New-Item -ItemType Directory -Force -Path (Join-Path $reviewRoot 'assets/ember/characters/robot'),(Join-Path $reviewRoot 'assets/ember/buildings/station') | Out-Null
Copy-Item -LiteralPath (Join-Path $workspaceRoot 'assets/ember/characters/robot/robot_idle_down_v001.png') -Destination (Join-Path $reviewRoot 'assets/ember/characters/robot/robot_idle_down_v001.png') -Force
Copy-Item -LiteralPath (Join-Path $workspaceRoot 'assets/ember/buildings/station/station_base_v001.png') -Destination (Join-Path $reviewRoot 'assets/ember/buildings/station/station_base_v001.png') -Force
Copy-Item -LiteralPath (Join-Path $workspaceRoot 'tools/capture_pixel_floor_showcase_v001.gd') -Destination (Join-Path $reviewRoot 'tools/capture_pixel_floor_showcase_v001.gd') -Force
$stdoutPath = Join-Path $reviewRoot 'logs/showcase.stdout.log'
$stderrPath = Join-Path $reviewRoot 'logs/showcase.stderr.log'
$process = Start-Process -FilePath $enginePath -ArgumentList @('--path',$reviewRoot,'--script','res://tools/capture_pixel_floor_showcase_v001.gd') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
if ($process.ExitCode -ne 0 -or (Get-Item -LiteralPath $stderrPath).Length -ne 0) {
    Get-Content -LiteralPath $stderrPath
    throw 'GPU showcase failed'
}
Get-ChildItem -LiteralPath (Join-Path $reviewRoot $assetRelative) -File | Where-Object { $_.Name -match '^gpu_scene_showcase_.*\.png$|^showcase_validation\.json$' } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $assetSource $_.Name) -Force
}
Copy-Item -LiteralPath (Join-Path $reviewRoot 'scenes/ember/pixel_floor_showcase_v001.tscn') -Destination (Join-Path $workspaceRoot 'scenes/ember/pixel_floor_showcase_v001.tscn') -Force
Get-Content -LiteralPath (Join-Path $assetSource 'showcase_validation.json')
