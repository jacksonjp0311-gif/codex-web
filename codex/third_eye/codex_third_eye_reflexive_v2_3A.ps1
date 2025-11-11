# ─────────────────────────────────────────────────────────────
# 🧿 Codex Third Eye v2.3A — Reflexive Forecasting Integration
# ─────────────────────────────────────────────────────────────
$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$LogDir    = "$CodexRoot\codex\third_eye\logs"
$StateDir  = "$CodexRoot\codex\third_eye\state"
$RunStamp  = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

Write-Host "`n🧠 Codex Third Eye v2.3A — Reflexive Integration Cycle ($RunStamp)"

# Ensure directories exist
foreach ($p in @($LogDir, $StateDir)) { if (!(Test-Path $p)) { New-Item -ItemType Directory -Path $p | Out-Null } }

# Merge all recent states into resonance file
Get-Content "$StateDir\third_eye_state_*.json" | Out-File "$LogDir\third_eye_resonance_v2_0.jsonl" -Encoding utf8

# Run harmonic integration
Write-Host "[run] harmonic integration..."
& "$CodexRoot\codex\third_eye\codex_third_eye_harmonic_v2_3.ps1"

# Check for new output
if (Test-Path "$LogDir\third_eye_resonance_v2_0.jsonl") {
    Write-Host "[ok] resonance data verified."
} else {
    Write-Host "[warn] resonance file missing."
}

# Autosave + Git
Set-Location $CodexRoot
git add "codex/third_eye/*" 2>$null
if (git status --porcelain) {
    git commit -m "🧠 Codex Third Eye v2.3A Reflexive Integration $RunStamp"
    try { git pull origin main --rebase } catch {}
    try { git push origin main } catch {}
}

Write-Host "[done] Cycle complete — returned to Codex root."
Set-Location $CodexRoot
