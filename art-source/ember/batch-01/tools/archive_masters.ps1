# 原样复制生成母稿；不处理像素、颜色或Alpha。
$ErrorActionPreference = 'Stop'
$generatedDirectory = Join-Path $PSScriptRoot '..\generated'
New-Item -ItemType Directory -Path $generatedDirectory -Force | Out-Null
Copy-Item -LiteralPath 'C:\Users\shiru\.codex\generated_images\01a10204-0a39-77b3-b144-9e7a03fd8e93\exec-fff053a5-4513-4485-a5e9-989260e06c3e.png' -Destination 'art-source/ember/batch-01/generated/robot_idle_down_master_v001.png'
Copy-Item -LiteralPath 'C:\Users\shiru\.codex\generated_images\01a10204-0a39-77b3-b144-9e7a03fd8e93\exec-b0f605ce-1414-4aab-8ecf-3bdf675c83e4.png' -Destination 'art-source/ember/batch-01/generated/robot_idle_down_master_v002.png'
Copy-Item -LiteralPath 'C:\Users\shiru\.codex\generated_images\01a10204-0a39-77b3-b144-9e7a03fd8e93\exec-7cca3b88-9081-48e2-9e7b-95b7835cb019.png' -Destination 'art-source/ember/batch-01/generated/station_master_v001.png'
Copy-Item -LiteralPath 'C:\Users\shiru\.codex\generated_images\01a10204-0a39-77b3-b144-9e7a03fd8e93\exec-d282fe9d-3909-4c79-8a93-816b4ba61fe0.png' -Destination 'art-source/ember/batch-01/generated/floor_clean_master_v001.png'
Copy-Item -LiteralPath 'C:\Users\shiru\.codex\generated_images\01a10204-0a39-77b3-b144-9e7a03fd8e93\exec-35a69a1f-c6c9-467d-b975-91c27a261df5.png' -Destination 'art-source/ember/batch-01/generated/floor_worn_master_v001.png'
Copy-Item -LiteralPath 'C:\Users\shiru\.codex\generated_images\01a10204-0a39-77b3-b144-9e7a03fd8e93\exec-96a197db-ba12-4731-9c39-b6f9597f4620.png' -Destination 'art-source/ember/batch-01/generated/floor_grate_master_v001.png'
Copy-Item -LiteralPath 'C:\Users\shiru\.codex\generated_images\01a10204-0a39-77b3-b144-9e7a03fd8e93\exec-0ab220d5-c87e-48cc-b53a-d1c6b2e4437a.png' -Destination 'art-source/ember/batch-01/generated/floor_wet_master_v001.png'
