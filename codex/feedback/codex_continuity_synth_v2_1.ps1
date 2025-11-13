# Codex Continuity Synthesizer v2.1
# Domain: Feedback / Continuity
# Law   : Universal Truth Protocol (E–I–C with Placidity, H7 = 0.70)
param()

$ErrorActionPreference = "Stop"

$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"

$IndexState  = Join-Path $StateDir   "codex_continuity_index_v2_1.json"
$LedgerPath  = Join-Path $StateDir   "codex_continuity_ledger.jsonl"

# Helper: safe JSON loader
function Load-JsonSafe {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return $null
    }
    try {
        return (Get-Content -Raw -Path $Path | ConvertFrom-Json)
    } catch {
        return $null
    }
}

# Helper: stats on numeric array
function Get-Stats {
    param([double[]]$values)

    if (-not $values -or $values.Count -eq 0) {
        return [ordered]@{
            mean  = $null
            std   = $null
            slope = $null
        }
    }

    $n = [double]$values.Count

    # mean
    $sum = 0.0
    foreach ($v in $values) { $sum += $v }
    $mean = $sum / $n

    # std
    $varSum = 0.0
    foreach ($v in $values) { $varSum += [math]::Pow($v - $mean, 2) }
    $std = 0.0
    if ($n -gt 1) { $std = [math]::Sqrt($varSum / ($n - 1.0)) }

    # slope (simple first-to-last)
    $slope = $null
    if ($n -gt 1) {
        $first = $values[0]
        $last  = $values[$values.Count - 1]
        $slope = ($last - $first) / ($n - 1.0)
    }

    return [ordered]@{
        mean  = $mean
        std   = $std
        slope = $slope
    }
}

# Load ledger lines
$rows = @()
if (Test-Path $LedgerPath) {
    $lines = Get-Content -Path $LedgerPath
    foreach ($line in $lines) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            try {
                $obj = $line | ConvertFrom-Json
                if ($obj) {
                    $rows += $obj
                }
            } catch {
                # skip malformed lines
            }
        }
    }
}

$ledgerCount = $rows.Count
$timestamp = (Get-Date).ToString("o")

if ($ledgerCount -eq 0) {
    # No data yet: write minimal state and exit
    $state = [ordered]@{
        ok            = $true
        version       = "2.1"
        timestamp     = $timestamp
        ledger_count  = 0
        continuity_index = $null
        continuity_mode  = "unknown"
        note          = "No entries in codex_continuity_ledger.jsonl; continuity index cannot be computed yet."
    }

    $state | ConvertTo-Json -Depth 6 | Set-Content -Path $IndexState -Encoding UTF8
    Write-Host "Codex Continuity Synthesizer v2.1: no ledger entries; wrote empty index state."
    Write-Host "  State : $IndexState"
    return
}

# Extract numeric sequences
$awarenessList = @()
$CList         = @()
$phiList       = @()

foreach ($r in $rows) {
    if ($null -ne $r.awareness_index) {
        $awarenessList += [double]$r.awareness_index
    }
    if ($null -ne $r.C_current) {
        $CList += [double]$r.C_current
    }
    if ($null -ne $r.delta_phi) {
        $phiList += [double]$r.delta_phi
    }
}

# Window function
function Get-Window {
    param(
        [object[]]$values,
        [int]$windowSize
    )

    if (-not $values -or $values.Count -eq 0) {
        return @()
    }

    $count = $values.Count
    if ($count -le $windowSize) {
        return $values
    }

    $start = $count - $windowSize
    return $values[$start..($count - 1)]
}

$winSizes = @(10, 25, 50)

$windows = @{}
foreach ($w in $winSizes) {
    $windows["w$w"] = [ordered]@{
        awareness = Get-Stats -values (Get-Window -values $awarenessList -windowSize $w)
        C_current = Get-Stats -values (Get-Window -values $CList         -windowSize $w)
        delta_phi = Get-Stats -values (Get-Window -values $phiList       -windowSize $w)
    }
}

# Use the largest window as base continuity
$baseWin = $windows["w50"]

$awStats = $baseWin.awareness
$CStats  = $baseWin.C_current
$phiStats= $baseWin.delta_phi

$awMean  = $awStats.mean
$awSlope = $awStats.slope
$phiStd  = $phiStats.std

$continuityIndex = $null
$continuityMode  = "unknown"

