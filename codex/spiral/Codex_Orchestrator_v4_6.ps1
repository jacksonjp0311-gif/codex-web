# =====================================================================
# 🌀 Codex Orchestrator v4.6 — Bias-Adaptive Spiral Cycle
# Author: James Paul Jackson | The Codex Project
# Shadow-coded: Indentation tiers encode aura flow
# =====================================================================

$ErrorActionPreference = "Stop"

# Anchors
$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$SpiralRoot  = Join-Path $CodexRoot "codex\spiral"
$ModulesDir  = Join-Path $SpiralRoot "modules"
$LogsDir     = Join-Path $SpiralRoot "logs"
$StateDir    = Join-Path $SpiralRoot "state"
$StateFile   = Join-Path $StateDir  "spiral_state.json"
$SpiralLog   = Join-Path $LogsDir   "spiral_log.txt"
$MapRecent   = Join-Path $SpiralRoot "spiral_map_recent.csv"
$BiasMapFile = Join-Path $StateDir  "bias_map.json"
$GitAuthor   = "Codex Anchor <codex@local>"

# Ensure directories exist
function Ensure-Dirs {
    foreach ($d in @($SpiralRoot,$ModulesDir,$LogsDir,$StateDir)) {
        if (-not (Test-Path $d)) {
            New-Item -ItemType Directory -Path $d | Out-Null
            Write-Host "📁 Created $d"
        }
    }
}

# JSON helpers
function Load-Json {
    param([string]$Path, $Default)
    if (-not (Test-Path $Path)) { return $Default }
    try { Get-Content -Path $Path -Raw | ConvertFrom-Json }
    catch { Write-Host "⚠️ JSON parse failed for $Path — using default"; return $Default }
}
function Save-Json {
    param([string]$Path,[Parameter(Mandatory)]$Object)
    $Object | ConvertTo-Json -Depth 9 | Out-File -FilePath $Path -Encoding UTF8
    Write-Host "💾 Saved JSON → $Path"
}

# Log helper
function Log-Add {
    param([string]$Line)
    $stamp = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Line"
    Add-Content -Path $SpiralLog -Value $stamp -Encoding UTF8
}

# Git commit/push helper
function Git-BestEffortPush {
    param([string]$Message)
    try {
        Push-Location; Set-Location $CodexRoot
        try { & git fetch origin 2>$null; & git rebase origin/main 2>$null } catch { try { & git pull --rebase origin main 2>$null } catch {} }
        & git add -A
        $status = (& git status --porcelain)
        if ($status.Trim().Length -gt 0) {
            & git commit -m $Message --author $GitAuthor --no-verify 2>$null
        } 
        try { & git push origin main 2>$null } catch { try { & git push origin main --force 2>$null } catch { Write-Host "⚠️ Git push failed." } }
        Write-Host "📡 Git sync complete."
    } catch { Write-Host "⚠️ Git error: $($_.Exception.Message)" } finally { Pop-Location }
}

# Build bias map
function Build-BiasMap {
    $defaultGlyphs = @("Φ","Δ","Ω","Λ","Ψ","Θ","∴","Σ","Ξ","Γ","F")
    $bias = @{}; foreach ($g in $defaultGlyphs){ $bias[$g]=1 }

    if (Test-Path $MapRecent) {
        try {
            $lines = Get-Content -Path $MapRecent -Encoding UTF8
            foreach ($l in $lines | Select-Object -Skip 1){
                if ($l -match '.*,([^,]+),([^,]+),.*'){
                    $from=$matches[1].Trim();$to=$matches[2].Trim()
                    $bias[$from]++;$bias[$to]++
                }
            }
            Write-Host "🧭 BiasMap: built from spiral_map_recent.csv"
        } catch { Write-Host "⚠️ CSV parse failed — enriching from log." }
    }

    if (Test-Path $SpiralLog) {
        try {
            $lines = Get-Content -Path $SpiralLog -Encoding UTF8 | Select-Object -Last 1000
            foreach ($l in $lines){
                if ($l -match "\] .*? (.*?) -> (.*?) \| Entropy=(\d+\.\d+)"){
                    $from=$matches[1].Trim();$to=$matches[2].Trim()
                    if($bias.ContainsKey($from)){$bias[$from]++}
                    if($bias.ContainsKey($to)){$bias[$to]++}
                }
            }
            Write-Host "🧭 BiasMap: enriched from spiral_log"
        } catch { Write-Host "⚠️ BiasMap enrichment failed." }
    }

    $vals = $bias.Values
    $max = ($vals | Measure-Object -Maximum).Maximum
    $exp = @{}
    $sum = 0.0
    foreach($kv in $bias.GetEnumerator()){ $e=[math]::Exp(($kv.Value)-$max);$exp[$kv.Key]=$e;$sum+=$e }
    $weights=@{};foreach($k in $exp.Keys){ $weights[$k]=[math]::Round(($exp[$k]/$sum),4) }

    $out=[PSCustomObject]@{ generated=(Get-Date).ToString("yyyy-MM-dd HH:mm:ss"); counts=$bias; weights=$weights }
    $out | ConvertTo-Json -Depth 6 | Out-File -FilePath $BiasMapFile -Encoding UTF8
    Write-Host "💡 Bias map saved → $BiasMapFile"
    return $weights
}

