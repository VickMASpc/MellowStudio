# FORCE REFRESH. Destructive by design: local edits, untracked/ignored files,
# virtual environment and local branches are erased. Keeps .git and remote history.
# Fetch must succeed and the origin must match before any local data is deleted.
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
    $root = & git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $root) {
        throw 'This is not a Git checkout. Clone MellowStudio into this folder first.'
    }
    $actualRoot = [System.IO.Path]::GetFullPath([string]$root).TrimEnd('\', '/')
    $scriptRoot = [System.IO.Path]::GetFullPath($repo).TrimEnd('\', '/')
    if (-not [string]::Equals($actualRoot, $scriptRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'The script is not running from the MellowStudio repository root.'
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

    Write-Warning 'FORCE SYNC: deleting local edits, untracked AND ignored files (including .venv and unsaved projects stored here), and local branches. Remote GitHub files are NOT deleted.'
    # -B moves/creates main directly at the freshly fetched remote tip;
    # -f discards conflicting working-tree and index edits, even on another branch.
    & git checkout --force -B main refs/remotes/origin/main
    Assert-Git 'Replacing local main'
    & git reset --hard refs/remotes/origin/main
    Assert-Git 'Resetting tracked files'
    # Two -f flags include nested repositories, -x includes .gitignore entries.
    # The primary .git directory is deliberately preserved by Git.
    & git clean -ffdx
    Assert-Git 'Removing all untracked and ignored files'

    # Obsolete local branches cause confusion even after GitHub removes the remote ones.
    # This is intentionally destructive: user explicitly chose force-sync.
    $branches = @(& git for-each-ref '--format=%(refname:short)' refs/heads)
    Assert-Git 'Listing local branches'
    foreach ($name in $branches) {
        if (-not $name -or $name -eq 'main') { continue }
        & git branch -D -- $name
        Assert-Git "Deleting local branch '$name'"
    }

    $revision = (& git rev-parse --short HEAD).Trim()
    Assert-Git 'Reading updated revision'
    Write-Host "[Mellow] Ready: latest origin/main at $revision. Local checkout is clean." -ForegroundColor Green
    Write-Host '[Mellow] .venv was removed; start_windows.bat will recreate it as needed.' -ForegroundColor Cyan
    exit 0
} catch {
    Write-Error "[Mellow] Force sync failed: $($_.Exception.Message)"
    exit 1
} finally {
    Pop-Location
}
