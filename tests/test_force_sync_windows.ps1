# Windows integration test against a LOCAL bare remote: no GitHub/network calls.
# The checkout's literal origin is the expected GitHub URL; Git insteadOf safely
# reroutes fetches to the test bare repo. Exercises real Git reset and clean behavior.
$ErrorActionPreference = 'Stop'
$fixture = Join-Path ([System.IO.Path]::GetTempPath()) ('mellow-sync-' + [guid]::NewGuid().ToString('N'))
$remote = Join-Path $fixture 'remote.git'
$seed = Join-Path $fixture 'seed'
$work = Join-Path $fixture 'work'
$origin = 'https://github.com/VickMASpc/MellowStudio.git'

function Check([string]$step) {
    if ($LASTEXITCODE -ne 0) { throw "$step failed with exit $LASTEXITCODE" }
}

try {
    New-Item -ItemType Directory -Force -Path $fixture | Out-Null
    & git init --bare $remote | Out-Null
    Check 'Create bare remote'
    & git --git-dir=$remote symbolic-ref HEAD refs/heads/main
    Check 'Set remote default branch'
    & git init -b main $seed | Out-Null
    Check 'Initialize seed'
    & git -C $seed config user.email 'mellow-ci@example.invalid'
    & git -C $seed config user.name 'Mellow CI'
    New-Item -ItemType Directory -Path (Join-Path $seed 'scripts') | Out-Null
    Copy-Item (Join-Path $PSScriptRoot '../scripts/sync_windows.ps1') (Join-Path $seed 'scripts/sync_windows.ps1')
    Set-Content (Join-Path $seed '.gitignore') ".venv/"
    Set-Content (Join-Path $seed 'version.txt') 'old remote'
    & git -C $seed add --all
    & git -C $seed commit -m baseline | Out-Null
    Check 'Commit seed'
    & git -C $seed remote add origin $remote
    & git -C $seed push -u origin main | Out-Null
    Check 'Push seed'
    & git clone $remote $work | Out-Null
    Check 'Clone local worktree'
    # The literal origin remains GitHub and passes the production safety guard.
    # Only this test repository has a URL rewrite to the local bare remote.
    & git -C $work remote set-url origin $origin
    Check 'Set expected origin'
    $remoteUnix = $remote.Replace('\', '/')
    & git -C $work config ("url.$remoteUnix.insteadOf") $origin
    Check 'Configure offline URL rewrite'
    & git -C $work config user.email 'mellow-ci@example.invalid'
    & git -C $work config user.name 'Mellow CI'
    & git -C $work checkout -b personal-work | Out-Null
    Check 'Create local branch'
    Set-Content (Join-Path $work 'version.txt') 'local conflicting commit'
    & git -C $work add version.txt
    & git -C $work commit -m 'local commit to discard' | Out-Null
    Check 'Create local commit'
    Set-Content (Join-Path $work 'version.txt') 'uncommitted changes'
    Set-Content (Join-Path $work 'untracked-art.png') 'temporary'
    New-Item -ItemType Directory -Path (Join-Path $work '.venv') | Out-Null
    Set-Content (Join-Path $work '.venv/python.exe') 'cached environment'
    New-Item -ItemType Directory -Path (Join-Path $work 'nested') | Out-Null
    & git init (Join-Path $work 'nested') | Out-Null
    Check 'Create untracked nested repository'

    Set-Content (Join-Path $seed 'version.txt') 'NEW REMOTE'
    & git -C $seed commit -am 'new version' | Out-Null
    Check 'Commit update'
    & git -C $seed push origin main | Out-Null
    Check 'Push update'
    & pwsh -NoProfile -File (Join-Path $work 'scripts/sync_windows.ps1')
    Check 'Run force sync'

    $branch = (& git -C $work branch --show-current).Trim()
    $revision = (& git -C $work rev-parse HEAD).Trim()
    $remoteRevision = (& git -C $seed rev-parse HEAD).Trim()
    $version = (Get-Content (Join-Path $work 'version.txt') -Raw).Trim()
    $branches = @(& git -C $work branch --format='%(refname:short)')
    $remaining = @(& git -C $work status --porcelain --untracked-files=all)
    if ($branch -ne 'main' -or $revision -ne $remoteRevision -or $version -ne 'NEW REMOTE') {
        throw 'The local checkout did not become the newest remote main.'
    }
    if ($branches.Count -ne 1 -or $branches[0] -ne 'main') { throw 'Stale local branches remain.' }
    if ($remaining.Count -gt 0) { throw 'The checkout still has local file changes.' }
    foreach ($name in @('untracked-art.png','.venv','nested')) {
        if (Test-Path (Join-Path $work $name)) { throw "Force sync left $name behind." }
    }

    # The guard must refuse to touch the wrong repo before destruction.
    Set-Content (Join-Path $work 'version.txt') 'keep me'
    & git -C $work remote set-url origin 'https://github.com/other-org/other-repo.git'
    Check 'Set unrelated origin'
    & pwsh -NoProfile -File (Join-Path $work 'scripts/sync_windows.ps1') 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { throw 'Wrong origin was accepted.' }
    if ((Get-Content (Join-Path $work 'version.txt') -Raw).Trim() -ne 'keep me') {
        throw 'Failed preflight destroyed local edits.'
    }
    Write-Host 'Force-sync integration: all checks passed.'
} finally {
    if (Test-Path $fixture) { Remove-Item -LiteralPath $fixture -Recurse -Force -ErrorAction SilentlyContinue }
}
