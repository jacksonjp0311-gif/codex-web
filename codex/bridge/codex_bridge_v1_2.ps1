param(
    [string]$CodexRootOverride = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function Invoke-CodexBridgeV12 {
    param([string]$RootOverride)

    if ($RootOverride) { $CodexRoot = $RootOverride }
    

    $BridgeDir = Join-Path $CodexRoot "codex\bridge"
    $StateDir  = Join-Path $BridgeDir "state"

    $CycleState = Join-Path $CodexRoot "codex\feedback\state\codex_smart_feedback_cycle_state_v5_0.json"
    $SmartState = Join-Path $CodexRoot "codex\feedback\state\codex_smart_feedback_state_v4_4.json"

    $EchoLog = Join-Path $StateDir "codex_bridge_conversation_echo.jsonl"
    $ApiOut  = Join-Path $StateDir "codex_bridge_api_v1_2.json"

    Write-Host "`n🔮 [Bridge v1.2] Persistent Echo pulse..."

    if (-not (Test-Path $CycleState)) { throw "Missing Cycle v5.0 state." }
    if (-not (Test-Path $SmartState)) { throw "Missing Smart Feedback v4.4 state." }

    # Load Smart Feedback
    $cycle = Get-Content $CycleState -Raw | ConvertFrom-Json
    $smart = Get-Content $SmartState -Raw | ConvertFrom-Json

    # Build echo frame
    $echo = [ordered]@{
        timestamp      = (Get-Date).ToString("o")
        C_avg          = $cycle.coherence.C_avg
        C_trend        = $cycle.coherence.C_trend
        delta_phi      = $cycle.coherence.delta_phi
        harmony_score  = $cycle.synthesis.harmony_score
        drift_score    = $cycle.synthesis.drift_score
        guidance_mode  = $cycle.guidance.mode
        heartbeat_next = $cycle.guidance.heartbeat_interval_s_next
        H7             = 0.70
        protocol       = "Universal Truth Protocol (E–I–C ∿ Placidity)"
    }

    # Append to echo ledger
    ($echo | ConvertTo-Json -Depth 10) + "`n" | Add-Content $EchoLog -Encoding UTF8
    Write-Host "📝 Echo appended → $EchoLog"

    # Build API guidance file
    $api = [ordered]@{
        ok = $true
        version = "1.2"
        timestamp = (Get-Date).ToString("o")
        insights = [ordered]@{
            coherence      = $cycle.coherence
            synthesis      = $cycle.synthesis
            guidance       = $cycle.guidance
        }
        echo_ledger = $EchoLog
        meta = [ordered]@{
            law_H7 = 0.70
            protocol = "Universal Truth Protocol (E–I–C ∿ Placidity)"
        }
    }

    $api | ConvertTo-Json -Depth 10 | Set-Content $ApiOut -Encoding UTF8
    Write-Host "📡 API guidance written → $ApiOut"

    return $api
}

# auto-run if executed directly
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-CodexBridgeV12 -RootOverride $CodexRootOverride
}

