param([ValidatePattern('^v[0-9]{3}$')][string]$Version)
$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$sourceRoot = Join-Path $workspaceRoot ('art-source/ember/enemy-patrol-move-' + $Version)
$rig = Get-Content -LiteralPath ($sourceRoot+'/rig.json') -Raw | ConvertFrom-Json
$catalogPath = $sourceRoot+'/output/catalog_'+$Version+'.json'
$catalog = Get-Content -LiteralPath $catalogPath -Raw | ConvertFrom-Json
$records = @()
# 用导出登记的实际矩阵映射原始骨端，独立于姿态求解器重算误差。
foreach ($pose in $catalog.poses) {
    foreach ($part in ($rig.parts | Where-Object { $null -ne $_.end })) {
        $matrix = $pose.part_transforms.($part.id)
        $restX = $part.end[0] - $part.pivot[0]
        $restY = $part.end[1] - $part.pivot[1]
        $actualX = $matrix.position[0]+$matrix.basis_x[0]*$restX+$matrix.basis_y[0]*$restY
        $actualY = $matrix.position[1]+$matrix.basis_x[1]*$restX+$matrix.basis_y[1]*$restY
        $side = $part.id.Split('_')[0]
        $targetPoint = if ($part.id.EndsWith('_thigh')) { $pose.legs.$side.knee_px } else { $pose.legs.$side.ankle_px }
        $endpointError = [Math]::Sqrt([Math]::Pow($actualX-$targetPoint[0],2)+[Math]::Pow($actualY-$targetPoint[1],2))
        if (-not [double]::IsFinite($endpointError)) { throw '非有限端点误差。' }
        $records += [pscustomobject]@{frame=$pose.frame;part=$part.id;actual=@($actualX,$actualY);target=$targetPoint;error_px=$endpointError}
    }
}
$maximum = ($records | Measure-Object -Property error_px -Maximum).Maximum
if ($records.Count -ne 32 -or $maximum -ge 0.0001) { throw '端点验证失败，不得打包。' }
$report = [pscustomobject]@{status='PASS';mapped_segments=$records.Count;max_endpoint_error_px=$maximum;catalog_sha256=(Get-FileHash -LiteralPath $catalogPath -Algorithm SHA256).Hash.ToLowerInvariant();scope='Actual recorded node matrices; not visual volume approval';records=$records}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath ($sourceRoot+'/qa/endpoint_mapping.json') -Encoding utf8NoBOM
$report | Select-Object status,mapped_segments,max_endpoint_error_px,catalog_sha256 | ConvertTo-Json
