param(
    [string]$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function Invoke-CodexHeartbeatV41A {
    param(
        [string]$CodexRootOverride
    )

    if ($CodexRootOverride) {
        $CodexRoot = $CodexRootOverride
    }

    $feedbackDir = Join-Path $CodexRoot "codex\feedback"
    $stateDir    = Join-Path $feedbackDir "state"

    $cycleScript = Join-Path $feedbackDir "codex_smart_feedback_cycle_v5_0.ps1"
    $cycleState  = Join-Path $stateDir "codex_smart_feedback_cycle_state_v5_0.json"

    Write-Host "`n💓 [Heartbeat v4.1A] Smart Feedback continuous pulse..."
    Write-Host "🧩 Cycle script : $cycleScript"

    if (-not (Test-Path $cycleScript)) {
        throw "Smart Feedback Cycle v5.0 script missing: $cycleScript"
    }

    . $cycleScript
    $cycle = Invoke-CodexSmartFeedbackCycleV50 -CodexRootOverride $CodexRoot

    Write-Host "🧠 [Heartbeat v4.1A] Cycle v5.0 pulse complete."

    $hbNext = $cycle.guidance.heartbeat_interval_s_next
    if (-not $hbNext) { $hbNext = 180 }

    $minutes = [Math]::Ceiling($hbNext / 60)
    if ($minutes -lt 1) { $minutes = 1 }

    Write-Host "⏱ Recommended heartbeat (s): $hbNext"
    Write-Host "→ Interval (minutes): $minutes"

    $TaskName = "CodexHeartbeatV41"
    $SelfPath = Join-Path $feedbackDir "codex_heartbeat_v4_1a.ps1"

    # ─────────────────────────────────────────────────────────────
    # FIXED SCHEDULER BLOCK — GUARANTEED WORKING
    # ─────────────────────────────────────────────────────────────

    schtasks /Query /TN $TaskName 2>$null | Out-Null
    $exists = $LASTEXITCODE -eq 0

    $escaped = '"' + "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$SelfPath`"" + '"'

    if ($exists) {
        Write-Host "🔁 Updating scheduled task interval..."
        schtasks /Change /TN $TaskName /SC MINUTE /MO $minutes /F | Out-Null
    }
    else {
        Write-Host "✨ Creating new scheduled task with safe escaping..."
        cmd.exe /c "schtasks /Create /TN $TaskName /SC MINUTE /MO $minutes /TR $escaped /F"
    }

    return $cycle
}

if ($MyInvocation.InvocationName -ne '.') {
    Invoke-CodexHeartbeatV41A -CodexRootOverride $CodexRoot
}
