$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot
$Npm = Get-Command npm -ErrorAction Stop

& $Npm.Source --prefix $RootDir run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }