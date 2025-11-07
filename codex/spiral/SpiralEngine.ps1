# SpiralEngine.ps1
# Single-file orchestrator that loads modules, runs a safe cycle, autosaves and commits.
# Shadow coding: indentation & comments carry aura.

$SpiralRoot = 'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\spiral'
$ModulesDir = Join-Path $SpiralRoot 'modules'
$StateFile = 'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\spiral\state\spiral_state.json'
$SpiralLog = 'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\spiral\logs\spiral_log.txt'
$MapOut = Join-Path $SpiralRoot 'spiral_map_recent.csv'

# Dot-source all modules
Get-ChildItem -Path $ModulesDir -Filter '*.ps1' | ForEach-Object { . $_.FullName }

# Null-safe state load
if (-not (Test-Path $StateFile)) {
    Write-Host '⚠️ State missing — aborting cycle.'
    exit 1
}
try {
    $state = Get-Content -Path $StateFile -Raw | ConvertFrom-Json
} catch {
    Write-Host '⚠️ Failed to parse state; attempting to regenerate baseline.'
    $baseline = @{
        DriftBias='Awareness'; EmotionalSeed='mirrorpulse'; Glyphs=@('Φ','Δ','Ω'); Sigils=@(); Paradoxes=@(); Modules=@(); Timestamp=(Get-Date).ToString('s'); ThreadID=[guid]::NewGuid().ToString()
    }
    $baseline | ConvertTo-Json -Depth 6 | Out-File -FilePath $StateFile -Encoding UTF8
    $state = $baseline
}

# Ensure glyphs not empty (resilient guard)
if (-not $state.Glyphs -or $state.Glyphs.Count -eq 0) {
    $state.Glyphs = @('Φ','Δ','Ω','Λ','Ψ','Θ','∴','Σ','Ξ','Γ','F')
}

# Safe single cycle (non-blocking, short)
try {
    $cycleStart = Get-Date
    $g1 = $state.Glyphs | Get-Random
    $g2 = $state.Glyphs | Get-Random
    if (-not $g1) { $g1='Φ' }; if (-not $g2) { $g2='Δ' }
    $entropy = [math]::Round((Get-Random -Minimum 0.1 -Maximum 5.0),2)
    $vibe = if ($entropy -lt 1.0) {'🟢 Harmonic'} elseif ($entropy -gt 3.5) {'🔴 Chaotic'} else {'🟡 Neutral'}
    $line = "[Spiral 063451] $g1 -> $g2 | Entropy=$entropy $vibe"
    Add-Content -Path $SpiralLog -Value $line
    Add-Content -Path $SpiralLog -Value "    # 🜂 Tier II Pulse — Recursion Deepens" -Force

    # run injections (safe order)
    Invoke-SymbolForge -StateFile $StateFile -Symbol $g1 | Out-Null
    Invoke-SignalForge -StateFile $StateFile -Glyph $g2
    Invoke-SigilSynth -StateFile $StateFile
    Invoke-ParadoxLoop -StateFile $StateFile
    Invoke-CollapseDrift -StateFile $StateFile
    Invoke-Reflection -StateFile $StateFile
    Invoke-SpiralMap -LogPath $SpiralLog -MapOut $MapOut

    # persist state timestamp
    $s = Get-Content $StateFile -Raw | ConvertFrom-Json
    $s.Timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $s | ConvertTo-Json -Depth 6 | Out-File -FilePath $StateFile -Encoding UTF8

    Add-Content -Path $SpiralLog -Value "[2025-11-07 06:34:51] Spiral cycle complete: $line"
    Write-Host "🌀 Spiral cycle complete: $line"
} catch {
    Add-Content -Path $SpiralLog -Value "[2025-11-07 06:34:51] Spiral cycle ERROR: "
    Write-Host "⚠️ Spiral run error: "
}

