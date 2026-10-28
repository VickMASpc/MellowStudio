<# Mellow Studio developer entry point. One .venv at repo root, never one per sprint.
   .\dev.ps1 run | test | build | cli info examples\mellow_hold_blink_v02.mellowzip
#>
param([Parameter(Position=0)][ValidateSet('run','test','build','cli','setup','sync')][string]$Command='run', [Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
Set-Location $PSScriptRoot
if ($Command -eq 'sync') {
  & .\scripts\sync_windows.ps1
  exit $LASTEXITCODE
}
& .\scripts\setup_windows.bat
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
switch ($Command) {
 'run' { & $python run.py @Arguments }
 'test' { & .\scripts\test_windows.bat }
 'build' { & .\scripts\build_windows.bat }
 'cli' { & $python -m mellowstudio.cli @Arguments }
 'setup' { Write-Host 'Ready: .venv' }
}
exit $LASTEXITCODE
