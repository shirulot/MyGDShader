param(
    [Parameter(Mandatory = $true)][string]$GodotPath,
    [string]$ApiPath = ''
)
$ErrorActionPreference = 'Stop'
# 在临时目录导出当前引擎 API，不向课程目录写入大型 API 文件。
if (-not $ApiPath) {
    $dumpDir = Join-Path ([IO.Path]::GetTempPath()) ('godot-completion-' + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $dumpDir | Out-Null
    $process = Start-Process -FilePath $GodotPath -ArgumentList '--headless', '--dump-extension-api' -WorkingDirectory $dumpDir -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw 'Godot API export failed.' }
    $ApiPath = Join-Path $dumpDir 'extension_api.json'
}
$api = Get-Content -LiteralPath $ApiPath -Raw | ConvertFrom-Json
$builtins = @{}
foreach ($type in $api.builtin_classes) {
    $builtins[$type.name] = @{
        constants = @($type.constants | Where-Object { $null -ne $_ })
        members = @($type.members | Where-Object { $null -ne $_ })
        methods = @($type.methods | Where-Object { $null -ne $_ } | ForEach-Object {
            @{ name = $_.name; return_type = $_.return_type; is_static = $_.is_static; arguments = @($_.arguments | Where-Object { $null -ne $_ } | Select-Object name, type) }
        })
    }
}
$index = @{
    engine = $api.header.version_full_name
    global_enums = $api.global_enums
    global_constants = $api.global_constants
    builtins = $builtins
}
$destination = Join-Path $PSScriptRoot '../api_index.json'
$index | ConvertTo-Json -Depth 15 -Compress | Set-Content -LiteralPath $destination -Encoding utf8NoBOM
Write-Output "Generated $destination from $($api.header.version_full_name)"
