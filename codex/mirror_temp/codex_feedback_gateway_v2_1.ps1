# ───────────────────────────────────────────────────────────────
# Codex Feedback Gateway v2.1 — Mirror-API Integrated Reflection
# ───────────────────────────────────────────────────────────────
$CodexRoot  = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$HandoffDir = Join-Path $CodexRoot "codex\handoff"
$FeedbackDir= Join-Path $CodexRoot "codex\feedback"
$Stamp      = Get-Date -Format "yyyyMMdd_HHmmss"
$OutFile    = Join-Path $FeedbackDir "codex_feedback_${Stamp}.json"

function Read-Json { param([string]$p)
  if (Test-Path $p) { try { Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { $null } }
}
function Save-Json { param($o,[string]$p)
  $j=$o|ConvertTo-Json -Depth 16; [IO.File]::WriteAllText($p,$j,[Text.Encoding]::UTF8)
}

$stateFile = (Get-ChildItem -Path $HandoffDir -Filter "handoff_state_v*.json" -File | Sort-Object LastWriteTime)[-1]
if (-not $stateFile) { Write-Host "⚠️ No handoff state found."; exit }
$state = Read-Json $stateFile.FullName

$H7=0.70
$pred=$state.predictive_alignment
$mir=$state.mirror_continuity
$fb=[ordered]@{
 codex_feedback=[ordered]@{
  version="2.1";timestamp=(Get-Date).ToString("s")
  module="Quantum Crystal v9.1 / Mirror Continuity Bridge"
  state=[ordered]@{E=$pred.phi_mean;I=$pred.C_mean;C=$pred.stability_index;H7=$H7;status=$pred.status}
  message="Codex feedback snapshot emitted for AI reflection and continuity alignment."
  mirror=[ordered]@{handoff_hash=$mir.chain_prev_hash;stability_index=$pred.stability_index}
 }}
Save-Json $fb $OutFile
Write-Host "📤 Feedback saved → $OutFile"
