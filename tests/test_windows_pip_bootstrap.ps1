# Windows smoke test: a pip-less Python environment must self-repair.
# Run against an isolated disposable path with spaces and parentheses.
$ErrorActionPreference = 'Stop'
$fixture = Join-Path ([System.IO.Path]::GetTempPath()) ('Mellow setup (8) ' + [guid]::NewGuid().ToString('N'))
$venv = Join-Path $fixture 'existing environment'
$venvPython = Join-Path $venv 'Scripts/python.exe'
$helper = Join-Path $PSScriptRoot '../scripts/ensure_pip_windows.bat'
function Assert-Exit([string]$step) {
    if ($LASTEXITCODE -ne 0) { throw "$step failed (exit $LASTEXITCODE)" }
}
try {
    New-Item -ItemType Directory -Force -Path $fixture | Out-Null
    & python -m venv --without-pip $venv
    Assert-Exit 'Create pip-less virtual environment'
    & $venvPython -m pip --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { throw 'The test environment unexpectedly already has pip.' }

    & $helper $venvPython
    Assert-Exit 'Automatic pip repair'
    & $venvPython -m pip --version
    Assert-Exit 'Verify repaired pip'

    & $helper $venvPython
    Assert-Exit 'Second idempotent setup'

    & $helper (Join-Path $fixture 'missing/python.exe') | Out-Null
    if ($LASTEXITCODE -eq 0) { throw 'Bootstrap silently accepted missing Python.' }

    Write-Host 'Pip bootstrap: missing pip repaired, rerun idempotent, invalid environment rejected.'
} finally {
    if (Test-Path $fixture) {
        Remove-Item -LiteralPath $fixture -Recurse -Force -ErrorAction SilentlyContinue
    }
}
