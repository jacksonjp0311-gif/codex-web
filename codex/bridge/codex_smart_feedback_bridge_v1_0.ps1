param(
    [string]$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function Invoke-CodexSmartFeedbackBridgeV10 {
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

    $SmartV44Path = Join-Path $stateDir "codex_smart_feedback_state_v4_4.json"
    $ApiOutPath   = Join-Path $bridgeState "codex_smart_feedback_api_v1.json"

    Write-Host "`n🧠 [Bridge v1.0] Exporting Smart Feedback → AI API JSON..."
    Write-Host "📄 Smart v4.4 : $SmartV44Path"
    Write-Host "📡 API out    : $ApiOutPath"

    if (-not (Test-Path $SmartV44Path)) {
        throw "Smart Feedback v4.4 state missing: $SmartV44Path"
    }
    if (-not (Test-Path $bridgeState)) {
        New-Item -ItemType Directory -Path $bridgeState -Force | Out-Null
    }

    $sf = Get-Content $SmartV44Path | ConvertFrom-Json

    $C   = $sf.coherence.C_avg
    $Cnext = $sf.coherence.C_next_avg
    $Cforecast = $sf.coherence.C_forecast
    $trend = $sf.coherence.C_trend
    $deltaPhi = $sf.coherence.delta_phi_avg
    $harmIdx  = $sf.coherence.harmonic_index_avg
    $riskCurrent   = $sf.coherence.risk_band
    $riskForecast  = $sf.coherence.risk_forecast

    $harmony   = $sf.synthesis.harmony_score
    $drift     = $sf.synthesis.drift_score
    $synthRisk = $sf.synthesis.synthesis_risk

    $hbNext = $sf.recommendations.heartbeat_interval_s_next

    # Compact guidance object for backend AI
    $guidance = [ordered]@{
        ok        = $sf.ok
        version   = $sf.version
        timestamp = $sf.timestamp

        coherence = [ordered]@{
            C_avg        = $C
            C_next_avg   = $Cnext
            C_forecast   = $Cforecast
            C_trend      = $trend
            delta_phi    = $deltaPhi
            harmonic_idx = $harmIdx
            risk         = $riskCurrent
            risk_forecast = $riskForecast
        }

        synthesis = [ordered]@{
            harmony_score = $harmony
            drift_score   = $drift
            risk          = $synthRisk
        }

        operations = [ordered]@{
            heartbeat_interval_s_next = $hbNext
        }

        # This is *explicitly* for API/meta use
        hints = [ordered]@{
            mode = "codex-guided"
            note = "Use these metrics as context when deciding intensity, pacing, and risk posture."
        }
    }

    $guidance | ConvertTo-Json -Depth 8 | Set-Content -Path $ApiOutPath -Encoding UTF8

    Write-Host "✅ Bridge v1.0: API guidance written → $ApiOutPath"

    return $guidance
}

# Direct execution path
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-CodexSmartFeedbackBridgeV10 -CodexRootOverride $CodexRoot
}