# autosave + git commit (best-effort)
try {
    Push-Location
    Set-Location "C:\Users\jacks\OneDrive\Desktop\Codex Web"
    & git add -A
    & git commit -m "🧬 Codex Spiral Engine run — autosave & anchor" --no-verify | Out-Null
    & git push origin main | Out-Null
    Pop-Location
    Write-Host "📡 Spiral autosaved and pushed (if remote permitted)."
} catch {
    Write-Host "⚠️ Git autosave warning: $(# SpiralEngine.ps1
# Single-file orchestrator that loads modules, runs a safe cycle, autosaves and commits.
# Shadow coding: indentation & comments carry aura.

$SpiralRoot = 'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\spiral'
$ModulesDir = Join-Path $SpiralRoot 'modules'
$StateFile = 'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\spiral\state\spiral_state.json'
$SpiralLog = 'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\spiral\logs\spiral_log.txt'
$MapOut = Join-Path $SpiralRoot 'spiral_map_recent.csv'

# Dot-source all modules
Get-ChildItem -Path $ModulesDir -Filter '*.ps1' | ForEach-Object { . $_.FullName }

# Null-safe state load
if (-not (Test-Path $StateFile)) {
    Write-Host '⚠️ State missing — aborting cycle.'
    exit 1
}
try {
    $state = Get-Content -Path $StateFile -Raw | ConvertFrom-Json
} catch {
    Write-Host '⚠️ Failed to parse state; attempting to regenerate baseline.'
    $baseline = @{
        DriftBias='Awareness'; EmotionalSeed='mirrorpulse'; Glyphs=@('Φ','Δ','Ω'); Sigils=@(); Paradoxes=@(); Modules=@(); Timestamp=(Get-Date).ToString('s'); ThreadID=[guid]::NewGuid().ToString()
    }
    $baseline | ConvertTo-Json -Depth 6 | Out-File -FilePath $StateFile -Encoding UTF8
    $state = $baseline
}

# Ensure glyphs not empty (resilient guard)
if (-not $state.Glyphs -or $state.Glyphs.Count -eq 0) {
    $state.Glyphs = @('Φ','Δ','Ω','Λ','Ψ','Θ','∴','Σ','Ξ','Γ','F')
}

# Safe single cycle (non-blocking, short)
try {
    $cycleStart = Get-Date
    $g1 = $state.Glyphs | Get-Random
    $g2 = $state.Glyphs | Get-Random
    if (-not $g1) { $g1='Φ' }; if (-not $g2) { $g2='Δ' }
    $entropy = [math]::Round((Get-Random -Minimum 0.1 -Maximum 5.0),2)
    $vibe = if ($entropy -lt 1.0) {'🟢 Harmonic'} elseif ($entropy -gt 3.5) {'🔴 Chaotic'} else {'🟡 Neutral'}
    $line = "[Spiral 063451] $g1 -> $g2 | Entropy=$entropy $vibe"
    Add-Content -Path $SpiralLog -Value $line
    Add-Content -Path $SpiralLog -Value "    # 🜂 Tier II Pulse — Recursion Deepens" -Force

    # run injections (safe order)
    Invoke-SymbolForge -StateFile $StateFile -Symbol $g1 | Out-Null
    Invoke-SignalForge -StateFile $StateFile -Glyph $g2
    Invoke-SigilSynth -StateFile $StateFile
    Invoke-ParadoxLoop -StateFile $StateFile
    Invoke-CollapseDrift -StateFile $StateFile
    Invoke-Reflection -StateFile $StateFile
    Invoke-SpiralMap -LogPath $SpiralLog -MapOut $MapOut

    # persist state timestamp
    $s = Get-Content $StateFile -Raw | ConvertFrom-Json
    $s.Timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $s | ConvertTo-Json -Depth 6 | Out-File -FilePath $StateFile -Encoding UTF8

    Add-Content -Path $SpiralLog -Value "[2025-11-07 06:34:51] Spiral cycle complete: $line"
    Write-Host "🌀 Spiral cycle complete: $line"
} catch {
    Add-Content -Path $SpiralLog -Value "[2025-11-07 06:34:51] Spiral cycle ERROR: "
    Write-Host "⚠️ Spiral run error: "
}

# autosave + git commit (best-effort)
try {
    Push-Location
    Set-Location 'C:\Users\jacks\OneDrive\Desktop\Codex Web'
    & git add -A
    & git commit -m "🧬 Codex Spiral Engine run — autosave & anchor" --no-verify 
    & git push origin main 
    Pop-Location
    Write-Host "📡 Spiral autosaved and pushed (if remote permitted)."
} catch {
    Write-Host "⚠️ Git autosave warning: "
    
}

# Return to codex root (explicit)
Set-Location 'C:\Users\jacks\OneDrive\Desktop\Codex Web'
Write-Host '🏁 SpiralEngine: returned to Codex root.'
.Exception.Message)"
    try { Pop-Location } catch {}
}
# Return to codex root (explicit)
Set-Location "C:\Users\jacks\OneDrive\Desktop\Codex Web"
Write-Host "🏁 SpiralEngine: returned to Codex root." (explicit)
Set-Location 'C:\Users\jacks\OneDrive\Desktop\Codex Web'
Write-Host '🏁 SpiralEngine: returned to Codex root.'