if ($null -ne $awMean) {
    $phiPenalty = 1.0
    if ($null -ne $phiStd) {
        $phiPenalty = 1.0 / (1.0 + $phiStd)
    }

    $stability = 1.0
    if ($null -ne $awSlope) {
        $stability = 1.0 / (1.0 + [math]::Abs($awSlope))
    }

    $raw = $awMean * $phiPenalty * $stability
    if ($raw -lt 0.0) { $raw = 0.0 }
    if ($raw -gt 1.0) { $raw = 1.0 }
    $continuityIndex = $raw

    # Classification
    $continuityMode = "divergent"
    if ($continuityIndex -ge 0.5) {
        $continuityMode = "balanced"
    }
    if ($continuityIndex -ge 0.7 -and $phiStd -lt 0.1) {
        $continuityMode = "stable"
    }
}

# Last row insight for semantic profile / risk
$lastRow = $rows[$rows.Count - 1]

$lastSemantic  = $null
$lastDriftBand = $null
$lastRisk      = $null
$lastRiskF     = $null
$hbInterval    = $null

if ($lastRow) {
    $lastSemantic  = $lastRow.semantic_profile
    $lastDriftBand = $lastRow.drift_band
    $lastRisk      = $lastRow.risk_current
    $lastRiskF     = $lastRow.risk_forecast
    if ($lastRow.hb_interval_s) {
        $hbInterval = [int]$lastRow.hb_interval_s
    }
}

if ($null -eq $hbInterval) {
    $hbInterval = 300
}

# Recommend next heartbeat interval based on continuity
$recommendedHb = $hbInterval
$recommendedProfile = "balanced"

if ($continuityIndex -ne $null) {
    if ($continuityIndex -lt 0.5) {
        $recommendedHb = [int]($hbInterval * 1.5)
        $recommendedProfile = "placidity_safe"
    }
    if ($continuityIndex -ge 0.5 -and $continuityIndex -lt 0.7) {
        $recommendedHb = $hbInterval
        $recommendedProfile = "balanced"
    }
    if ($continuityIndex -ge 0.7) {
        $recommendedHb = [int]([math]::Max(120, $hbInterval * 0.75))
        $recommendedProfile = "harmonic_expansion"
    }
}

$state = [ordered]@{
    ok               = $true
    version          = "2.1"
    timestamp        = $timestamp
    ledger_count     = $ledgerCount
    continuity_index = $continuityIndex
    continuity_mode  = $continuityMode

    summary = [ordered]@{
        awareness_mean_w50 = $awMean
        awareness_slope_w50= $awSlope
        delta_phi_std_w50  = $phiStats.std
        C_mean_w50         = $CStats.mean
    }

    windows = [ordered]@{
        w10 = $windows["w10"]
        w25 = $windows["w25"]
        w50 = $windows["w50"]
    }

    signals = [ordered]@{
        last_awareness_index = $lastRow.awareness_index
        last_C_current       = $lastRow.C_current
        last_C_forecast      = $lastRow.C_forecast
        last_harmony         = $lastRow.harmony
        last_delta_phi       = $lastRow.delta_phi
        last_risk_current    = $lastRisk
        last_risk_forecast   = $lastRiskF
        last_semantic        = $lastSemantic
        last_drift_band      = $lastDriftBand
    }

    drift_vector = [ordered]@{
        awareness_slope = $awSlope
        C_slope         = $CStats.slope
        phi_std         = $phiStd
    }

    recommendations = [ordered]@{
        recommended_heartbeat_s = $recommendedHb
        recommended_profile     = $recommendedProfile
        note                    = "Continuity index close to 1 means stable, low-drift Codex evolution; near 0 indicates divergent / unstable conditions."
    }

    meta = [ordered]@{
        codex_root = $CodexRoot
        law_H7     = 0.70
        protocol   = "Universal Truth Protocol (E–I–C with Placidity)"
        ledger     = $LedgerPath
        note       = "Continuity Synthesizer v2.1 aggregates continuity ledger into a single controllable index and mode for orchestrators."
    }
}

$state | ConvertTo-Json -Depth 10 | Set-Content -Path $IndexState -Encoding UTF8

Write-Host "Codex Continuity Synthesizer v2.1 complete."
Write-Host "  State  : $IndexState"
Write-Host "  Ledger : $LedgerPath (input)"
