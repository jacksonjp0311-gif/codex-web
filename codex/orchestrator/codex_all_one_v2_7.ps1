# Codex All-One v2.7 — VoiceBox Wrapper Orchestrator
# Domain : RootMirror / Feedback
# Law    : Universal Truth Protocol (E–I–C with Placidity, H7 = 0.70)
param()

$ErrorActionPreference = "Stop"

$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$OrchDir     = Join-Path $CodexRoot "codex\orchestrator"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"

$AllOneV26   = Join-Path $OrchDir "codex_all_one_v2_6.ps1"

# Feedback state paths
$Smart46Path   = Join-Path $StateDir "codex_smart_feedback_state_v4_6.json"
$WeavePath     = Join-Path $StateDir "codex_memory_weave_state_v2_0.json"
$ContinuityPath= Join-Path $StateDir "codex_continuity_index_v2_1.json"
$Heartbeat42   = Join-Path $StateDir "codex_heartbeat_state_v4_2.json"

# Helper: safe JSON loader
function Load-JsonSafe {
    param([string]$Path)
    if (-not $Path) { return $null }
    if (-not (Test-Path $Path)) { return $null }
    try {
        return (Get-Content -Raw -Path $Path | ConvertFrom-Json)
    } catch {
        return $null
    }
}

# 1) RUN EXISTING ALL-ONE v2.6 (FULL SYSTEM ORCHESTRATOR)
if (Test-Path $AllOneV26) {
    Write-Host ""
    Write-Host "────────────────────────────────────────────────────────"
    Write-Host "  Codex All-One v2.7 → invoking v2.6 orchestrator..."
    Write-Host "────────────────────────────────────────────────────────"
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $AllOneV26
    } catch {
        Write-Host "Warning: All-One v2.6 orchestration failed: $($_.Exception.Message)"
    }
} 

# 2) LOAD FEEDBACK STATES FOR VOICEBOX
$smart46    = Load-JsonSafe -Path $Smart46Path
$weave      = Load-JsonSafe -Path $WeavePath
$continuity = Load-JsonSafe -Path $ContinuityPath
$hb42       = Load-JsonSafe -Path $Heartbeat42

# Extract Smart Feedback coherence context
$C_current   = $null
$C_forecast  = $null
$harmony     = $null
$driftScore  = $null

if ($smart46 -and $smart46.coherence_context) {
    $C_current  = $smart46.coherence_context.C_current
    $C_forecast = $smart46.coherence_context.C_forecast
    $harmony    = $smart46.coherence_context.harmony_current
    $driftScore = $smart46.coherence_context.drift_score
}

# Awareness / continuity from Memory Weave and continuity index
$awarenessIndex   = $null
$deltaPhi         = $null
$continuityIndex  = $null
$continuityMode   = "unknown"

if ($weave -and $weave.awareness) {
    $awarenessIndex = $weave.awareness.awareness_index
    $deltaPhi       = $weave.awareness.delta_phi
}

if ($continuity) {
    if ($continuity.continuity_index -ne $null) {
        $continuityIndex = $continuity.continuity_index
    }
    if ($continuity.continuity_mode) {
        $continuityMode = $continuity.continuity_mode
    }
}

# Heartbeat and recommendations from continuity index
$hbIntervalCurrent   = $null
$hbRecommended       = $null
$profileRecommended  = "balanced"

if ($hb42 -and $hb42.hb_interval_s) {
    $hbIntervalCurrent = [int]$hb42.hb_interval_s
}

if ($continuity -and $continuity.recommendations) {
    if ($continuity.recommendations.recommended_heartbeat_s -ne $null) {
        $hbRecommended = [int]$continuity.recommendations.recommended_heartbeat_s
    }
    if ($continuity.recommendations.recommended_profile) {
        $profileRecommended = $continuity.recommendations.recommended_profile
    }
}

# Fallback defaults if missing
if ($null -eq $hbIntervalCurrent) {
    $hbIntervalCurrent = 300
}
if ($null -eq $hbRecommended) {
    $hbRecommended = $hbIntervalCurrent
}

# Semantic weather from Smart Feedback 4.6 if available
$semanticIntensity = $null
$driftBand         = $null

if ($smart46 -and $smart46.guidance -and $smart46.guidance.hints) {
    $semanticIntensity = $smart46.guidance.hints.semantic_intensity
    $driftBand         = $smart46.guidance.hints.drift_band
}

# 3) PRINT VOICEBOX SUMMARY
Write-Host ""
Write-Host "==============================================================="
Write-Host " Codex VoiceBox v1.0 — Feedback Summary"
Write-Host "==============================================================="

# Continuity / awareness
if ($continuityIndex -ne $null) {
    Write-Host (" Continuity index : {0:N3}   mode: {1}" -f $continuityIndex, $continuityMode)
} 

if ($awarenessIndex -ne $null) {
    Write-Host (" Awareness index  : {0:N3}" -f $awarenessIndex)
} 

if ($deltaPhi -ne $null) {
    Write-Host (" Delta Phi (ΔΦ)   : {0:N4}" -f $deltaPhi)
} 

Write-Host ""

# Coherence and harmony
if ($C_current -ne $null) {
    if ($C_forecast -ne $null) {
        Write-Host (" Coherence C_now  : {0:N3}   C_next: {1:N3}" -f $C_current, $C_forecast)
    } " -f $C_current)
    }
} 

if ($harmony -ne $null) {
    Write-Host (" Harmony score    : {0:N3}" -f $harmony)
}

if ($driftScore -ne $null) {
    Write-Host (" Drift score      : {0:N4}" -f $driftScore)
}

Write-Host ""

# Semantic weather
if ($semanticIntensity) {
    Write-Host (" Semantic weather : intensity={0}" -f $semanticIntensity)
} 

if ($driftBand) {
    Write-Host (" Drift band       : {0}" -f $driftBand)
}

Write-Host ""

# Heartbeat and profile
Write-Host (" Heartbeat now    : {0} s" -f $hbIntervalCurrent)
Write-Host (" Heartbeat next   : {0} s" -f $hbRecommended)
Write-Host (" Profile          : {0}" -f $profileRecommended)

Write-Host "==============================================================="
Write-Host " VoiceBox complete. Codex cycle reflection emitted."
Write-Host "==============================================================="

# Always return to Codex root
try { Set-Location $CodexRoot } catch {}

