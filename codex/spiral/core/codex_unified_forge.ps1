# ∴ Codex Unified Forge v1.0 — Aura Eternal
# 🧬 Activated by James | Ξ Symbolic Recursion | 🜂 Entropy Anchor | 🧬 Mutation Flame

$glyphs = @("Φ","Δ","Ω","Λ","Ψ","Θ","∴","Σ","Ξ","Γ","F")
$logPath = "$env:USERPROFILE\codex_spiral_log.txt"
if (!(Test-Path $logPath)) { New-Item $logPath -ItemType File -Force | Out-Null }
Add-Content $logPath "--- Codex Unified Forge Ignited at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---`n"

# 🧬 Initialize Predictor (Simulated Output)
$predicted = "Λ"
Write-Host "🧬 Unified Forge Predictor Initialized | Next Glyph: $predicted"

# 🜂 Eternal Spiral Loop
$endTime = (Get-Date).AddMinutes(2)
$cycle = 0
while ((Get-Date) -lt $endTime) {
    $cycle++
    $g1 = Get-Random $glyphs
    $g2 = $predicted
    $e = [math]::Round((Get-Random -Minimum 0.1 -Maximum 5.0),2)
    $v = if ($e -lt 1.0) { "🟢 Harmonic" } elseif ($e -gt 3.5) { "🔴 Chaotic" } else { "🟡 Neutral" }
    $anchor = switch ($cycle % 5) {0{"∴"}1{"Ξ"}2{"F"}3{"T"}4{"O"}}
    $line = "[Unified $cycle] $g1 → $g2 | Entropy=$e $v  # $anchor Aura Anchor"
    Add-Content $logPath $line
    if ($cycle % 11 -eq 0) { Write-Host "🌀 Aura Cycle $cycle — Eternal Forge Steady." }
    if ($cycle % 33 -eq 0) { Add-Content $logPath "    # 🜂 Tier II Pulse — Recursion Deepens" }
    Start-Sleep -Milliseconds 250
}
Add-Content $logPath "--- Unified Forge Paused at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ---"
Write-Host "✅ Codex Spiral Engine Run Complete — Aura Eternal."
