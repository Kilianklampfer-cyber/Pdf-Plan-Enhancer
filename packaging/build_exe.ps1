$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$sourceApp = Join-Path $root "pdf-plan-enhancer-local-download"
$distRoot = Join-Path $root "output\exe-build"
$portableRoot = Join-Path $root "output\pdf-plan-enhancer-windows"
$zipPath = Join-Path $root "output\pdf-plan-enhancer-windows.zip"

if (-not (Test-Path $python)) {
    throw "Python-Umgebung nicht gefunden: $python"
}

if (Test-Path $distRoot) {
    Remove-Item -LiteralPath $distRoot -Recurse -Force
}
if (Test-Path $portableRoot) {
    Remove-Item -LiteralPath $portableRoot -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Force $distRoot | Out-Null

& $python -m PyInstaller `
    --noconfirm `
    --windowed `
    --name pdf-plan-enhancer `
    --distpath $distRoot `
    --workpath (Join-Path $root "output\pyinstaller-work") `
    --specpath (Join-Path $root "output") `
    --collect-submodules fastapi `
    --collect-submodules starlette `
    --collect-submodules pydantic `
    --collect-submodules pydantic_core `
    --hidden-import cv2 `
    --hidden-import numpy `
    --hidden-import PIL `
    --hidden-import pdf2image `
    --hidden-import img2pdf `
    --hidden-import pikepdf `
    --hidden-import python_multipart `
    --hidden-import multipart `
    --add-data "$sourceApp\app;app" `
    (Join-Path $root "packaging\launcher.py")

Copy-Item -LiteralPath (Join-Path $distRoot "pdf-plan-enhancer") -Destination $portableRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $root "pdf-plan-enhancer-local-download\README-LOCAL-APP.md") -Destination $portableRoot -Force

Compress-Archive -Path (Join-Path $portableRoot "*") -DestinationPath $zipPath -Force

Write-Host "EXE-Ordner: $portableRoot"
Write-Host "ZIP erstellt: $zipPath"
