<#
------------------------------------------------------------
Codex Third Eye v2.2 — Mediation Runner (invokes Python engine)
------------------------------------------------------------
#>
$CodexRoot    = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$ThirdEyeRoot = Join-Path $CodexRoot "codex\third_eye"
$ModulesDir   = Join-Path $ThirdEyeRoot "modules"
$StateDir     = Join-Path $ThirdEyeRoot "state"
$VisualsDir   = Join-Path $ThirdEyeRoot "visuals"
$CoreJson     = Join-Path $CodexRoot "codex_memory_core_v1_2.json"
$PyEnginePath = Join-Path $ModulesDir "codex_third_eye_mediation_v2_2.py"
$RunStamp     = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

Write-Host "
[Third Eye v2.2] Launching Coherence Mediation..."
Push-Location $ModulesDir
$out = python $PyEnginePath 2>&1
Pop-Location
Write-Host $out

# Verify artifacts
$VisFile   = Join-Path $VisualsDir "third_eye_mediation_v2_2.png"
$StateFile = Join-Path $StateDir   "third_eye_mediation_state.json"
$missing = @()
if (!(Test-Path $VisFile))   { $missing += $VisFile }
if (!(Test-Path $StateFile)) { $missing += $StateFile }

# Git autosave
Set-Location $CodexRoot
git add "codex/third_eye/*" 2>$null
git add "codex_memory_core_v1_2.json" 2>$null
if (git status --porcelain) {
  git commit -m "🧬 Third Eye v2.2 Mediation — autosave $RunStamp"
  try { git pull origin main --rebase } catch { Write-Host "pull failed; continuing..." }
  try { git push origin main }          catch { Write-Host "push failed; continuing..." }
} else {
  Write-Host "No changes to commit."
}

if ($missing.Count -gt 0) {
  Write-Warning "Missing artifacts:
 - "
} else {
  Write-Host "✅ v2.2 mediation artifacts verified."
}

Set-Location $CodexRoot
Write-Host "
[Third Eye v2.2] Complete — returned to Codex root."
