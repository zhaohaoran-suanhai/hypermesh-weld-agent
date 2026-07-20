[CmdletBinding()]
param(
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

$PythonOccPython = (Resolve-Path -LiteralPath $PythonOccPython).Path

Push-Location $repoRoot
try {
    # The full local run intentionally includes tests that exercise PythonOCC.
    & $PythonOccPython -m pytest
    if ($LASTEXITCODE -ne 0) {
        throw "pytest failed with exit code $LASTEXITCODE"
    }

    & $PythonOccPython -m weld_agent.cli doctor --pythonocc-python $PythonOccPython
    if ($LASTEXITCODE -ne 0) {
        throw "runtime doctor failed with exit code $LASTEXITCODE"
    }

    & $PythonOccPython -m weld_agent.cli validate `
        --schema integration-profile.schema.json `
        --input config\integration-probe-1.json
    if ($LASTEXITCODE -ne 0) {
        throw "integration profile validation failed with exit code $LASTEXITCODE"
    }

    git diff --check
    if ($LASTEXITCODE -ne 0) {
        throw "git diff --check failed"
    }
}
finally {
    Pop-Location
}
