# 收集UI及真实地图依赖到独立冷工程；不复制主工程设置、不覆盖历史ZIP。
param([string]$Revision = 'v004')
$ErrorActionPreference = 'Stop'
$uiSourceRoot = (Get-Location).Path
$uiStage = Join-Path $uiSourceRoot "art-source/ember/ui-interactions-v004/review-build-$Revision"
New-Item -ItemType Directory -Path $uiStage -Force | Out-Null
Set-Content -LiteralPath (Join-Path $uiStage '.gdignore') -Value ''
$uiFiles = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$uiQueue = [System.Collections.Generic.Queue[string]]::new()
function Add-UiFile([string]$relative) {
    $relative = $relative.Replace('\','/')
    if ($relative.Contains('..') -or $relative.StartsWith('/') -or $relative.Contains(':')) { return }
    if ((Test-Path -LiteralPath (Join-Path $uiSourceRoot $relative) -PathType Leaf) -and $uiFiles.Add($relative)) { $uiQueue.Enqueue($relative) }
}
foreach ($folder in @('scripts/ember/ui_edge_v001','scripts/ember/ui_edge_v004','scenes/ember/ui_edge_v001','scenes/ember/ui_edge_v004','assets/ember/ui_final/skins')) {
    Get-ChildItem -LiteralPath (Join-Path $uiSourceRoot $folder) -File -Recurse | ForEach-Object { Add-UiFile $_.FullName.Substring($uiSourceRoot.Length+1) }
}
foreach ($file in @('assets/ember/ui_final/ui.tscn','assets/ember/ui_final/demo.tscn','scenes/ember/ui_edge_interactive_v004.tscn','scripts/ember/ui_edge_preview_v001.gd','scripts/ember/ui_edge_binding_v001.gd',
    'tools/validate_ui_interactions_v004.gd','tools/capture_ui_interactions_v004.gd','tools/probe_ui_interaction_navigation_v004.gd',
    'tools/validate_ui_edge_logic_v001.gd','tools/validate_ui_edge_reuse_v002.gd','tools/validate_ui_edge_lifecycle_v003.gd',
    'tools/validate_ui_edge_ta_regression_v003.gd','tools/probe_ui_edge_widget_v002.gd','tools/probe_ui_edge_layout_v002.gd',
    'art-source/ember/ui-edge-v001/selected_reference.png','docs/shader-learning/ta-art-review-standard-v001.md',
    'art-source/ember/ui-interactions-v004/README.md')) { Add-UiFile $file }
while ($uiQueue.Count -gt 0) {
    $relative = $uiQueue.Dequeue()
    $source = Join-Path $uiSourceRoot $relative
    $destination = Join-Path $uiStage $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination -Force
    if ([IO.Path]::GetExtension($relative) -in @('.gd','.tscn','.tres')) {
        foreach ($match in [regex]::Matches((Get-Content -LiteralPath $source -Raw),'res://[A-Za-z0-9_./-]+')) {
            $dependency = $match.Value.Substring(6)
            if (-not $dependency.StartsWith('art-source/')) { Add-UiFile $dependency }
        }
    }
    if ([IO.Path]::GetExtension($relative) -eq '.png') { Add-UiFile ($relative + '.import') }
    if ([IO.Path]::GetExtension($relative) -eq '.gd') { Add-UiFile ($relative + '.uid') }
}
$uiProject = @'
config_version=5
[application]
config/name="Ember UI Interaction Review"
run/main_scene="res://assets/ember/ui_final/demo.tscn"
config/features=PackedStringArray("4.7")
[display]
window/size/viewport_width=720
window/size/viewport_height=720
window/stretch/mode="canvas_items"
[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
'@
Set-Content -LiteralPath (Join-Path $uiStage 'project.godot') -Value $uiProject -Encoding utf8
New-Item -ItemType Directory -Path (Join-Path $uiStage 'art-source/ember/ui-edge-v001') -Force | Out-Null
# 这里只登记从工作区复制的输入。冷工程执行生成的证据在冻结时单独加入manifest。
$inputs = @($uiFiles | Sort-Object | ForEach-Object { [pscustomobject]@{path=$_;sha256=(Get-FileHash -LiteralPath (Join-Path $uiStage $_) -Algorithm SHA256).Hash.ToLowerInvariant()} })
[ordered]@{revision=$Revision;inputs=$inputs;main_project_unchanged=$true} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $uiStage 'input-manifest.json') -Encoding utf8
[pscustomobject]@{stage=$uiStage;input_files=$inputs.Count}
