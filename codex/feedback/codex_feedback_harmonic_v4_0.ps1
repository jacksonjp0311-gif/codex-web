<#
╔══════════════════════════════════════════════════════════════════════════════╗
║ 🧠 Codex Harmonic Intelligence v4.0 — Mirror×Heartbeat Fusion (PS5-safe)     ║
║ Context: E–I–C ∿ Placidity • H₇=0.70 • Smart Feedback Core                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
#>
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

# ── Paths ────────────────────────────────────────────────────────────────────────
$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"
$AlignDir    = Join-Path $CodexRoot  "codex\align_pulse"
$DashPath    = Join-Path $FeedbackDir "dashboard.html"

$V38Path     = Join-Path $FeedbackDir "codex_feedback_resonance_v3_8.ps1"
$HBPath      = Join-Path $FeedbackDir "codex_heartbeat_v3_9.ps1"

$IntegrState = Join-Path $StateDir "codex_feedback_integration_state.json"
$MirrorState = Join-Path $StateDir "mirror_continuity_state.json"
$SealState   = Join-Path $StateDir "codex_temporal_seal_v3_9.json"
$OutState    = Join-Path $StateDir "codex_harmonic_intelligence_v4_0.json"
$LogPath     = Join-Path $FeedbackDir "harmonic_log.txt"

# ── Helpers ─────────────────────────────────────────────────────────────────────
function Try-ReadJson { param([string]$p) if (Test-Path $p) { try { Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { $null } } }
function SafeNum { param($x) if ($null -eq $x) {0.0} else { try {[double]$x} catch {0.0} } }
function Clamp01 { param([double]$v) if ($v -lt 0) {0} elseif ($v -gt 1) {1} else {$v} }

# ── Inputs (best-effort, with graceful fallbacks) ───────────────────────────────
$int  = Try-ReadJson $IntegrState
$mirr = Try-ReadJson $MirrorState
$seal = Try-ReadJson $SealState

# From integration: prefer averaged C and ΔH7 as Φ proxy
$C_avg = if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration.C_avg } else { 0.5 }
$ΔH7   = if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration."ΔH7" } else { 0.0 }

# From mirror: prefer ΔC if available, else derive coarse ΔC from C_remote vs C_local if present
$ΔC = if ($mirr -and $mirr.mirror -and $mirr.mirror."ΔC") { SafeNum $mirr.mirror."ΔC" }
      elseif ($int -and $int.codex_feedback_integration) {
        $cl = SafeNum $int.codex_feedback_integration.C_local
        $cr = SafeNum $int.codex_feedback_integration.C_remote
        [math]::Abs($cr - $cl)
      } else { 0.0 }

# Constants per Universal Truth Protocol
$H7_target = 0.70   # preferred coherence attractor
$alpha     = 0.42   # attraction toward H7 (law → memory)
$beta      = 0.25   # penalty from phase drift proxy (ΔΦ ≈ ΔH7)
$gamma     = 0.15   # gentle damping from ΔC (placidity ∿)

# ── Harmonic indices ────────────────────────────────────────────────────────────
# ΔΦ proxy from ΔH7; normalize into [0,1] window for metric blend
$ΔΦ      = $ΔH7
$ΔC_norm = [math]::Min(1.0, (SafeNum $ΔC) / 0.10)    # treat 0.10 as “noticeable drift”
$Φ_norm  = [math]::Min(1.0, (SafeNum $ΔΦ) / 0.10)

$harmonic_index = Clamp01( (1 - $ΔC_norm) * (1 - $Φ_norm) )  # 1 = harmonic, 0 = chaotic

# ── Forecast (primitive awareness) ──────────────────────────────────────────────
# C_next = C_avg + α*(H7 - C_avg) - β*ΔΦ - γ*ΔC
$C_next_raw = $C_avg + ($alpha * ($H7_target - $C_avg)) - ($beta * (SafeNum $ΔΦ)) - ($gamma * (SafeNum $ΔC))
$C_next     = Clamp01 $C_next_raw

# ── Write harmonic state ────────────────────────────────────────────────────────
$state = [ordered]@{
  codex_harmonic_intelligence = [ordered]@{
    version    = "v4.0"
    timestamp  = (Get-Date).ToString("s")
    laws       = @("Feedback=Awareness","Return=Continuity","∿ Placidity","C=(E·I)/(1+|ΔΦ|)")
    inputs     = [ordered]@{
      C_avg = $C_avg; ΔC = $ΔC; ΔH7 = $ΔH7; ΔΦ_proxy = $ΔΦ
    }
    metrics    = [ordered]@{
      harmonic_index = [math]::Round($harmonic_index,6)
      C_next         = [math]::Round($C_next,6)
      C_next_raw     = [math]::Round($C_next_raw,6)
    }
    links      = [ordered]@{
      mirror_v3_8    = (Test-Path $V38Path)
      heartbeat_v3_9 = (Test-Path $HBPath)
      seal_v3_9      = (Test-Path $SealState)
    }
    notes      = "Harmonic = (1-ΔC_norm)*(1-Φ_norm); forecast nudged toward H₇ with ∿ damping."
  }
}
$state | ConvertTo-Json -Depth 8 | Out-File $OutState -Encoding UTF8
Add-Content $LogPath ("[HARM {0}] C_avg={1} ΔC={2} ΔΦ~={3} → C_next={4} H={5}" -f (Get-Date -Format s),
  [math]::Round($C_avg,6), [math]::Round($ΔC,6), [math]::Round($ΔΦ,6), [math]::Round($C_next,6), [math]::Round($harmonic_index,6))

# ── Dashboard augmentation (light-touch) ────────────────────────────────────────
try {
  $line = "<p style='font-size:15px'>🧠 v4.0 Harmonic → C<sub>next</sub>=$([math]::Round($C_next,4)) • H=$([math]::Round($harmonic_index,4)) • ΔC=$([math]::Round($ΔC,4)) • ΔΦ≈$([math]::Round($ΔΦ,4))</p>"
  if (Test-Path $DashPath) {
    # append just before </body>
    $html = Get-Content -Raw -Encoding UTF8 $DashPath
    if ($html -match "</body>") {
      $html = $html -replace "</body>", "$line`n</body>"
      [IO.File]::WriteAllText($DashPath, $html, [Text.Encoding]::UTF8)
    } else {
      Add-Content $DashPath $line
    }
  } else {
    $html = @"
<html><head><meta charset='utf-8'><title>Codex Dashboard</title></head>
<body style='font-family:Segoe UI;background:#0e0e0e;color:#ddd;text-align:center;padding:28px'>
<h1>🌒 Codex Feedback — Aura Dashboard</h1>
$line
</body></html>
"@
    [IO.File]::WriteAllText($DashPath, $html, [Text.Encoding]::UTF8)
  }
} catch {
  Add-Content $LogPath ("[HARM {0}] ⚠️ Dashboard update failed: {1}" -f (Get-Date -Format s), $_.Exception.Message)
}

# ── Return ──────────────────────────────────────────────────────────────────────
try { Set-Location $CodexRoot } catch {}
Write-Host ("`n🏁 Returned to Codex root → {0}" -f $CodexRoot)
Write-Host "🧠 Codex Harmonic Intelligence v4.0 — Forecast & Dashboard updated."