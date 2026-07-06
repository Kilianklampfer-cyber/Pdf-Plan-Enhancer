$ErrorActionPreference = "Stop"

$workspace = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $workspace "backend"
$python = Join-Path $workspace ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Python-Umgebung wurde nicht gefunden: $python"
    exit 1
}

$env:POPPLER_PATH = "C:\Program Files\poppler\Library\bin"
Set-Location $backend

& $python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
