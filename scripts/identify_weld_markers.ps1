[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputManifest,
    [string]$PythonOccPython = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($PythonOccPython)) {
    $PythonOccPython = $env:WELD_AGENT_PYTHONOCC_PYTHON
}

if ([string]::IsNullOrWhiteSpace($PythonOccPython)) {
    throw "Set WELD_AGENT_PYTHONOCC_PYTHON or pass -PythonOccPython"
}

if (-not (Test-Path -LiteralPath $PythonOccPython -PathType Leaf)) {
    throw "PythonOCC interpreter not found: $PythonOccPython"
}

if (-not (Test-Path -LiteralPath $InputManifest -PathType Leaf)) {
    throw "Marker input manifest not found: $InputManifest"
}

$PythonOccPython = (Resolve-Path -LiteralPath $PythonOccPython).Path
$InputManifest = (Resolve-Path -LiteralPath $InputManifest).Path

Push-Location $repoRoot
try {
    & $PythonOccPython -m weld_agent.cli identify-markers --manifest $InputManifest
    if ($LASTEXITCODE -ne 0) {
        throw "marker identification failed with exit code $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}
