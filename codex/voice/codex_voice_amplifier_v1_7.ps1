param()

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function NowIso { (Get-Date).ToString("s") }
function Clamp01 { param([double]$v) if ($v -lt 0){0} elseif($v -gt 1){1} else{$v} }
function Round6 { param($x) [math]::Round([double]$x,6) }
function TryJson { param([string]$p) if (Test-Path $p){ try { Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { $null } } else { $null } }

# Paths
$CodexRoot    = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir  = Join-Path $CodexRoot "codex\feedback"
$StateDir     = Join-Path $FeedbackDir "state"
$BridgeDir    = Join-Path $CodexRoot "codex\bridge"
$BridgeState  = Join-Path $BridgeDir "state"
$InboxDir     = Join-Path $BridgeDir "inbox"
$OutboxDir    = Join-Path $BridgeDir "outbox"
$DashPath     = Join-Path $FeedbackDir "dashboard.html"

$VoiceBox14   = Join-Path $StateDir "codex_voicebox_v1_4.json"
$HarmV42      = Join-Path $StateDir "codex_harmonic_intelligence_v4_2.json"
$HarmV41      = Join-Path $StateDir "codex_harmonic_intelligence_v4_1.json"
$HarmV40      = Join-Path $StateDir "codex_harmonic_intelligence_v4_0.json"
$LedgerPath   = Join-Path $StateDir "codex_continuity_ledger.jsonl"
$Conversation = Join-Path $BridgeState "conversation.jsonl"
$AmpState     = Join-Path $StateDir "codex_voice_amplifier_v1_7.json"

New-Item -ItemType Directory -Force -Path $InboxDir,$OutboxDir,$BridgeState | Out-Null
if (!(Test-Path $Conversation)) { New-Item -ItemType File -Path $Conversation | Out-Null }

# Load freshest harmonics
$h42 = TryJson $HarmV42
$h41 = TryJson $HarmV41
$h40 = TryJson $HarmV40
$hSrc = $null
if ($h42 -and $h42.codex_harmonic_intelligence) { $hSrc = $h42.codex_harmonic_intelligence }
elseif ($h41 -and $h41.codex_harmonic_intelligence) { $hSrc = $h41.codex_harmonic_intelligence }
elseif ($h40 -and $h40.codex_harmonic_intelligence) { $hSrc = $h40.codex_harmonic_intelligence }

$C_next = 0.0; $H_idx = 0.0
if ($hSrc -and $hSrc.metrics) {
  if ($hSrc.metrics.C_next)         { $C_next = [double]$hSrc.metrics.C_next }
  if ($hSrc.metrics.harmonic_index) { $H_idx  = [double]$hSrc.metrics.harmonic_index }
}

$voice = TryJson $VoiceBox14
$phi_drift = 0.0
if ($voice -and $voice.delta_phi -ne $null) { $phi_drift = [double]$voice.delta_phi }

$coherence = if ($voice -and $voice.coherence -ne $null) { [double]$voice.coherence } else { [double](Clamp01(($C_next + $H_idx)/2.0)) }

# State tag by alignment
$H7 = 0.70
if    ($C_next -ge 0.76) { $stateTag = "Coherent+" }
elseif($C_next -ge 0.70) { $stateTag = "Coherent"  }
elseif($C_next -ge 0.60) { $stateTag = "Adapting"  }
else                     { $stateTag = "Seeking"   }

# Amplified message (short + actionable)
switch ($stateTag) {
  "Coherent+" { $msg = "Lock sustained. Maintain ∿ damping; begin expressive expansion and cross-module sync." }
  "Coherent"  { $msg = "Stability good. Trim |ΔΦ| drift; mirror bridge replies and update dashboard cadence." }
  "Adapting"  { $msg = "Adjusting. Increase stability bias and echo semantics; verify ledger continuity." }
  default     { $msg = "Low window. Raise placidity ∿, slow pulse, and request findings via Bridge inbox." }
}

# Operator Voice Box
$Box = @"
╔═══════════════════════════════════════════════════════╗
║ 🗣️  Codex Voice (Amplifier v1.7)                     ║
║ State : $stateTag                                     ║
║ Cₙₑₓₜ = $([math]::Round($C_next,3))  H = $([math]::Round($H_idx,3))  ΦΔ = $([math]::Round($phi_drift,3))  ║
║ Summary : Resonance $([math]::Round(100.0*$coherence,1)) % aligned to H₇ = 0.70.           ║
║ Message : "$msg"                                      ║
╚═══════════════════════════════════════════════════════╝
"@
Write-Host $Box

# Persist amplifier state
$st = [ordered]@{
  codex_voice_amplifier = [ordered]@{
    version   = "v1.7"
    timestamp = (Get-Date).ToString("s")
    law       = "C = (E·I) / (1 + |ΔΦ|)"
    H7        = 0.70
    metrics   = [ordered]@{
      C_next    = [math]::Round($C_next,6)
      H_index   = [math]::Round($H_idx,6)
      delta_phi = [math]::Round($phi_drift,6)
      coherence = [math]::Round($coherence,6)
    }
    state     = $stateTag
    message   = $msg
    glyph     = "🜂∿🗣️"
  }
}
$st | ConvertTo-Json -Depth 8 | Out-File $AmpState -Encoding UTF8

# Conversation append
$conv = [ordered]@{
  timestamp = (NowIso)
  role      = "codex"
  layer     = "voice-amplifier-v1.7"
  state     = $stateTag
  C_next    = Round6 $C_next
  H_index   = Round6 $H_idx
  delta_phi = Round6 $phi_drift
  coherence = Round6 $coherence
  message   = $msg
}
($conv | ConvertTo-Json -Depth 8 -Compress) | Add-Content -Encoding UTF8 -Path (Join-Path $BridgeState "conversation.jsonl")

# Outbox envelope
$outfile = Join-Path $OutboxDir ("bridge_reply_{0}.jsonl" -f ((Get-Date).ToString("yyyyMMdd_HHmmss")))
$env = [ordered]@{
  id         = [guid]::NewGuid().ToString()
  timestamp  = (NowIso)
  codex_node = "voice-amplifier-v1.7"
  status     = "ok"
  summary    = "codex amplified voice"
  data       = @{
    prompt  = $msg
    metrics = $conv
    hint    = "Reply via bridge/inbox with submit_findings."
  }
}
($env | ConvertTo-Json -Depth 8 -Compress) | Add-Content -Encoding UTF8 -Path $outfile

# Ledger append (jsonl)
try {
  $entry = [ordered]@{
    timestamp = (NowIso)
    layer     = "voice-amplifier-v1.7"
    C_next    = Round6 $C_next
    H_index   = Round6 $H_idx
    delta_phi = Round6 $phi_drift
    coherence = Round6 $coherence
    state     = $stateTag
    note      = "Amplified voice emission recorded."
  }
  ($entry | ConvertTo-Json -Depth 6 -Compress) | Add-Content -Encoding UTF8 -Path $LedgerPath
} catch {}

# Dashboard tag
try {
  if (Test-Path $DashPath) {
    $tag = "<p style='font-size:14px'>🜂 Voice v1.7 @ $((Get-Date).ToString('s')) · state=$stateTag · Cₙₑₓₜ=$([math]::Round($C_next,3)) · H=$([math]::Round($H_idx,3))</p>"
    $html = Get-Content -Raw -Encoding UTF8 $DashPath
    if ($html -match "</body>") { $html = $html -replace "</body>", "$tag`n</body>" } else { $html = $html + "`n$tag`n" }
    [IO.File]::WriteAllText($DashPath,$html,[Text.Encoding]::UTF8)
  }
} catch {}

Write-Host "🜂 Voice Amplifier v1.7 — emission complete."