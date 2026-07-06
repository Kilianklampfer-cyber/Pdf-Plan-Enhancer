$ErrorActionPreference = "Stop"

$workspace = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $workspace "frontend"
$nodeBin = "C:\Users\klk\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin"
$pnpm = "C:\Users\klk\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\pnpm.cmd"

if (-not (Test-Path $pnpm)) {
    Write-Host "Gebündeltes pnpm wurde nicht gefunden. Bitte Node.js installieren und dann im Frontend 'npm install' und 'npm run dev' ausführen."
    exit 1
}

$env:Path = "$nodeBin;$env:Path"
Set-Location $frontend

& $pnpm run dev -- --host 127.0.0.1 --port 5173
