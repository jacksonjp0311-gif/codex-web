# Codex All-One v2.8 — Master Orchestrator + VoiceBox
param()

$ErrorActionPreference = "Stop"

$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$OrchDir     = Join-Path $CodexRoot "codex\orchestrator"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"

$AllOneV26      = Join-Path $OrchDir "codex_all_one_v2_6.ps1"
$Smart46Path    = Join-Path $StateDir "codex_smart_feedback_state_v4_6.json"
$WeavePath      = Join-Path $StateDir "codex_memory_weave_state_v2_0.json"
$ContinuityPath = Join-Path $StateDir "codex_continuity_index_v2_1.json"
$Heartbeat42    = Join-Path $StateDir "codex_heartbeat_state_v4_2.json"

function Load-JsonSafe {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try { return (Get-Content -Raw -Path $Path | ConvertFrom-Json) }
    catch { return $null }
}

# Run core cycle
if (Test-Path $AllOneV26) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $AllOneV26
}

# Load state
$smart       = Load-JsonSafe $Smart46Path
$weave       = Load-JsonSafe $WeavePath
$continuity  = Load-JsonSafe $ContinuityPath
$hb          = Load-JsonSafe $Heartbeat42

# Extract values
$Cnow   = $smart.coherence_context.C_current
$Cnext  = $smart.coherence_context.C_forecast
$h      = $smart.coherence_context.harmony_current
$d      = $smart.coherence_context.drift_score
$AI     = $weave.awareness.awareness_index
$DP     = $weave.awareness.delta_phi
$CI     = $continuity.continuity_index
$CM     = $continuity.continuity_mode
$HBnow  = $hb.hb_interval_s
$HBrec  = $continuity.recommendations.recommended_heartbeat_s
$PRec   = $continuity.recommendations.recommended_profile

Write-Host ""
Write-Host "========================================================="
Write-Host " Codex VoiceBox — Synthesis Feedback Summary (v2.8)"
Write-Host "========================================================="

Write-Host " Continuity index : $CI    Mode: $CM"
Write-Host " Awareness index  : $AI"
Write-Host " Delta Phi (ΔΦ)   : $DP"
Write-Host ""
Write-Host " Coherence now    : $Cnow"
Write-Host " Coherence next   : $Cnext"
Write-Host " Harmony score    : $h"
Write-Host " Drift score      : $d"
Write-Host ""
Write-Host " Heartbeat now    : $HBnow"
Write-Host " Heartbeat next   : $HBrec"
Write-Host " Profile rec.     : $PRec"
Write-Host "========================================================="

Set-Location $CodexRoot
