# ============================================================
# Codex Sync Protocol — Unified Data Commit v1.0
# Author: James Paul Jackson
# Project: The Codex Project
# Alignment: Quantum–Symbolic Triad | v3.3+
# ============================================================

& {
    $root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
    Set-Location $root

    Write-Host "?? Initiating Codex Sync Protocol..." -ForegroundColor Cyan

    $gitignorePath = "$root\.gitignore"
    $requiredLines = @(
        "`n# Allow Codex logs and handoffs to be tracked",
        "!codex/logs/**",
        "!codex/handoff/**",
        "!codex/evolution/**"
    )

    if (Test-Path $gitignorePath) {
        $gitignoreContent = Get-Content $gitignorePath -Raw
        foreach ($line in $requiredLines) {
            if ($gitignoreContent -notmatch [regex]::Escape($line.Trim())) {
                Add-Content $gitignorePath $line
            }
        }
    } else {
        Set-Content $gitignorePath ($requiredLines -join "`n")
    }

    git add -f codex/logs/ codex/handoff/ codex/evolution/ codex/core/registry.json *>$null 2>&1
    Write-Host "?? Staged Codex logs, handoffs, evolution data, and registry..." -ForegroundColor Green

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $commitMsg = "?? Codex Sync — full data + registry | $timestamp"
    git commit -m $commitMsg *>$null 2>&1
    Write-Host "?? Commit created: $commitMsg" -ForegroundColor Yellow

    git push origin main
    Write-Host "?? Sync complete — pushed to GitHub main branch." -ForegroundColor Cyan

    Set-Location $root
    Write-Host "?? Returned to Codex Root: $root" -ForegroundColor Magenta
}
# ============================================================
