$ErrorActionPreference = "Stop"

$workspace = Split-Path -Parent $PSScriptRoot
$outputDir = Join-Path $workspace "output"
$stagingDir = Join-Path $outputDir ("pdf-plan-enhancer-share-" + [guid]::NewGuid().ToString("N"))
$zipPath = Join-Path $outputDir "pdf-plan-enhancer-share.zip"

$excludedNames = @(
    ".git",
    ".agents",
    ".codex",
    ".vscode",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    ".workspace",
    "temp_pdf_workspace",
    "output"
)

$excludedExtensions = @(".pyc", ".log", ".zip")

New-Item -ItemType Directory -Force $outputDir | Out-Null
New-Item -ItemType Directory -Force $stagingDir | Out-Null

Get-ChildItem -LiteralPath $workspace -Recurse -File -Force | Where-Object {
    $relative = $_.FullName.Substring($workspace.Length).TrimStart("\", "/")
    $parts = $relative -split "[\\/]+"
    -not ($parts | Where-Object { $excludedNames -contains $_ }) -and
    -not ($excludedExtensions -contains $_.Extension)
} | ForEach-Object {
    $relative = $_.FullName.Substring($workspace.Length).TrimStart("\", "/")
    $target = Join-Path $stagingDir $relative
    $targetDir = Split-Path -Parent $target
    New-Item -ItemType Directory -Force $targetDir | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $target -Force
}

if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $zipPath -Force
Remove-Item -LiteralPath $stagingDir -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "ZIP erstellt: $zipPath"
