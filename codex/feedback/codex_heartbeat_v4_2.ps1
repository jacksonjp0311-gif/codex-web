# Codex Heartbeat v4.2 — Auto-Anchoring Adaptive Rhythm Node
param()

$ErrorActionPreference = "Stop"

$CodexRoot     = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$HeartbeatDir  = Join-Path $CodexRoot "codex\feedback"
$ScriptPath    = Join-Path $HeartbeatDir "codex_heartbeat_v4_2.ps1"
$StatePath     = Join-Path $HeartbeatDir "state\codex_heartbeat_state_v4_2.json"
$SmartState    = Join-Path $HeartbeatDir "state\codex_smart_feedback_state_v4_6.json"

# Load smart feedback
$smart = Get-Content $SmartState -Raw | ConvertFrom-Json

# Determine heartbeat interval
$base = 300
if ($smart.coherence_context.C_current -lt 0.45) {
    $interval = 420
}
if ($smart.coherence_context.C_current -ge 0.45 -and $smart.coherence_context.C_current -le 0.70) {
    $interval = $base
}
if ($smart.coherence_context.C_current -gt 0.70) {
    $interval = 180
}

# Write heartbeat state
$state = @{
    ok             = $true
    version        = "4.2"
    timestamp      = (Get-Date).ToString("s")
    hb_interval_s  = $interval
    C_current      = $smart.coherence_context.C_current
    C_forecast     = $smart.coherence_context.C_forecast
    drift_score    = $smart.coherence_context.drift_score
}
$state | ConvertTo-Json -Depth 5 | Set-Content -Path $StatePath -Encoding UTF8

# Git autosave
Set-Location $CodexRoot
git add "codex/feedback/*"
if (git status --porcelain) {
    git commit -m "Heartbeat v4.2 — Adaptive Rhythm Node $(Get-Date -Format yyyyMMdd_HHmmss)"
    git -c rebase.autoStash=true pull origin main --rebase
    git push origin main
}

Set-Location $CodexRoot
