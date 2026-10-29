# UPDATE LOCAL CODE ONLY. Fetch first, then replace tracked files with origin/main.
# Preserve .venv, untracked artwork, ignored assets and unrelated local branches.
# No git clean: deleting the user's working environment was a serious product bug.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$expected = 'VickMASpc/MellowStudio'

function Assert-Git([string]$step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$step failed (Git exit $LASTEXITCODE). Read the Git error above."
    }
}

Push-Location $repo
try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git for Windows was not found. Install Git and run sync again.'
    }
    # Git may report Windows paths with / instead of \, alternate casing, or
    # canonicalized/reparse-point paths. Comparing those path strings is brittle.
    # --show-prefix is empty only when our current directory is the Git root.
    # Never force-clean a parent repository from inside a nested directory.
    $prefix = & git rev-parse --show-prefix 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw 'This is not a Git checkout. Clone MellowStudio into this folder first.'
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$prefix)) {
        throw "MellowStudio is inside another Git checkout (relative path: '$prefix'). Refusing to wipe the parent repository."
    }

    # Use the literal configured URL; git remote get-url expands insteadOf rules.
    $origin = & git config --get remote.origin.url 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $origin) {
        throw 'The origin remote is missing. No files were touched.'
    }
    $origin = ([string]$origin).Trim()
    if ($origin -notmatch '^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/|git://github\.com/)VickMASpc/MellowStudio(?:\.git)?/?$') {
        throw "Unexpected origin '$origin'. Refusing to overwrite the wrong repository."
    }

    Write-Host '[Mellow] Checking for the newest main on GitHub...' -ForegroundColor Cyan
    # Fetch the remote first. Network/authentication failure MUST NOT erase local files.
    & git fetch --prune origin '+refs/heads/*:refs/remotes/origin/*'
    Assert-Git 'Fetch'
    & git show-ref --verify --quiet refs/remotes/origin/main
    Assert-Git 'Finding origin/main'

    Write-Host '[Mellow] Updating Mellow code to latest origin/main...' -ForegroundColor Cyan
    # Tracked source files must match GitHub, even if the user accidentally
    # edited them or has an old local commit. Keep unrelated working files.
    # This switches to main, resets tracked code and never calls git clean.
    & git checkout --force -B main refs/remotes/origin/main
    Assert-Git 'Switching to current main'
    & git reset --hard refs/remotes/origin/main
    Assert-Git 'Updating tracked code'

    $revision = (& git rev-parse --short HEAD).Trim()
    Assert-Git 'Reading updated revision'
    Write-Host "[Mellow] Updated to GitHub main at $revision." -ForegroundColor Green
    Write-Host '[Mellow] Kept .venv, artwork, exports and local branches. No dependency reinstall required.' -ForegroundColor Cyan
    exit 0
} catch {
    Write-Error "[Mellow] Force sync failed: $($_.Exception.Message)"
    exit 1
} finally {
    Pop-Location
}
