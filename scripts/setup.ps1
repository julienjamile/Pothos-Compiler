$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
$Python = Get-Command python -ErrorAction Stop
$Npm = Get-Command npm -ErrorAction Stop

& $Python.Source -m venv (Join-Path $RootDir ".venv")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
& $VenvPython -m pip install -r (Join-Path $RootDir "requirements.txt")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $Npm.Source --prefix $RootDir ci
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }