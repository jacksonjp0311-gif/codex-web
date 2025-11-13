# Codex Memory Weaving Engine v2.0
# Universal Truth Protocol (E–I–C with Placidity, H7 = 0.70)
param()

$ErrorActionPreference = "Stop"

$CodexRoot    = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir  = Join-Path $CodexRoot "codex\feedback"
$StateDir     = Join-Path $FeedbackDir "state"
$WeaveState   = Join-Path $StateDir    "codex_memory_weave_state_v2_0.json"
$LedgerPath   = Join-Path $StateDir    "codex_continuity_ledger.jsonl"

# Source states
$Smart44Path  = Join-Path $StateDir "codex_smart_feedback_state_v4_4.json"
$Smart45Path  = Join-Path $StateDir "codex_smart_feedback_state_v4_5.json"
$Smart46Path  = Join-Path $StateDir "codex_smart_feedback_state_v4_6.json"
$CyclePath    = Join-Path $StateDir "codex_smart_feedback_cycle_state_v5_0.json"
$Heartbeat41  = Join-Path $StateDir "codex_heartbeat_state_v4_1.json"
$Heartbeat42  = Join-Path $StateDir "codex_heartbeat_state_v4_2.json"

$BridgeStateDir = Join-Path $CodexRoot "codex\bridge\state"
$BridgeApiPath  = Join-Path $BridgeStateDir "codex_bridge_api_v1_2.json"
$EchoPath       = Join-Path $BridgeStateDir "codex_bridge_conversation_echo.jsonl"

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

# Load states
$smart44 = Load-JsonSafe -Path $Smart44Path
$smart45 = Load-JsonSafe -Path $Smart45Path
$smart46 = Load-JsonSafe -Path $Smart46Path
$cycle   = Load-JsonSafe -Path $CyclePath
$hb41    = Load-JsonSafe -Path $Heartbeat41
$hb42    = Load-JsonSafe -Path $Heartbeat42
$bridge  = Load-JsonSafe -Path $BridgeApiPath

# Derive core coherence values
$C_current   = $null
$C_forecast  = $null
$harmony     = $null
$deltaPhi    = 0.0
$riskCurrent = $null
$riskForecast= $null

if ($smart46 -and $smart46.coherence_context) {
    $C_current  = [double]$smart46.coherence_context.C_current
    $C_forecast = [double]$smart46.coherence_context.C_forecast
    $harmony    = [double]$smart46.coherence_context.harmony_current
}

# Fallback to cycle or bridge if needed
if ($null -eq $C_current -and $cycle -and $cycle.coherence) {
    $C_current  = [double]$cycle.coherence.C_avg
    $C_forecast = [double]$cycle.coherence.C_forecast
}
if ($null -eq $harmony -and $cycle -and $cycle.synthesis) {
    $harmony = [double]$cycle.synthesis.harmony_score
}

if ($cycle -and $cycle.coherence) {
    $deltaPhi    = [double]$cycle.coherence.delta_phi
    $riskCurrent = $cycle.coherence.risk_current
    $riskForecast= $cycle.coherence.risk_forecast
} elseif ($bridge -and $bridge.insights -and $bridge.insights.coherence) {
    $deltaPhi    = [double]$bridge.insights.coherence.delta_phi
    $riskCurrent = $bridge.insights.coherence.risk_current
    $riskForecast= $bridge.insights.coherence.risk_forecast
}

# Semantic hints from Smart Feedback 4.6
$semanticIntensity  = $null
$driftBand          = $null
$adaptiveWindowSize = $null
$adaptiveWindowBase = $null
$echoEntriesUsed    = $null

if ($smart46 -and $smart46.guidance -and $smart46.guidance.hints) {
    $semanticIntensity = $smart46.guidance.hints.semantic_intensity
    $driftBand         = $smart46.guidance.hints.drift_band
    $adaptiveWindowSize= $smart46.guidance.hints.adaptive_window_size
    $adaptiveWindowBase= $smart46.guidance.hints.adaptive_window_base
}

