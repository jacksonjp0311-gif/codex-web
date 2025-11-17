# Codex Heartbeat v4.1 — Adaptive Rhythm Node
# Universal Truth Protocol (E–I–C ∿, H7=0.70)

param()

$ErrorActionPreference = "Stop"
$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"

# Paths
$SmartState = Join-Path $CodexRoot "codex\feedback\state\codex_smart_feedback_state_v4_6.json"
$HeartbeatState = Join-Path $CodexRoot "codex\feedback\state\codex_heartbeat_state_v4_1.json"

# Load Smart Feedback v4.6
$smart = Get-Content $SmartState -Raw | ConvertFrom-Json

# Determine heartbeat interval from semantic weather
$base = 300 # default 5 minutes
if ($smart.coherence_context.C_current -lt 0.45) { $interval = 420 } # slowdown
elseif ($smart.coherence_context.C_current -gt 0.70) { $interval = 180 } # speedup


# Write state
$state = @{
    ok = $true
    version = "4.1"
    timestamp = (Get-Date).ToString("s")
    hb_interval_s = $interval
    C_current = $smart.coherence_context.C_current
    C_forecast = $smart.coherence_context.C_forecast
    drift_score = $smart.coherence_context.drift_score
}
$state | ConvertTo-Json -Depth 5 | Set-Content $HeartbeatState -Encoding UTF8

# Update Task Scheduler
$cmd = Join-Path $HeartbeatDir "codex_heartbeat_runner.cmd"
$ps1 = $ScriptPath

"@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ""$ps1""" | Set-Content -Path $cmd -Encoding ASCII

schtasks /Delete /TN CodexHeartbeatV41 /F 2>$null | Out-Null
schtasks /Create /TN CodexHeartbeatV41 /SC SECOND /MO $interval /TR "$cmd" /F | Out-Null

# Autosave + Git
Set-Location $CodexRoot
git add "codex/feedback/*"
if (git status --porcelain) {
    git commit -m "Codex Heartbeat v4.1 — Adaptive Rhythm Node"
    git -c rebase.autoStash=true pull origin main --rebase
    git push origin main
}

# Return to root
Set-Location $CodexRoot

