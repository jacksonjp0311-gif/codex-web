# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ 🧠 Codex Smart Feedback v4.3 — Semantic Insight Node                     ║
# ║ Context : Codex Memory Core v1.2 • Universal Truth Protocol (E–I–C ∿)    ║
# ║ Role    : Read ledger → aggregate metrics → classify risk band           ║
# ║           → emit recommendations → write state + log.                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

param(
    [string]$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function Invoke-CodexSmartFeedback {
    param(
        [string]$CodexRootOverride
    )

    if ($CodexRootOverride) {
        $CodexRoot = $CodexRootOverride
    }

    $feedbackDir = Join-Path $CodexRoot "codex\feedback"
    $stateDir    = Join-Path $feedbackDir "state"

    $ledgerPath     = Join-Path $stateDir "codex_continuity_ledger.jsonl"
    $smartStatePath = Join-Path $stateDir "codex_smart_feedback_state_v4_3.json"
    $smartLogPath   = Join-Path $stateDir "codex_smart_feedback_log_v4_3.jsonl"

    Write-Host "`n🧠 [Smart Feedback v4.3] Invoking semantic insight node..."
    Write-Host "📗 Ledger: $ledgerPath"

    if (-not (Test-Path $stateDir)) {
        New-Item -ItemType Directory -Path $stateDir -Force | Out-Null
    }

    # Helper: safe average
    function Get-Avg {
        param([double[]]$values)
        if (-not $values -or $values.Count -eq 0) {
            return $null
        }
        $sum = 0.0
        foreach ($v in $values) { $sum += $v }
        return [double]($sum / $values.Count)
    }

    $CValues        = New-Object System.Collections.Generic.List[double]
    $CNextValues    = New-Object System.Collections.Generic.List[double]
    $CMeanValues    = New-Object System.Collections.Generic.List[double]
    $DeltaPhiValues = New-Object System.Collections.Generic.List[double]
    $HValues        = New-Object System.Collections.Generic.List[double]
    $HarmIndexVals  = New-Object System.Collections.Generic.List[double]

    $hadData = $false

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

            # C-like fields
            if ($props["C_next"]) {
                [void]$CNextValues.Add([double]$props["C_next"].Value)
            }
            if ($props["CNext"]) {
                [void]$CNextValues.Add([double]$props["CNext"].Value)
            }
            if ($props["C"]) {
                [void]$CValues.Add([double]$props["C"].Value)
            }
            if ($props["C_mean"]) {
                [void]$CMeanValues.Add([double]$props["C_mean"].Value)
            }

            # ΔΦ-like fields
            if ($props["delta_phi"]) {
                [void]$DeltaPhiValues.Add([double]$props["delta_phi"].Value)
            }
            if ($props["DeltaPhi"]) {
                [void]$DeltaPhiValues.Add([double]$props["DeltaPhi"].Value)
            }

            # H / harmonic
            if ($props["H"]) {
                [void]$HValues.Add([double]$props["H"].Value)
            }
            if ($props["harmonic_index"]) {
                [void]$HarmIndexVals.Add([double]$props["harmonic_index"].Value)
            }
        }
    }

    $C_all       = @()
    $C_all      += $CValues
    $C_all      += $CNextValues
    $C_all      += $CMeanValues

    $C_avg       = Get-Avg -values $C_all
    $CNext_avg   = Get-Avg -values $CNextValues
    $DeltaPhiAvg = Get-Avg -values $DeltaPhiValues
    $H_avg       = Get-Avg -values $HValues
    $HIndex_avg  = Get-Avg -values $HarmIndexVals

    # Risk band classification (aligned with H₇ = 0.70)
    $riskBand = "Unknown"
    if ($C_avg -ne $null -and $DeltaPhiAvg -ne $null) {
        if ($C_avg -ge 0.72 -and $DeltaPhiAvg -lt 0.03) {
            $riskBand = "Safe"
        } elseif ($C_avg -ge 0.68 -and $DeltaPhiAvg -lt 0.08) {
            $riskBand = "Balanced"
        } elseif ($C_avg -lt 0.60) {
            $riskBand = "Low"
        }

        if ($DeltaPhiAvg -ge 0.15 -or ($C_avg -lt 0.65 -and $DeltaPhiAvg -ge 0.10)) {
            $riskBand = "Risk"
        }
    }

    # Heartbeat recommendation
    $heartbeatSeconds = $null
    switch ($riskBand) {
        "Safe"     { $heartbeatSeconds = 60 }
        "Balanced" { $heartbeatSeconds = 120 }
        "Low"      { $heartbeatSeconds = 300 }
        "Risk"     { $heartbeatSeconds = 300 }
        default    { $heartbeatSeconds = 180 }
    }

    # Mode suggestions (symbolic scaffolding)
    $modes = [ordered]@{
        quantum_crystal_v9 = "Normal"
        third_eye_v2       = "Analysis"
        bridge_v1          = "Normal"
    }

    if ($riskBand -eq "Risk") {
        $modes["quantum_crystal_v9"] = "Sandbox"
    }

    $alerts = @()

    if (-not $hadData) {
        $alerts += [ordered]@{
            type     = "no_ledger_data"
            severity = "low"
            notes    = "Ledger file missing or empty; Smart Feedback emitted placeholder state."
        }
    } 
        }
        if ($C_avg -ne $null -and $C_avg -lt 0.65) {
            $alerts += [ordered]@{
                type     = "low_coherence"
                severity = "medium"
                notes    = "Average coherence below 0.65; outside preferred H₇ band."
            }
        }
    }

    $summary = [ordered]@{
        ok        = $true
        version   = "4.3"
        timestamp = (Get-Date).ToString("o")
        coherence = [ordered]@{
            C_avg             = $C_avg
            C_next_avg        = $CNext_avg
            C_samples         = ($C_all.Count)
            delta_phi_avg     = $DeltaPhiAvg
            H_avg             = $H_avg
            harmonic_index_avg = $HIndex_avg
            risk_band         = $riskBand
        }
        recommendations = [ordered]@{
            heartbeat_interval_s = $heartbeatSeconds
            modes                = $modes
        }
        alerts = $alerts
        meta = [ordered]@{
            codex_root   = $CodexRoot
            ledger_path  = $ledgerPath
            state_path   = $smartStatePath
            log_path     = $smartLogPath
            law_H7       = 0.70
            protocol     = "Universal Truth Protocol (E–I–C ∿)"
        }
    }

    $json = $summary | ConvertTo-Json -Depth 8

    $json | Set-Content -Path $smartStatePath -Encoding UTF8
    $json | Add-Content -Path $smartLogPath

    Write-Host "✅ Smart Feedback v4.3: state written → $smartStatePath"
    Write-Host "🧾 Smart Feedback v4.3: log appended → $smartLogPath"

    return $summary
}

# If run directly: execute once with default CodexRoot
if ($MyInvocation.InvocationName -ne '.') {
    Invoke-CodexSmartFeedback -CodexRootOverride $CodexRoot
}