if ($smart46 -and $smart46.guidance -and $smart46.guidance.weaving -and $smart46.guidance.weaving.adaptive_window) {
    $echoEntriesUsed = $smart46.guidance.weaving.adaptive_window.echo_entries_used
}

# Heartbeat data
$hbInterval = $null
if ($hb42 -and $hb42.hb_interval_s) {
    $hbInterval = [int]$hb42.hb_interval_s
} elseif ($hb41 -and $hb41.hb_interval_s) {
    $hbInterval = [int]$hb41.hb_interval_s
}

# Awareness index based on Codex law
$AwarenessIndex = $null
if ($null -ne $C_current -and $null -ne $harmony) {
    $AwarenessIndex = ($C_current * $harmony) / (1 + [math]::Abs($deltaPhi))
}

# Echo window statistics (lightweight)
$echoCount   = 0
$echoRecentN = $null
if (Test-Path $EchoPath) {
    $echoLines = Get-Content -Path $EchoPath
    $echoCount = $echoLines.Count
    if ($echoCount -gt 0) {
        $takeN = 10
        if ($echoCount -lt $takeN) { $takeN = $echoCount }
        $echoRecentN = $takeN
    }
}

$timestamp = (Get-Date).ToString("o")

$weave = [ordered]@{
    ok         = $true
    version    = "2.0"
    timestamp  = $timestamp

    awareness  = [ordered]@{
        awareness_index = $AwarenessIndex
        C_current       = $C_current
        C_forecast      = $C_forecast
        harmony         = $harmony
        delta_phi       = $deltaPhi
        risk_current    = $riskCurrent
        risk_forecast   = $riskForecast
    }

    semantic   = [ordered]@{
        semantic_intensity   = $semanticIntensity
        drift_band           = $driftBand
        adaptive_window_size = $adaptiveWindowSize
        adaptive_window_base = $adaptiveWindowBase
        echo_entries_used    = $echoEntriesUsed
    }

    heartbeat  = [ordered]@{
        hb_interval_s = $hbInterval
        hb_state_v4_1 = $Heartbeat41
        hb_state_v4_2 = $Heartbeat42
    }

    echo       = [ordered]@{
        echo_ledger_path = $EchoPath
        echo_total_lines = $echoCount
        echo_recent_n    = $echoRecentN
    }

    sources    = [ordered]@{
        smart_v4_4_state = $Smart44Path
        smart_v4_5_state = $Smart45Path
        smart_v4_6_state = $Smart46Path
        cycle_v5_0_state = $CyclePath
        heartbeat_v4_1   = $Heartbeat41
        heartbeat_v4_2   = $Heartbeat42
        bridge_api_v1_2  = $BridgeApiPath
    }

    meta       = [ordered]@{
        codex_root = $CodexRoot
        law_H7     = 0.70
        protocol   = "Universal Truth Protocol (E–I–C with Placidity)"
        note       = "Memory Weaving Engine v2.0 aggregates Smart Feedback, Heartbeat, Bridge, and Echo into a single reflective awareness snapshot."
    }
}

# Write weave state
$weave | ConvertTo-Json -Depth 8 | Set-Content -Path $WeaveState -Encoding UTF8

# Append ledger entry
$ledgerEntry = [ordered]@{
    timestamp        = $timestamp
    source           = "MemoryWeaveV2.0"
    awareness_index  = $AwarenessIndex
    C_current        = $C_current
    C_forecast       = $C_forecast
    harmony          = $harmony
    delta_phi        = $deltaPhi
    risk_current     = $riskCurrent
    risk_forecast    = $riskForecast
    hb_interval_s    = $hbInterval
    drift_band       = $driftBand
    semantic_profile = $semanticIntensity
}

$ledgerLine = $ledgerEntry | ConvertTo-Json -Depth 6
Add-Content -Path $LedgerPath -Value $ledgerLine

Write-Host "Codex Memory Weaving Engine v2.0 completed."
Write-Host "  State  : $WeaveState"
Write-Host "  Ledger : $LedgerPath (appended entry)"
