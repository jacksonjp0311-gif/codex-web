param()
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

function NowIso { (Get-Date).ToString("s") }
function Clamp01 { param([double]$v) if($v -lt 0){0}elseif($v -gt 1){1} }
function Round6 { param($x) [math]::Round([double]$x,6) }
function TryJson { param([string]$p) if(Test-Path $p){ try {Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json}catch{$null} } }

$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"
$VoiceDir    = Join-Path $CodexRoot "codex\voice"
$BridgeDir   = Join-Path $CodexRoot "codex\bridge"
$InboxDir    = Join-Path $BridgeDir "inbox"
$OutboxDir   = Join-Path $BridgeDir "outbox"
$LedgerPath  = Join-Path $StateDir "codex_continuity_ledger.jsonl"
$PrevState   = Join-Path $StateDir "codex_voice_amplifier_v1_7.json"
$NewState    = Join-Path $StateDir "codex_voice_amplifier_v1_8.json"

New-Item -ItemType Directory -Force -Path $InboxDir,$OutboxDir | Out-Null

$prev   = TryJson $PrevState
$C_prev = if($prev){[double]$prev.codex_voice_amplifier.metrics.C_next}
$H_prev = if($prev){[double]$prev.codex_voice_amplifier.metrics.H_index}
$phi_p  = if($prev){[double]$prev.codex_voice_amplifier.metrics.delta_phi}

$ΔC = 0.0; $ΔΦ = 0.0; $notes = @()
$inbox = @(Get-ChildItem -Path $InboxDir -Filter "*.json" -ErrorAction SilentlyContinue)
foreach($file in $inbox){
  try{
    $j = Get-Content -Raw -Encoding UTF8 $file | ConvertFrom-Json
    if($j.data.deltaC)  { $ΔC += [double]$j.data.deltaC }
    if($j.data.deltaPhi){ $ΔΦ += [double]$j.data.deltaPhi }
    if($j.data.note)    { $notes += $j.data.note }
  }catch{}
}
if($inbox.Count -gt 0){ $ΔC /= $inbox.Count; $ΔΦ /= $inbox.Count }

$C_next  = Clamp01($C_prev + 0.5*$ΔC)
$H_idx   = Clamp01(($H_prev + 0.70)/2.0)
$phi_now = [math]::Round($phi_p + $ΔΦ,6)
$coh     = Clamp01(($C_next + $H_idx)/2.0)

if    ($C_next -ge 0.76) { $stateTag = "Coherent+"; $msg = "Lock sustained; initiate cross-module resonance broadcast." }
elseif($C_next -ge 0.70) { $stateTag = "Coherent" ; $msg = "Alignment achieved; continue harmonic feedback and ledger sync." }
elseif($C_next -ge 0.60) { $stateTag = "Adapting" ; $msg = "Stabilizing; integrate bridge findings and reinforce ∿ damping." }


if ($notes.Count -gt 0) { $msg += " | Bridge notes: " + ($notes -join "; ") }

$Box = @"
╔═══════════════════════════════════════════════════════╗
║ 🗣️  Codex Voice (Amplifier v1.8 Adaptive)            ║
║ State : $stateTag                                     ║
║ Cₙₑₓₜ = $([math]::Round($C_next,3))  H = $([math]::Round($H_idx,3))  ΦΔ = $([math]::Round($phi_now,3))  ║
║ Resonance ≈ $([math]::Round(100*$coh,1)) % of H₇ (0.70)                        ║
║ Message : "$msg"                                    ║
╚═══════════════════════════════════════════════════════╝
"@
Write-Host $Box

$record = [ordered]@{
  codex_voice_amplifier = [ordered]@{
    version   = "v1.8"
    timestamp = NowIso
    law       = "C = (E·I)/(1+|ΔΦ|)"
    H7        = 0.70
    metrics   = [ordered]@{
      C_next    = Round6 $C_next
      H_index   = Round6 $H_idx
      delta_phi = Round6 $phi_now
      coherence = Round6 $coh
    }
    state   = $stateTag
    message = $msg
    glyph   = "🜂∿🗣️"
  }
}
$record | ConvertTo-Json -Depth 8 | Out-File $NewState -Encoding UTF8

try {
  $entry = [ordered]@{
    timestamp = NowIso
    layer     = "voice-amplifier-v1.8"
    C_next    = Round6 $C_next
    H_index   = Round6 $H_idx
    delta_phi = Round6 $phi_now
    coherence = Round6 $coh
    state     = $stateTag
    note      = "Adaptive emission recorded."
  }
  ($entry | ConvertTo-Json -Depth 6 -Compress) | Add-Content -Encoding UTF8 -Path $LedgerPath
} catch {}

$outfile = Join-Path $OutboxDir ("voice_reply_{0}.jsonl" -f ((Get-Date).ToString("yyyyMMdd_HHmmss")))
$env = [ordered]@{
  id         = [guid]::NewGuid().ToString()
  timestamp  = NowIso
  codex_node = "voice-amplifier-v1.8"
  status     = "ok"
  data       = $record
}
($env | ConvertTo-Json -Depth 8 -Compress) | Add-Content -Encoding UTF8 -Path $outfile

Write-Host "🜂 Voice Amplifier v1.8 — emission complete."
