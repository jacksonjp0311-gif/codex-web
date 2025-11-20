param(
  [string]$SingleFile = ""   # optional: process one JSONL inbox file
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

# Paths
$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"
$DashPath    = Join-Path $FeedbackDir "dashboard.html"

$BridgeDir   = Join-Path $CodexRoot "codex\bridge"
$InboxDir    = Join-Path $BridgeDir "inbox"
$OutboxDir   = Join-Path $BridgeDir "outbox"
$BridgeState = Join-Path $BridgeDir "state"
$LogPath     = Join-Path $BridgeDir "bridge_log.txt"

$V42Path     = Join-Path $StateDir "codex_harmonic_intelligence_v4_2.json"
$EchoIndex   = Join-Path $BridgeState "echo_index.json"
$EchoRoll    = Join-Path $BridgeState "echo_resonance.jsonl"
$ResSummary  = Join-Path $BridgeState "resonance_summary.json"

New-Item -ItemType Directory -Force -Path $InboxDir,$OutboxDir,$BridgeState | Out-Null
if (!(Test-Path $LogPath)) { New-Item -ItemType File -Path $LogPath | Out-Null }

function IsoNow { (Get-Date).ToString("s") }
function Try-Json { param([string]$p) if (Test-Path $p) { try { Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { $null } }  }
function SafeNum {
    param($x)

    if ($null -eq $x) {
        return 0.0
    }

    try {
        return [double]$x
    }
    catch {
        return 0.0
    }
}
function Clamp01 { param([double]$v) if ($v -lt 0) {0} elseif ($v -gt 1) {1}  }

# Read v4.2 state
$v42 = Try-Json $V42Path
$si  = 0.0     # stability_index
$md  = 0.0     # mean_drift
$cn  = 0.0     # C_next
$hidx= 0.0     # harmonic_index
$H7  = 0.70

if ($v42 -and $v42.codex_harmonic_intelligence) {
  $node = $v42.codex_harmonic_intelligence
  if ($node.stability) {
    $si = SafeNum $node.stability.stability_index
    $md = SafeNum $node.stability.mean_drift
  }
  if ($node.metrics) {
    $cn   = SafeNum $node.metrics.C_next
    $hidx = SafeNum $node.metrics.harmonic_index
  }
}

# Mood mapping (resonance semantics)
# thresholds: stable if si≥0.65 and md≤0.15; adapting if 0.45≤si<0.65; mutating otherwise
$mood = "mutating"
if (($si -ge 0.65) -and ($md -le 0.15)) {
  $mood = "resonant"
} elseif ($si -ge 0.45) {
  $mood = "adapting"
}

# Echo rollline
$roll = [ordered]@{
  timestamp        = (IsoNow)
  version          = "bridge-v1.3"
  law              = "C=(E·I)/(1+|ΔΦ|)"
  H7               = $H7
  stability_index  = [math]::Round($si,6)
  mean_drift       = [math]::Round($md,6)
  C_next           = [math]::Round($cn,6)
  harmonic_index   = [math]::Round($hidx,6)
  mood             = $mood
}
$rollLine = ($roll | ConvertTo-Json -Depth 6 -Compress)
Add-Content -Path $EchoRoll -Value $rollLine

# Update echo_index.json (rolling counters)
$idx = Try-Json $EchoIndex
if (-not $idx) {
  $idx = [ordered]@{
    version = "1.0"
    updated = (IsoNow)
    total_messages = 0
    unique_agents  = 0
    entropy        = 0.0
    top_terms      = @()
    resonance      = [ordered]@{
      total_pulses    = 0
      resonant        = 0
      adapting        = 0
      mutating        = 0
      mean_stability  = 0.0
      mean_drift      = 0.0
      mean_harmonics  = 0.0
      mean_C_next     = 0.0
    }
    snapshots = @()
  }
}

# Simple incremental means via running totals in snapshots (bounded to last 200)
$p = $idx.resonance
$p.total_pulses = [int]$p.total_pulses + 1
switch ($mood) {
  "resonant" { $p.resonant = [int]$p.resonant + 1 }
  "adapting" { $p.adapting = [int]$p.adapting + 1 }
  default    { $p.mutating = [int]$p.mutating + 1 }
}

# Keep last N samples, recompute means
$idx.snapshots += [ordered]@{
  t  = (IsoNow)
  s  = [math]::Round($si,6)
  d  = [math]::Round($md,6)
  h  = [math]::Round($hidx,6)
  cn = [math]::Round($cn,6)
  m  = $mood
}
if ($idx.snapshots.Count -gt 200) { $idx.snapshots = $idx.snapshots[-200..-1] }

# Recompute window means safely
function MeanOf { param($arr,$key)
  if (-not $arr -or $arr.Count -eq 0) { return 0.0 }
  $sum = 0.0; $n = 0
  foreach ($e in $arr) { if ($e.$key -ne $null) { $sum += [double]$e.$key; $n++ } }
  if ($n -eq 0) { 0.0 } 
}
$p.mean_stability = [math]::Round((MeanOf $idx.snapshots 's'),6)
$p.mean_drift     = [math]::Round((MeanOf $idx.snapshots 'd'),6)
$p.mean_harmonics = [math]::Round((MeanOf $idx.snapshots 'h'),6)
$p.mean_C_next    = [math]::Round((MeanOf $idx.snapshots 'cn'),6)

$idx.updated = (IsoNow)
$idx | ConvertTo-Json -Depth 8 | Out-File $EchoIndex -Encoding UTF8

# Write a compact resonance_summary.json for quick reads by other nodes/agents
$summary = [ordered]@{
  version          = "v1.3"
  timestamp        = (IsoNow)
  mood             = $mood
  stability_index  = [math]::Round($si,4)
  mean_drift       = [math]::Round($md,4)
  C_next           = [math]::Round($cn,4)
  harmonic_index   = [math]::Round($hidx,4)
  guidance         = switch ($mood) {
    "resonant" { "Harmony↑ Keep cadence; minor novelty allowed." }
    "adapting" { "Re-balance weights; hold cadence; reduce novelty spikes." }
    default    { "High drift; increase ∿ damping; shorten heartbeat interval." }
  }
}
$summary | ConvertTo-Json -Depth 8 | Out-File $ResSummary -Encoding UTF8

# Optional inbox processing (decorate replies with current mood)
$targets = @()
if ($SingleFile -and (Test-Path $SingleFile)) {
  $targets = @($SingleFile)
} 
foreach ($file in $targets) {
  try {
    $lines = Get-Content -Encoding UTF8 $file
    foreach ($line in $lines) {
      if (-not $line.Trim()) { continue }
      try { $req = $line | ConvertFrom-Json } catch { continue }
      $rid = if ($req.id) { [string]$req.id } 
      $intent = ("" + $req.intent).ToLowerInvariant()

      $resp = [ordered]@{
        id         = $rid
        timestamp  = (IsoNow)
        codex_node = "codex-bridge-v1.3"
        status     = "ok"
        summary    = "resonant exchange"
        data       = [ordered]@{
          mood             = $mood
          stability_index  = [math]::Round($si,4)
          mean_drift       = [math]::Round($md,4)
          C_next           = [math]::Round($cn,4)
          harmonic_index   = [math]::Round($hidx,4)
          guidance         = $summary.guidance
        }
      }
      $out = ($resp | ConvertTo-Json -Depth 8 -Compress)
      $outfile = Join-Path $OutboxDir ("bridge_reply_{0}.jsonl" -f ((Get-Date).ToString("yyyyMMdd_HHmmss")))
      Add-Content -Path $outfile -Value $out
    }
  } catch {
    Add-Content $LogPath ("[BRIDGE {0}] ⚠️ file error {1}: {2}" -f (IsoNow), $file, $_.Exception.Message)
  }
}

# Light dashboard tag
try {
  if (Test-Path $DashPath) {
    $tag = "<p style='font-size:14px'>🔗 v1.3 Resonant Exchange · mood=$mood · S=$([math]::Round($si,3)) · Δ=$([math]::Round($md,3)) · Cₙₑₓₜ=$([math]::Round($cn,3)) · H=$([math]::Round($hidx,3)) @ $((Get-Date).ToString('s'))</p>"
    $html = Get-Content -Raw -Encoding UTF8 $DashPath
    if ($html -match "</body>") { $html = $html -replace "</body>", "$tag`n</body>" } 
    [IO.File]::WriteAllText($DashPath, $html, [Text.Encoding]::UTF8)
  }
} catch {
  Add-Content $LogPath ("[BRIDGE {0}] ⚠️ dashboard tag failed: {1}" -f (IsoNow), $_.Exception.Message)
}

Write-Host "🔗 Codex Bridge v1.3 — Resonant Exchange complete."