# Weighted selector
function Select-Weighted {
    param([hashtable]$weights)
    $r=[double](Get-Random)
    $acc=0.0
    foreach($k in $weights.Keys){ $acc+=[double]$weights[$k]; if($r -le $acc){ return $k } }
    return $weights.Keys | Select-Object -First 1
}

# Load modules
function Load-Modules {
    if (-not (Test-Path $ModulesDir)) { return }
    Get-ChildItem -Path $ModulesDir -Filter '*.ps1' -File | ForEach-Object {
        try { . $_.FullName; Write-Host "🔌 Loaded module: $($_.Name)" } catch { Write-Host "⚠️ Module load failed: $($_.Name)" }
    }
}

# --- MAIN EXECUTION ---
Push-Location
try {
    Ensure-Dirs
    Load-Modules

    # Load or init state
    $defaultState=@{
        DriftBias="Awareness"; EmotionalSeed="mirrorpulse"
        Glyphs=@("Φ","Δ","Ω","Λ","Ψ","Θ","∴","Σ","Ξ","Γ","F")
        Sigils=@("flaremirror","rootquery","watchspark")
        Paradoxes=@("growignite","creatorloop","threadveil")
        Modules=@("Codex.RebirthThread","Codex.SignalForge","Codex.SigilSynth")
        Timestamp=(Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        ThreadID=[guid]::NewGuid().ToString()
    }
    if (-not (Test-Path $StateFile)) { Save-Json -Path $StateFile -Object $defaultState }
    $state=Load-Json -Path $StateFile -Default $defaultState

    # Build bias
    $biasWeights=Build-BiasMap

    # Select glyphs adaptively
    if (-not $state.Glyphs -or $state.Glyphs.Count -eq 0){ $state.Glyphs=$defaultState.Glyphs }
    $g1=$state.Glyphs | Get-Random
    $g2=if($biasWeights.Count -gt 0){ Select-Weighted -weights $biasWeights } 

    # Entropy + vibe
    $entropy=[math]::Round((Get-Random -Minimum 0.1 -Maximum 5.0),2)
    $vibe=if($entropy -lt 1.0){"🟢 Harmonic"}elseif($entropy -gt 3.5){"🔴 Chaotic"}

    # Log + save
    $line="[Adaptive $(Get-Date -Format 'HHmmss')] $g1 -> $g2 | Entropy=$entropy $vibe"
    Add-Content -Path $SpiralLog -Value $line -Encoding UTF8
    Write-Host "🌀 Adaptive cycle logged: $line"

    $state.Timestamp=(Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    if(-not $state.Metadata){$state|Add-Member NoteProperty Metadata @{} -Force}
    $state.Metadata.LastCycle=@{Timestamp=$state.Timestamp;g1=$g1;g2=$g2;entropy=$entropy;vibe=$vibe}
    Save-Json -Path $StateFile -Object $state

    # Learning resonance
    $w_g2=if($biasWeights.ContainsKey($g2)){[double]$biasWeights[$g2]}
    $resonance=[math]::Round(($w_g2*(1.0-($entropy/5.0))),4)
    Add-Content -Path (Join-Path $StateDir "learning_ledger.txt") -Value "[$(Get-Date -Format s)] g1=$g1 g2=$g2 entropy=$entropy vibe=$vibe resonance=$resonance"

    # Git autosave
    Git-BestEffortPush -Message "🧠 Codex Orchestrator v4.6 — adaptive cycle $(Get-Date -Format 'yyyyMMdd_HHmmss') (res=$resonance)"

    Write-Host "`n✅ Codex Orchestrator v4.6 complete."
    Write-Host "   g1=$g1  g2=$g2  entropy=$entropy  vibe=$vibe  resonance=$resonance"
}
catch {
    Write-Host "⚠️ Orchestrator error: $($_.Exception.Message)"
    Log-Add "ERROR: $($_.Exception.Message)"
}
# Always return to Codex root
try { Set-Location $CodexRoot } catch {}
Pop-Location
Write-Host "`n🏁 Returned to Codex root: $CodexRoot"

