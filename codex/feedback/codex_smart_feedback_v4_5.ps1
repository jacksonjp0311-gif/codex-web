param(
    [string]$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function Invoke-CodexSmartFeedbackV45 {
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

    $CycleStatePath = Join-Path $stateDir "codex_smart_feedback_cycle_state_v5_0.json"
    $Smart44State   = Join-Path $stateDir "codex_smart_feedback_state_v4_4.json"
    $EchoLogPath    = Join-Path $bridgeState "codex_bridge_conversation_echo.jsonl"

    $StatePathV45   = Join-Path $stateDir "codex_smart_feedback_state_v4_5.json"
    $LogPathV45     = Join-Path $stateDir "codex_smart_feedback_log_v4_5.jsonl"

    Write-Host "`n🧠 [Smart Feedback v4.5] Semantic Drift Engine..."
    Write-Host "📄 Cycle v5.0 state : $CycleStatePath"
    Write-Host "📄 Smart v4.4 state : $Smart44State"
    Write-Host "📄 Echo ledger      : $EchoLogPath"

    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    }

    # Helper: average
    function Get-Avg {
        param([double[]]$values)
        if (-not $values -or $values.Count -eq 0) { return $null }
        $sum = 0.0
        foreach ($v in $values) { $sum += $v }
        return [double]($sum / $values.Count)
    }

    # Helper: standard deviation
    function Get-Std {
        param([double[]]$values)
        if (-not $values -or $values.Count -lt 2) { return $null }
        $mean = Get-Avg -values $values
        $sumSq = 0.0
        foreach ($v in $values) {
            $diff = $v - $mean
            $sumSq += $diff * $diff
        }
        return [double][Math]::Sqrt($sumSq / ($values.Count - 1))
    }

    # ─────────────────────────────────────────────────────────
    # 1) LOAD BASE STATES (CYCLE + SMART v4.4)
    # ─────────────────────────────────────────────────────────
    $cycle  = $null
    $smart  = $null

    if (Test-Path $CycleStatePath) {
        try { $cycle = Get-Content $CycleStatePath -Raw | ConvertFrom-Json } catch { $cycle = $null }
    }
    if (Test-Path $Smart44State) {
        try { $smart = Get-Content $Smart44State -Raw | ConvertFrom-Json } catch { $smart = $null }
    }

    # ─────────────────────────────────────────────────────────
    # 2) LOAD ECHO LEDGER WINDOW
    # ─────────────────────────────────────────────────────────
    $EchoEntries = New-Object System.Collections.Generic.List[object]
    $windowSize  = 32

    $hadEcho = $false

    if (Test-Path $EchoLogPath) {
        $lines = Get-Content -Path $EchoLogPath
        # Take last N lines
        $startIndex = [Math]::Max(0, $lines.Count - $windowSize)
        for ($i = $startIndex; $i -lt $lines.Count; $i++) {
            $line = $lines[$i]
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            try {
                $obj = $line | ConvertFrom-Json
                if ($obj) {
                    $EchoEntries.Add($obj) | Out-Null
                    $hadEcho = $true
                }
            } catch {
                continue
            }
        }
    }

    # ─────────────────────────────────────────────────────────
    # 3) COLLECT SERIES FOR DRIFT METRICS
    # ─────────────────────────────────────────────────────────
    $CSeries       = New-Object System.Collections.Generic.List[double]
    $HarmonySeries = New-Object System.Collections.Generic.List[double]
    $DriftSeries   = New-Object System.Collections.Generic.List[double]
    $DeltaPhiSeries = New-Object System.Collections.Generic.List[double]
    $HBSeries      = New-Object System.Collections.Generic.List[double]
    $ModeCounts    = @{}

    foreach ($e in $EchoEntries) {
        $props = $e.PSObject.Properties

        if ($props["C_avg"]) {
            [void]$CSeries.Add([double]$props["C_avg"].Value)
        }
        if ($props["harmony_score"]) {
            [void]$HarmonySeries.Add([double]$props["harmony_score"].Value)
        }
        if ($props["drift_score"]) {
            [void]$DriftSeries.Add([double]$props["drift_score"].Value)
        }
        if ($props["delta_phi"]) {
            [void]$DeltaPhiSeries.Add([double]$props["delta_phi"].Value)
        }
        if ($props["heartbeat_next"]) {
            [void]$HBSeries.Add([double]$props["heartbeat_next"].Value)
        }
        if ($props["guidance_mode"] -and $props["guidance_mode"].Value) {
            $mode = [string]$props["guidance_mode"].Value
            if (-not $ModeCounts.ContainsKey($mode)) {
                $ModeCounts[$mode] = 0
            }
            $ModeCounts[$mode]++
        }
    }

    $C_mean   = Get-Avg -values $CSeries
    $C_std    = Get-Std -values $CSeries
    $H_mean   = Get-Avg -values $HarmonySeries
    $H_std    = Get-Std -values $HarmonySeries
    $D_mean   = Get-Avg -values $DriftSeries
    $D_std    = Get-Std -values $DriftSeries
    $Phi_mean = Get-Avg -values $DeltaPhiSeries
    $Phi_std  = Get-Std -values $DeltaPhiSeries
    $HB_mean  = Get-Avg -values $HBSeries

    $C_trend = "unknown"
    $C_delta = $null

    if ($CSeries.Count -ge 2) {
        $first = $CSeries[0]
        $last  = $CSeries[$CSeries.Count - 1]

        $C_delta = $last - $first
        if ([Math]::Abs($C_delta) -lt 0.01) {
            $C_trend = "flat"
        } elseif ($C_delta -gt 0) {
            $C_trend = "rising"
        } else {
            $C_trend = "falling"
        }
    }

    # "Semantic drift" index here = combination of:
    # - coherence volatility (C_std)
    # - phase volatility (Phi_std)
    # - drift-score volatility (D_std)
    # Normalized into [0,1] band heuristically.
    $semDrift = $null
    if ($C_std -ne $null -or $Phi_std -ne $null -or $D_std -ne $null) {
        $cTerm  = (if ($C_std  -ne $null) { $C_std  } else { 0.0 })
        $pTerm  = (if ($Phi_std -ne $null) { $Phi_std } else { 0.0 })
        $dTerm  = (if ($D_std -ne $null) { $D_std } else { 0.0 })

        # Heuristic scaling
        $raw = $cTerm * 1.5 + [Math]::Abs($pTerm) * 4.0 + $dTerm * 2.0
        if ($raw -lt 0) { $raw = 0 }
        if ($raw -gt 1) { $raw = 1 }
        $semDrift = [double]$raw
    }

    $DriftBand = "unknown"
    if ($semDrift -ne $null) {
        if ($semDrift -lt 0.20)      { $DriftBand = "stable" }
        elseif ($semDrift -lt 0.45)  { $DriftBand = "low" }
        elseif ($semDrift -lt 0.70)  { $DriftBand = "medium" }
        else                         { $DriftBand = "high" }
    }

    # Pull latest cycle + smart data for context
    $C_current        = $null
    $C_forecast       = $null
    $Risk_current     = $null
    $Risk_forecast    = $null
    $Harmony_current  = $null
    $DriftScore       = $null
    $SmartAlerts      = $null

    if ($cycle) {
        $C_current     = $cycle.coherence.C_avg
        $C_forecast    = $cycle.coherence.C_forecast
        $Risk_current  = $cycle.coherence.risk_current
        $Risk_forecast = $cycle.coherence.risk_forecast
        $Harmony_current = $cycle.synthesis.harmony_score
        $DriftScore      = $cycle.synthesis.drift_score
    }

    if ($smart) {
        $SmartAlerts = $smart.alerts
        if (-not $Harmony_current -and $smart.synthesis) {
            $Harmony_current = $smart.synthesis.harmony_score
        }
        if (-not $DriftScore -and $smart.synthesis) {
            $DriftScore = $smart.synthesis.drift_score
        }
    }

    # Recommend a semantic "intensity" mode
    $SemanticIntensity = "balanced"
    if ($DriftBand -eq "high" -or $Risk_forecast -eq "Risk") {
        $SemanticIntensity = "calm"
    } elseif ($DriftBand -eq "medium" -and $Risk_forecast -ne "Risk") {
        $SemanticIntensity = "focused"
    } elseif ($DriftBand -eq "stable" -and $Risk_current -in @("Safe","Balanced")) {
        $SemanticIntensity = "exploratory"
    }

    # Compose a simple set of guidance hints
    $GuidanceHints = [ordered]@{
        semantic_intensity = $SemanticIntensity
        drift_band         = $DriftBand
        coherence_trend    = $C_trend
        preferred_heartbeat_s = $HB_mean
        note = "Use semantic_intensity + drift_band to modulate depth, abstraction level, and risk profile."
    }

    $alertList = @()
    if (-not $hadEcho) {
        $alertList += [ordered]@{
            type     = "no_echo_data"
            severity = "low"
            notes    = "Bridge v1.2 echo ledger empty or missing; semantic drift estimate is limited."
        }
    } else {
        if ($DriftBand -eq "high") {
            $alertList += [ordered]@{
                type     = "high_semantic_drift"
                severity = "medium"
                notes    = "Semantic drift index in HIGH band; favor grounding, reflection, and slower cycles."
            }
        }
        if ($C_current -ne $null -and $C_current -lt 0.60) {
            $alertList += [ordered]@{
                type     = "low_current_coherence"
                severity = "medium"
                notes    = "Current coherence below 0.60; Codex is operating outside ideal H₇ band."
            }
        }
    }

    $summary = [ordered]@{
        ok        = $true
        version   = "4.5"
        timestamp = (Get-Date).ToString("o")

        semantic_drift = [ordered]@{
            window_size      = $EchoEntries.Count
            C_series_mean    = $C_mean
            C_series_std     = $C_std
            C_series_trend   = $C_trend
            C_series_delta   = $C_delta
            phi_series_mean  = $Phi_mean
            phi_series_std   = $Phi_std
            drift_series_mean = $D_mean
            drift_series_std  = $D_std
            heartbeat_mean_s  = $HB_mean
            semantic_drift_index = $semDrift
            semantic_drift_band  = $DriftBand
            modes_histogram      = $ModeCounts
        }

        coherence_context = [ordered]@{
            C_current     = $C_current
            C_forecast    = $C_forecast
            risk_current  = $Risk_current
            risk_forecast = $Risk_forecast
            harmony_current = $Harmony_current
            drift_score     = $DriftScore
        }

        guidance = [ordered]@{
            hints = $GuidanceHints
        }

        smart_alerts = $SmartAlerts
        alerts       = $alertList

        meta = [ordered]@{
            codex_root = $CodexRoot
            echo_path  = $EchoLogPath
            cycle_path = $CycleStatePath
            smart_v44_path = $Smart44State
            state_path = $StatePathV45
            log_path   = $LogPathV45
            law_H7     = 0.70
            protocol   = "Universal Truth Protocol (E–I–C ∿ Placidity)"
            note       = "Semantic drift over recent Bridge echo window; designed for guiding AI behavior and orchestrator modes."
        }
    }

    $json = $summary | ConvertTo-Json -Depth 8
    $json | Set-Content -Path $StatePathV45 -Encoding UTF8
    $json | Add-Content -Path $LogPathV45

    Write-Host "✅ Smart Feedback v4.5: state written → $StatePathV45"
    Write-Host "🧾 Smart Feedback v4.5: log appended → $LogPathV45"

    return $summary
}

# Direct execution path
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-CodexSmartFeedbackV45 -CodexRootOverride $CodexRoot
}
