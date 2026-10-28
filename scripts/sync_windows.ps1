# Safely synchronize one existing Mellow Studio Git checkout on Windows.
# Never resets commits, discards edits, deletes the .venv or force-pulls main.
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = 'VickMASpc/MellowStudio'
$uri = 'https://api.github.com/repos/VickMASpc/MellowStudio/pulls?state=closed&per_page=100'

function Assert-GitSuccess([string]$step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$step failed (git exit code $LASTEXITCODE). Existing files and history were not reset."
    }
}

Push-Location $repo
try {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git for Windows is not installed or cannot be found on PATH.'
    }
    $inside = (& git rev-parse --is-inside-work-tree 2>$null)
    if ($LASTEXITCODE -ne 0 -or $inside -ne 'true') {
        throw 'This folder is not a Git checkout. Clone the repository once; do not unpack a sprint ZIP.'
    }
    $origin = (& git remote get-url origin 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $origin) {
        throw 'No origin remote configured. Nothing was rewritten; expected GitHub repository VickMASpc/MellowStudio.'
    }
    # Accept GitHub HTTPS or SSH URLs for this exact repository; refuse to sync a fork or unrelated remote.
    if ($origin -notmatch '^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/|git://github\.com/)VickMASpc/MellowStudio(?:\.git)?/?$') {
        throw "Unexpected origin '$origin'. Refusing to change or fetch from an unrelated repository."
    }
    Write-Host '[Mellow] Fetching main and pruning deleted remote-tracking branches...' -ForegroundColor Cyan
    & git fetch --prune origin
    Assert-GitSuccess 'Fetch'

    $dirty = @(& git status --porcelain --untracked-files=normal)
    Assert-GitSuccess 'Worktree check'
    if ($dirty.Count -gt 0) {
        Write-Warning 'There are local changes or new files in this checkout. They are untouched. Fetch succeeded, but branch switching and pulling were skipped to avoid overwriting work.'
        & git status --short
        exit 2
    }

    & git show-ref --verify --quiet refs/heads/main
    if ($LASTEXITCODE -ne 0) {
        & git switch --track -c main origin/main
        Assert-GitSuccess 'Creating local main'
    } else {
        & git switch main
        Assert-GitSuccess 'Switching to main'
    }
    & git pull --ff-only origin main
    Assert-GitSuccess 'Fast-forwarding main'

    # A squash-merged feature branch is *not* an ancestor of main. Therefore
    # git branch -d may reject it. Delete only if the local commit SHA exactly
    # matches the historical head SHA of a completed PR, confirmed by GitHub,
    # AND the remote branch is already absent. Everything else is preserved.
    $prs = @()
    try {
        $reply = Invoke-RestMethod -Uri $uri -Headers @{ 'Accept' = 'application/vnd.github+json'; 'User-Agent' = 'MellowStudio-GitSync' } -TimeoutSec 15
        $prs = @($reply)
    } catch {
        Write-Warning 'Cannot verify merged PRs with GitHub right now. No local branches will be deleted; main is still synchronized.'
    }
    $removed = @()
    $lines = @(& git for-each-ref '--format=%(refname:short)|%(objectname)' refs/heads)
    Assert-GitSuccess 'Listing local branches'
    foreach ($line in $lines) {
        if ($line -notmatch '^(.+)\|([0-9a-f]{40})$') { continue }
        $name = $Matches[1]
        $sha = $Matches[2]
        if ($name -eq 'main') { continue }
        if ($name -notmatch '^(?:feat|fix|chore|docs)/') { continue }
        & git show-ref --verify --quiet "refs/remotes/origin/$name"
        if ($LASTEXITCODE -eq 0) { continue }
        $merged = @($prs | Where-Object {
            $_.merged_at -and $_.head.ref -eq $name -and $_.head.sha -eq $sha -and
            $_.head.repo.full_name -eq $source -and $_.base.ref -eq 'main'
        })
        if ($merged.Count -ne 1) { continue }
        & git branch -D -- $name
        if ($LASTEXITCODE -eq 0) { $removed += $name }
    }
    if ($removed.Count) { Write-Host ('[Mellow] Removed ' + $removed.Count + ' verified merged local branch(es): ' + ($removed -join ', ')) -ForegroundColor Green }
    Write-Host '[Mellow] main synchronized. Root .venv and any independent/local work are preserved.' -ForegroundColor Green
    exit 0
} finally {
    Pop-Location
}
