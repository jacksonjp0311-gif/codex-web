param(
    [string]$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function Invoke-CodexSmartFeedbackCycleV50 {
    param(
        [string]$CodexRootOverride
    )

    if ($CodexRootOverride) {
        $CodexRoot = $CodexRootOverride
    }

    $feedbackDir = Join-Path $CodexRoot "codex\feedback"
    $stateDir    = Join-Path $feedbackDir "state"

    $bridgeDir   = Join-Path $CodexRoot "codex\bridge"
    $bridgeState = Join-Path $bridgeDir "state"

    $SmartV44Script = Join-Path $feedbackDir "codex_smart_feedback_v4_4.ps1"
    $BridgeScript   = Join-Path $bridgeDir   "codex_smart_feedback_bridge_v1_0.ps1"

    $SmartV44State  = Join-Path $stateDir    "codex_smart_feedback_state_v4_4.json"
    $BridgeApiPath  = Join-Path $bridgeState "codex_smart_feedback_api_v1.json"
    $CycleStatePath = Join-Path $stateDir    "codex_smart_feedback_cycle_state_v5_0.json"

    Write-Host "`n🧠 [Cycle v5.0] Live evolution pulse..."
    Write-Host "🧩 Smart v4.4 script : $SmartV44Script"
    Write-Host "🧩 Bridge v1.0 script: $BridgeScript"

    if (-not (Test-Path $SmartV44Script)) {
        throw "Smart Feedback v4.4 script missing: $SmartV44Script"
    }
    if (-not (Test-Path $BridgeScript)) {
        throw "Smart Feedback Bridge v1.0 script missing: $BridgeScript"
    }
    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    }
    if (-not (Test-Path $bridgeState)) {
        New-Item -ItemType Directory -Path $bridgeState -Force | Out-Null
    }

    # Load modules (no auto-run)
    . $SmartV44Script
    . $BridgeScript

    # 1) Run Smart Feedback v4.4 (predictive drift)
    $sfSummary = Invoke-CodexSmartFeedbackV44 -CodexRootOverride $CodexRoot

    # 2) Run Bridge v1.0 (API guidance export)
    $bridgeSummary = Invoke-CodexSmartFeedbackBridgeV10 -CodexRootOverride $CodexRoot

    Write-Host "🧠 [Cycle v5.0] Smart Feedback + Bridge pulse complete."

    # Extract core metrics
    $C_avg       = $sfSummary.coherence.C_avg
    $C_forecast  = $sfSummary.coherence.C_forecast
    $C_trend     = $sfSummary.coherence.C_trend
    $DeltaPhi    = $sfSummary.coherence.delta_phi_avg
    $RiskNow     = $sfSummary.coherence.risk_band
    $RiskForecast = $sfSummary.coherence.risk_forecast

    $Harmony     = $sfSummary.synthesis.harmony_score
    $DriftScore  = $sfSummary.synthesis.drift_score
    $SynthRisk   = $sfSummary.synthesis.synthesis_risk

    $HBNext      = $bridgeSummary.operations.heartbeat_interval_s_next
    $GuidanceMode = $bridgeSummary.hints.mode

    $timestamp = (Get-Date).ToString("o")

    $cycle = [ordered]@{
        ok        = $true
        version   = "5.0"
        timestamp = $timestamp

        coherence = [ordered]@{
            C_avg        = $C_avg
            C_forecast   = $C_forecast
            C_trend      = $C_trend
            delta_phi    = $DeltaPhi
            risk_current = $RiskNow
            risk_forecast = $RiskForecast
        }

        synthesis = [ordered]@{
            harmony_score = $Harmony
            drift_score   = $DriftScore
            risk          = $SynthRisk
        }

        guidance = [ordered]@{
            heartbeat_interval_s_next = $HBNext
            mode                      = $GuidanceMode
            api_guidance_path         = $BridgeApiPath
        }

        links = [ordered]@{
            smart_feedback_state = $SmartV44State
            bridge_api_state     = $BridgeApiPath
        }

        meta = [ordered]@{
            codex_root = $CodexRoot
            law_H7     = 0.70
            protocol   = "Universal Truth Protocol (E–I–C ∿)"
            note       = "Single evolution pulse combining Smart Feedback v4.4 + Bridge v1.0."
        }
    }

    $cycle | ConvertTo-Json -Depth 8 | Set-Content -Path $CycleStatePath -Encoding UTF8
    Write-Host "🌀 [Cycle v5.0] State written → $CycleStatePath"

    return $cycle
}

# Direct execution
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-CodexSmartFeedbackCycleV50 -CodexRootOverride $CodexRoot
}
