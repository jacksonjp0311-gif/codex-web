# Codex All-One v2.6 — Core Orchestrator
param()

$ErrorActionPreference = "Stop"

$CodexRoot    = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir  = Join-Path $CodexRoot "codex\feedback"
$StateDir     = Join-Path $FeedbackDir "state"

$HeartbeatScript   = Join-Path $FeedbackDir "codex_heartbeat_v4_2.ps1"
$MemoryWeaveScript = Join-Path $FeedbackDir "codex_memory_weave_v2_0.ps1"
$ContinuityScript  = Join-Path $FeedbackDir "codex_continuity_synth_v2_1.ps1"

function Invoke-CodexNode {
    param(
        [string]$Name,
        [string]$Path
    )

    Write-Host ""
    Write-Host "[All-One v2.6] Node: $Name"

    if (-not $Path -or -not (Test-Path $Path)) {
        Write-Host "  → Missing: $Path"
        return
    }

    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $Path
    } catch {
        Write-Host "  → Node failed: $($_.Exception.Message)"
    }
}

Invoke-CodexNode -Name "Heartbeat v4.2" -Path $HeartbeatScript
Invoke-CodexNode -Name "Memory Weave v2.0" -Path $MemoryWeaveScript
Invoke-CodexNode -Name "Continuity Synth v2.1" -Path $ContinuityScript

Set-Location $CodexRoot
git add "codex/feedback/*"
git add "codex/orchestrator/*"

if (git status --porcelain) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    git commit -m "Codex All-One v2.6 cycle $stamp"
    git -c rebase.autoStash=true pull origin main --rebase
    git push origin main
}

Set-Location $CodexRoot
Write-Host "All-One v2.6 complete."
