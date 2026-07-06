$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "app\backend"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$requirements = Join-Path $backend "requirements.txt"

function Test-PortAvailable {
    param([int]$Port)

    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $Port)
        $listener.Start()
        return $true
    } catch {
        return $false
    } finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

$port = 8765
while (-not (Test-PortAvailable -Port $port)) {
    $port += 1
}

$url = "http://127.0.0.1:$port"

if (-not (Test-Path $venvPython)) {
    Write-Host "Erstelle lokale Python-Umgebung..."
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv (Join-Path $root ".venv")
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv (Join-Path $root ".venv")
    } else {
        throw "Python wurde nicht gefunden. Bitte Python 3.10 oder neuer installieren."
    }
}

Write-Host "Installiere/prüfe Python-Abhängigkeiten..."
& $venvPython -m pip install -r $requirements

$localPoppler = Join-Path $root "poppler\Library\bin"
if (Test-Path $localPoppler) {
    $env:POPPLER_PATH = $localPoppler
} elseif (Test-Path "C:\Program Files\poppler\Library\bin") {
    $env:POPPLER_PATH = "C:\Program Files\poppler\Library\bin"
}

Write-Host "Starte pdf-plan-enhancer auf $url ..."
Start-Job -ScriptBlock {
    param($targetUrl)
    Start-Sleep -Seconds 2
    Start-Process $targetUrl
} -ArgumentList $url | Out-Null
Set-Location $backend
& $venvPython -m uvicorn main:app --host 127.0.0.1 --port $port
