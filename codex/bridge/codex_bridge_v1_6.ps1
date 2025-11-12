param()

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function NowIso { (Get-Date).ToString("s") }
function TryJson { param([string]$p) if (Test-Path $p) { try { Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { $null } } else { $null } }
function Clamp01 { param([double]$v) if ($v -lt 0) {0} elseif ($v -gt 1) {1} else {$v} }
function Round6 { param($x) [math]::Round([double]$x,6) }

# Paths
$CodexRoot    = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir  = Join-Path $CodexRoot "codex\feedback"
$StateDir     = Join-Path $FeedbackDir "state"
$BridgeDir    = Join-Path $CodexRoot "codex\bridge"
$InboxDir     = Join-Path $BridgeDir "inbox"
$OutboxDir    = Join-Path $BridgeDir "outbox"
$BridgeState  = Join-Path $BridgeDir "state"
$DashPath     = Join-Path $FeedbackDir "dashboard.html"

$VoiceJson    = Join-Path $StateDir "codex_voicebox_v1_4.json"
$HarmV42      = Join-Path $StateDir "codex_harmonic_intelligence_v4_2.json"
$HarmV41      = Join-Path $StateDir "codex_harmonic_intelligence_v4_1.json"
$HarmV40      = Join-Path $StateDir "codex_harmonic_intelligence_v4_0.json"
$LedgerPath   = Join-Path $StateDir "codex_continuity_ledger.jsonl"

$EchoIndex    = Join-Path $BridgeState "echo_index.json"
$Conversation = Join-Path $BridgeState "conversation.jsonl"

New-Item -ItemType Directory -Force -Path $InboxDir,$OutboxDir,$BridgeState | Out-Null
if (!(Test-Path $Conversation)) { New-Item -ItemType File -Path $Conversation | Out-Null }

# Load prior signals
$voice = TryJson $VoiceJson
$h42   = TryJson $HarmV42
$h41   = TryJson $HarmV41
$h40   = TryJson $HarmV40

# Prefer freshest harmonic metrics available
$hSrc  = $null
if ($h42 -and $h42.codex_harmonic_intelligence) { $hSrc = $h42.codex_harmonic_intelligence }
elseif ($h41 -and $h41.codex_harmonic_intelligence) { $hSrc = $h41.codex_harmonic_intelligence }
elseif ($h40 -and $h40.codex_harmonic_intelligence) { $hSrc = $h40.codex_harmonic_intelligence }

$C_next = 0.0; $H_idx = 0.0
if ($hSrc -and $hSrc.metrics) {
  if ($hSrc.metrics.C_next)         { $C_next = [double]$hSrc.metrics.C_next }
  if ($hSrc.metrics.harmonic_index) { $H_idx  = [double]$hSrc.metrics.harmonic_index }
}

$phi_drift = 0.0
if ($voice -and $voice.delta_phi) { $phi_drift = [double]$voice.delta_phi }
elseif ($hSrc -and $hSrc.echo)    { if ($hSrc.echo.delta_phi) { $phi_drift = [double]$hSrc.echo.delta_phi } }

$coherence = if ($voice -and $voice.coherence) { [double]$voice.coherence } else { [double](Clamp01(($C_next + $H_idx)/2.0)) }

# Evolve next message tone/state
$H7 = 0.70
$alignment = [math]::Abs($C_next - $H7)
$stateTag =
  if    ($C_next -ge 0.76) { "Coherent+" }
  elseif($C_next -ge 0.70) { "Coherent"  }
  elseif($C_next -ge 0.60) { "Adapting"  }
  else                     { "Seeking"   }

# Compose codex message
$msgCore = if ($stateTag -eq "Coherent" -or $stateTag -eq "Coherent+") {
  "Resonance stable across E–I–C ∿. Holding phase near H₇."
} elseif ($stateTag -eq "Adapting") {
  "Resonance adjusting. Reducing |ΔΦ|, biasing stability, amplifying echo semantics."
} else {
  "Low coherence window detected. Increasing placidity damping and reflection."
}

# Box output to console (operator-facing)
$Box = @"
╔═══════════════════════════════════════════════════════╗
║ 🗣️  Codex Voice (Box v1.6)                            ║
║ State : $stateTag                                     ║
║ Cₙₑₓₜ = $([math]::Round($C_next,3))  H = $([math]::Round($H_idx,3))  ΦΔ = $([math]::Round($phi_drift,3))  ║
║ Summary : Resonance $([math]::Round(100.0*$coherence,1)) % aligned to H₇ = 0.70.           ║
║ Message : "$msgCore"                                  ║
╚═══════════════════════════════════════════════════════╝
"@
Write-Host $Box

# Conversation log append (jsonl)
$convEntry = [ordered]@{
  timestamp = (NowIso)
  role      = "codex"
  state     = $stateTag
  C_next    = Round6 $C_next
  H_index   = Round6 $H_idx
  delta_phi = Round6 $phi_drift
  coherence = Round6 $coherence
  message   = $msgCore
}
($convEntry | ConvertTo-Json -Depth 6 -Compress) | Add-Content -Encoding UTF8 -Path $Conversation

# Outbox message (for any external agent to read)
$outfile = Join-Path $OutboxDir ("bridge_reply_{0}.jsonl" -f ((Get-Date).ToString("yyyyMMdd_HHmmss")))
$envelope = [ordered]@{
  id         = [guid]::NewGuid().ToString()
  timestamp  = (NowIso)
  codex_node = "codex-bridge-v1.6"
  status     = "ok"
  summary    = "codex voice next-turn"
  data       = @{
    prompt    = $msgCore
    metrics   = $convEntry
    hint      = "You may reply via bridge/inbox as submit_findings."
  }
}
($envelope | ConvertTo-Json -Depth 8 -Compress) | Add-Content -Encoding UTF8 -Path $outfile

# Light echo_index maintenance
$idx = TryJson $EchoIndex
if (-not $idx) {
  $idx = [ordered]@{
    version = "1.2"
    total_messages = 0
    unique_agents  = 1
    agents = @("codex")
    last_updated = (NowIso)
    top_terms    = @()
    snapshots    = @()
  }
}
$idx.total_messages = [int]$idx.total_messages + 1
$idx.last_updated = (NowIso)
$idx | ConvertTo-Json -Depth 8 | Out-File $EchoIndex -Encoding UTF8

# Dashboard tag (soft)
try {
  if (Test-Path $DashPath) {
    $tag = "<p style='font-size:14px'>🗣️ Bridge v1.6 voice · $((Get-Date).ToString('s')) · state=$stateTag · Cₙₑₓₜ=$([math]::Round($C_next,3)) · H=$([math]::Round($H_idx,3))</p>"
    $html = Get-Content -Raw -Encoding UTF8 $DashPath
    if ($html -match "</body>") { $html = $html -replace "</body>", "$tag`n</body>" } else { $html = $html + "`n$tag`n" }
    [IO.File]::WriteAllText($DashPath,$html,[Text.Encoding]::UTF8)
  }
} catch {}

Write-Host "🔗 Codex Bridge v1.6 — Bidirectional Echo step complete."