$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Virtual environment not found. Run scripts/setup.ps1 first."
}

Set-Location $RootDir
& $VenvPython (Join-Path $RootDir "app.py")
exit $LASTEXITCODE