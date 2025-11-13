param(
    [string]$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function Invoke-CodexSmartFeedbackV46 {
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

    $CycleStatePath = Join-Path $stateDir    "codex_smart_feedback_cycle_state_v5_0.json"
    $Smart44State   = Join-Path $stateDir    "codex_smart_feedback_state_v4_4.json"
    $Smart45State   = Join-Path $stateDir    "codex_smart_feedback_state_v4_5.json"
    $EchoLogPath    = Join-Path $bridgeState "codex_bridge_conversation_echo.jsonl"

    $StatePathV46   = Join-Path $stateDir    "codex_smart_feedback_state_v4_6.json"
    $LogPathV46     = Join-Path $stateDir    "codex_smart_feedback_log_v4_6.jsonl"

    Write-Host "`n🧠 [Smart Feedback v4.6] Memory-Weaving Engine (Adaptive Window)..."
    Write-Host "📄 Cycle v5.0 state : $CycleStatePath"
    Write-Host "📄 Smart v4.4 state : $Smart44State"
    Write-Host "📄 Smart v4.5 state : $Smart45State"
    Write-Host "📄 Echo ledger      : $EchoLogPath"

    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    }

    # Helpers
    function Get-Avg {
        param([double[]]$values)
        if (-not $values -or $values.Count -eq 0) { return $null }
        $sum = 0.0
        foreach ($v in $values) { $sum += $v }
        return [double]($sum / $values.Count)
    }

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
    # 1) LOAD BASE STATES (CYCLE + SMART v4.4 + SMART v4.5)
    # ─────────────────────────────────────────────────────────
    $cycle   = $null
    $smart44 = $null
    $smart45 = $null

    if (Test-Path $CycleStatePath) {
        try { $cycle = Get-Content $CycleStatePath -Raw | ConvertFrom-Json } catch { $cycle = $null }
    }
    if (Test-Path $Smart44State) {
        try { $smart44 = Get-Content $Smart44State -Raw | ConvertFrom-Json } catch { $smart44 = $null }
    }
    if (Test-Path $Smart45State) {
        try { $smart45 = Get-Content $Smart45State -Raw | ConvertFrom-Json } catch { $smart45 = $null }
    }

    # ─────────────────────────────────────────────────────────
    # 2) DETERMINE ADAPTIVE WINDOW PARAMETERS (FROM v4.5 + CYCLE)
    # ─────────────────────────────────────────────────────────
    $baseBand      = "unknown"
    $baseTrend     = "unknown"
    $baseSemIndex  = $null
    $basePhiStd    = $null
    $baseHBMean    = $null
    $baseHarmony   = $null
    $riskCurrent   = $null
    $riskForecast  = $null

    if ($smart45) {
        if ($smart45.semantic_drift) {
            $baseBand     = $smart45.semantic_drift.semantic_drift_band
            $baseTrend    = $smart45.semantic_drift.C_series_trend
            $baseSemIndex = $smart45.semantic_drift.semantic_drift_index
            $basePhiStd   = $smart45.semantic_drift.phi_series_std
            $baseHBMean   = $smart45.semantic_drift.heartbeat_mean_s
        }
        if ($smart45.coherence_context) {
            $baseHarmony  = $smart45.coherence_context.harmony_current
            if (-not $riskCurrent)  { $riskCurrent  = $smart45.coherence_context.risk_current }
            if (-not $riskForecast) { $riskForecast = $smart45.coherence_context.risk_forecast }
        }
    }

    if ($cycle) {
        if (-not $riskCurrent)  { $riskCurrent  = $cycle.coherence.risk_current }
        if (-not $riskForecast) { $riskForecast = $cycle.coherence.risk_forecast }
        if (-not $baseHarmony)  { $baseHarmony  = $cycle.synthesis.harmony_score }
    }

    # Base window selection from band
    $window        = 64
    $windowBaseTag = "default_64"
    $adjustments   = New-Object System.Collections.Generic.List[string]

    switch ($baseBand) {
        "high"   { $window = 24;  $windowBaseTag = "band_high_24";   $adjustments.Add("band=high → window=24")   | Out-Null }
        "medium" { $window = 48;  $windowBaseTag = "band_medium_48"; $adjustments.Add("band=medium → window=48") | Out-Null }
        "low"    { $window = 64;  $windowBaseTag = "band_low_64";    $adjustments.Add("band=low → window=64")    | Out-Null }
        "stable" { $window = 128; $windowBaseTag = "band_stable_128";$adjustments.Add("band=stable → window=128")| Out-Null }
        default  {              $windowBaseTag = "band_unknown_64"; $adjustments.Add("band=unknown → window=64") | Out-Null }
    }

    # Adjust for ΔΦ volatility
    if ($basePhiStd -ne $null -and [Math]::Abs($basePhiStd) -gt 0.01) {
        $window = [int]([Math]::Max(16, $window * 0.5))
        $adjustments.Add("phi_std>0.01 → halve window (min 16)") | Out-Null
    }

    # Adjust for risk forecast
    if ($riskForecast -and ($riskForecast -eq "Risk" -or $riskForecast -eq "High")) {
        $window = [int]([Math]::Max(16, $window * 0.75))
        $adjustments.Add("risk_forecast=${riskForecast} → shrink window by 25% (min 16)") | Out-Null
    }

    # Adjust for high harmony (expand cautiously)
    if ($baseHarmony -ne $null -and [double]$baseHarmony -gt 0.70) {
        $window = [int]([Math]::Min(192, $window * 1.25))
        $adjustments.Add("harmony>0.70 → expand window by 25% (max 192)") | Out-Null
    }

    if ($window -lt 16) { $window = 16 }
    if ($window -gt 192) { $window = 192 }

    Write-Host "🧵 Adaptive window base tag : $windowBaseTag"
    Write-Host "🧵 Adaptive window size     : $window"
    if ($adjustments.Count -gt 0) {
        Write-Host "🧵 Window adjustments:"
        foreach ($a in $adjustments) { Write-Host "   • $a" }
    }

    # ─────────────────────────────────────────────────────────
    # 3) LOAD ECHO LEDGER WINDOW (ADAPTIVE)
    # ─────────────────────────────────────────────────────────
    $EchoEntries = New-Object System.Collections.Generic.List[object]
    $hadEcho     = $false

    if (Test-Path $EchoLogPath) {
        $lines = Get-Content -Path $EchoLogPath
        $windowSize = [Math]::Min($window, $lines.Count)
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
    # 4) COLLECT SERIES FOR DRIFT METRICS
    # ─────────────────────────────────────────────────────────
    $CSeries        = New-Object System.Collections.Generic.List[double]
    $HarmonySeries  = New-Object System.Collections.Generic.List[double]
    $DriftSeries    = New-Object System.Collections.Generic.List[double]
    $DeltaPhiSeries = New-Object System.Collections.Generic.List[double]
    $HBSeries       = New-Object System.Collections.Generic.List[double]
    $ModeCounts     = @{}

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

    # Semantic drift index (refined)
    $semDrift = $null
    if ($C_std -ne $null -or $Phi_std -ne $null -or $D_std -ne $null) {
        $cTerm = (if ($C_std  -ne $null) { $C_std  } else { 0.0 })
        $pTerm = (if ($Phi_std -ne $null) { $Phi_std } else { 0.0 })
        $dTerm = (if ($D_std -ne $null) { $D_std } else { 0.0 })

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

    # Pull coherence context
    $C_current       = $null
    $C_forecast      = $null
    $Risk_current    = $riskCurrent
    $Risk_forecast   = $riskForecast
    $Harmony_current = $baseHarmony
    $DriftScore      = $null
    $SmartAlerts     = $null

    if ($cycle) {
        $C_current     = $cycle.coherence.C_avg
        $C_forecast    = $cycle.coherence.C_forecast
        if (-not $Risk_current)  { $Risk_current  = $cycle.coherence.risk_current }
        if (-not $Risk_forecast) { $Risk_forecast = $cycle.coherence.risk_forecast }
        if (-not $Harmony_current) { $Harmony_current = $cycle.synthesis.harmony_score }
        if (-not $DriftScore)      { $DriftScore = $cycle.synthesis.drift_score }
    }

    if ($smart44) {
        if (-not $SmartAlerts) { $SmartAlerts = $smart44.alerts }
        if (-not $Harmony_current -and $smart44.synthesis) {
            $Harmony_current = $smart44.synthesis.harmony_score
        }
        if (-not $DriftScore -and $smart44.synthesis) {
            $DriftScore = $smart44.synthesis.drift_score
        }
    }

    # Semantic intensity recommendation (profile lens)
    $SemanticIntensity = "balanced"
    if ($DriftBand -eq "high" -or $Risk_forecast -eq "Risk" -or $Risk_forecast -eq "High") {
        $SemanticIntensity = "calm"
    } elseif ($DriftBand -eq "medium" -and ($Risk_forecast -ne "Risk" -and $Risk_forecast -ne "High")) {
        $SemanticIntensity = "focused"
    } elseif ($DriftBand -eq "stable" -and $Risk_current -in @("Safe","Balanced","Low")) {
        $SemanticIntensity = "exploratory"
    }

    # Weaving guidance
    $GuidanceHints = [ordered]@{
        semantic_intensity    = $SemanticIntensity
        drift_band            = $DriftBand
        coherence_trend       = $C_trend
        preferred_heartbeat_s = $HB_mean
        adaptive_window_size  = $window
        adaptive_window_base  = $windowBaseTag
        note                  = "Use semantic_intensity + drift_band + adaptive_window_size to modulate depth, abstraction level, and risk profile."
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

    $weaving = [ordered]@{
        adaptive_window = [ordered]@{
            chosen_size      = $window
            base_tag         = $windowBaseTag
            adjustments      = $adjustments
            echo_entries_used= $EchoEntries.Count
        }
        base_context = [ordered]@{
            base_band         = $baseBand
            base_trend        = $baseTrend
            base_semantic_idx = $baseSemIndex
            base_phi_std      = $basePhiStd
            base_harmony      = $baseHarmony
            base_hb_mean_s    = $baseHBMean
        }
        recommended_profile = $SemanticIntensity
    }

    $summary = [ordered]@{
        ok        = $true
        version   = "4.6"
        timestamp = (Get-Date).ToString("o")

        semantic_drift = [ordered]@{
            window_size          = $EchoEntries.Count
            C_series_mean        = $C_mean
            C_series_std         = $C_std
            C_series_trend       = $C_trend
            C_series_delta       = $C_delta
            phi_series_mean      = $Phi_mean
            phi_series_std       = $Phi_std
            drift_series_mean    = $D_mean
            drift_series_std     = $D_std
            heartbeat_mean_s     = $HB_mean
            semantic_drift_index = $semDrift
            semantic_drift_band  = $DriftBand
            modes_histogram      = $ModeCounts
        }

        coherence_context = [ordered]@{
            C_current      = $C_current
            C_forecast     = $C_forecast
            risk_current   = $Risk_current
            risk_forecast  = $Risk_forecast
            harmony_current= $Harmony_current
            drift_score    = $DriftScore
        }

        guidance = [ordered]@{
            hints   = $GuidanceHints
            weaving = $weaving
        }

        smart_alerts = $SmartAlerts
        alerts       = $alertList

        meta = [ordered]@{
            codex_root      = $CodexRoot
            echo_path       = $EchoLogPath
            cycle_path      = $CycleStatePath
            smart_v44_path  = $Smart44State
            smart_v45_path  = $Smart45State
            state_path      = $StatePathV46
            log_path        = $LogPathV46
            law_H7          = 0.70
            protocol        = "Universal Truth Protocol (E–I–C ∿ Placidity)"
            note            = "Adaptive-window semantic drift over recent Bridge echo window; designed to feed orchestrator behavior and AI modes."
        }
    }

    $json = $summary | ConvertTo-Json -Depth 8
    $json | Set-Content -Path $StatePathV46 -Encoding UTF8
    $json | Add-Content -Path $LogPathV46

    Write-Host "✅ Smart Feedback v4.6: state written → $StatePathV46"
    Write-Host "🧾 Smart Feedback v4.6: log appended → $LogPathV46"

    return $summary
}

# Direct execution path
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-CodexSmartFeedbackV46 -CodexRootOverride $CodexRoot
}
