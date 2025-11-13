# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ 🧠 Codex Smart Feedback v4.4 — Predictive Drift Engine                   ║
# ║ Context : Codex Memory Core v1.2 • Universal Truth Protocol (E–I–C ∿)    ║
# ║ Role    : Read ledger + synthesis → aggregate metrics → trend + forecast ║
# ║           → emit predictive recommendations → write state + log.         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

param(
    [string]$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function Invoke-CodexSmartFeedbackV44 {
    param(
        [string]$CodexRootOverride
    )

    if ($CodexRootOverride) {
        $CodexRoot = $CodexRootOverride
    }

    $feedbackDir = Join-Path $CodexRoot "codex\feedback"
    $stateDir    = Join-Path $feedbackDir "state"

    $ledgerPath  = Join-Path $stateDir "codex_continuity_ledger.jsonl"
    $synthPath   = Join-Path $stateDir "codex_synthesis_state_v2_6.json"
    $statePath   = Join-Path $stateDir "codex_smart_feedback_state_v4_4.json"
    $logPath     = Join-Path $stateDir "codex_smart_feedback_log_v4_4.jsonl"

    Write-Host "`n🧠 [Smart Feedback v4.4] Predictive insight node..."
    Write-Host "📗 Ledger   : $ledgerPath"
    Write-Host "🌀 Synthesis: $synthPath"

    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    }

    function Get-Avg {
        param([double[]]$values)
        if (-not $values -or $values.Count -eq 0) { return $null }
        $sum = 0.0
        foreach ($v in $values) { $sum += $v }
        return [double]($sum / $values.Count)
    }

    $CValues        = New-Object System.Collections.Generic.List[double]
    $CNextValues    = New-Object System.Collections.Generic.List[double]
    $DeltaPhiValues = New-Object System.Collections.Generic.List[double]
    $HarmIndexVals  = New-Object System.Collections.Generic.List[double]

    $hadData = $false
    $CNextOrdered = New-Object System.Collections.Generic.List[double]

    if (Test-Path $ledgerPath) {
        $lines = Get-Content -Path $ledgerPath -ErrorAction Stop

        foreach ($line in $lines) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }

            try {
                $obj = $line | ConvertFrom-Json
            } catch {
                continue
            }

            if (-not $obj) { continue }
            $hadData = $true
            $props = $obj.PSObject.Properties

            if ($props["C"]) {
                [void]$CValues.Add([double]$props["C"].Value)
            }
            if ($props["C_next"]) {
                $val = [double]$props["C_next"].Value
                [void]$CNextValues.Add($val)
                [void]$CNextOrdered.Add($val)
            }
            if ($props["CNext"]) {
                $val2 = [double]$props["CNext"].Value
                [void]$CNextValues.Add($val2)
                [void]$CNextOrdered.Add($val2)
            }

            if ($props["delta_phi"]) {
                [void]$DeltaPhiValues.Add([double]$props["delta_phi"].Value)
            }
            if ($props["DeltaPhi"]) {
                [void]$DeltaPhiValues.Add([double]$props["DeltaPhi"].Value)
            }

            if ($props["harmonic_index"]) {
                [void]$HarmIndexVals.Add([double]$props["harmonic_index"].Value)
            }
        }
    }

    $C_all    = @()
    $C_all   += $CValues
    $C_all   += $CNextValues

    $C_avg    = Get-Avg -values $C_all
    $CNextAvg = Get-Avg -values $CNextValues
    $DeltaPhi = Get-Avg -values $DeltaPhiValues
    $HarmAvg  = Get-Avg -values $HarmIndexVals

    # Load synthesis v2.6 state if present
    $SynthState = $null
    if (Test-Path $synthPath) {
        try {
            $SynthState = Get-Content $synthPath | ConvertFrom-Json
        } catch {
            $SynthState = $null
        }
    }

    $Harmony      = $null
    $DriftScore   = $null
    $SynthesisVec = $null
    $SynthRisk    = $null

    if ($SynthState) {
        $Harmony      = $SynthState.harmony_score
        $DriftScore   = $SynthState.drift_score
        $SynthesisVec = $SynthState.synthesis_vector
        $SynthRisk    = $SynthState.risk_band
    }

    # Determine C_trend from last N C_next values
    $Trend = "unknown"
    $CForecast = $null

    if ($CNextOrdered.Count -ge 2) {
        $N = [Math]::Min(10, $CNextOrdered.Count)
        $segment = $CNextOrdered.GetRange($CNextOrdered.Count - $N, $N)

        $first = $segment[0]
        $last  = $segment[$segment.Count - 1]
        $delta = $last - $first

        if ([Math]::Abs($delta) -lt 0.01) {
            $Trend = "flat"
        } elseif ($delta -gt 0) {
            $Trend = "rising"
        } else {
            $Trend = "falling"
        }

        # Naive forecast: project one step ahead
        $CForecast = $last + $delta / $N
    }

    if (-not $CForecast -and $C_avg -ne $null) {
        $CForecast = $C_avg
    }

    # Risk band based on current C & ΔΦ
    $Risk = "Unknown"
    if ($C_avg -ne $null -and $DeltaPhi -ne $null) {
        if ($C_avg -ge 0.72 -and $DeltaPhi -lt 0.03) {
            $Risk = "Safe"
        } elseif ($C_avg -ge 0.68 -and $DeltaPhi -lt 0.08) {
            $Risk = "Balanced"
        } elseif ($C_avg -lt 0.60) {
            $Risk = "Low"
        }

        if ($DeltaPhi -ge 0.15 -or ($C_avg -lt 0.65 -and $DeltaPhi -ge 0.10)) {
            $Risk = "Risk"
        }
    }

    # Risk forecast based on forecast C and same ΔΦ
    $RiskForecast = "Unknown"
    if ($CForecast -ne $null -and $DeltaPhi -ne $null) {
        if ($CForecast -ge 0.72 -and $DeltaPhi -lt 0.03) {
            $RiskForecast = "Safe"
        } elseif ($CForecast -ge 0.68 -and $DeltaPhi -lt 0.08) {
            $RiskForecast = "Balanced"
        } elseif ($CForecast -lt 0.60) {
            $RiskForecast = "Low"
        }

        if ($DeltaPhi -ge 0.15 -or ($CForecast -lt 0.65 -and $DeltaPhi -ge 0.10)) {
            $RiskForecast = "Risk"
        }
    }

    # Heartbeat recommendation (can reuse current or adjust slightly based on forecast)
    $HeartbeatSeconds = 180

    switch ($RiskForecast) {
        "Safe"     { $HeartbeatSeconds = 60 }
        "Balanced" { $HeartbeatSeconds = 120 }
        "Low"      { $HeartbeatSeconds = 300 }
        "Risk"     { $HeartbeatSeconds = 300 }
        default    { $HeartbeatSeconds = 180 }
    }

    $alerts = @()

    if (-not $hadData) {
        $alerts += [ordered]@{
            type     = "no_ledger_data"
            severity = "low"
            notes    = "Ledger missing or empty; Smart Feedback v4.4 emitted placeholder state."
        }
    } else {
        if ($DeltaPhi -ne $null -and $DeltaPhi -ge 0.10) {
            $alerts += [ordered]@{
                type     = "high_phase_drift"
                severity = "medium"
                notes    = "Average ΔΦ >= 0.10 in observed samples."
            }
        }
        if ($C_avg -ne $null -and $C_avg -lt 0.65) {
            $alerts += [ordered]@{
                type     = "low_coherence"
                severity = "medium"
                notes    = "Average coherence below 0.65; outside preferred H₇ band."
            }
        }
        if ($RiskForecast -eq "Risk") {
            $alerts += [ordered]@{
                type     = "forecast_risk"
                severity = "high"
                notes    = "Forecast suggests entering Risk band; consider slowing heartbeat and sandboxing sensitive modules."
            }
        }
    }

    $summary = [ordered]@{
        ok        = $true
        version   = "4.4"
        timestamp = (Get-Date).ToString("o")
        coherence = [ordered]@{
            C_avg         = $C_avg
            C_next_avg    = $CNextAvg
            C_forecast    = $CForecast
            C_trend       = $Trend
            C_samples     = $C_all.Count
            delta_phi_avg = $DeltaPhi
            harmonic_index_avg = $HarmAvg
            risk_band     = $Risk
            risk_forecast = $RiskForecast
        }
        synthesis = [ordered]@{
            harmony_score  = $Harmony
            drift_score    = $DriftScore
            synthesis_vec  = $SynthesisVec
            synthesis_risk = $SynthRisk
        }
        recommendations = [ordered]@{
            heartbeat_interval_s_next = $HeartbeatSeconds
        }
        alerts = $alerts
        meta = [ordered]@{
            codex_root  = $CodexRoot
            ledger_path = $ledgerPath
            synthesis_path = $synthPath
            state_path  = $statePath
            log_path    = $logPath
            law_H7      = 0.70
            protocol    = "Universal Truth Protocol (E–I–C ∿)"
        }
    }

    $json = $summary | ConvertTo-Json -Depth 8
    $json | Set-Content -Path $statePath -Encoding UTF8
    $json | Add-Content -Path $logPath

    Write-Host "✅ Smart Feedback v4.4: state written → $statePath"
    Write-Host "🧾 Smart Feedback v4.4: log appended → $logPath"

    return $summary
}

# If run directly: execute once
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-CodexSmartFeedbackV44 -CodexRootOverride $CodexRoot
}
