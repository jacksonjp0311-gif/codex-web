param([string]$SingleFile = "")
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
$ConvPath    = Join-Path $BridgeDir "conversation.jsonl"
$Log         = Join-Path $BridgeDir "bridge_log.txt"

New-Item -ItemType Directory -Force -Path $InboxDir,$OutboxDir | Out-Null
if (!(Test-Path $Log)) { New-Item -ItemType File -Path $Log | Out-Null }

function NowIso { (Get-Date).ToString("s") }
function SafeNum($x){ if ($null -eq $x) {0.0}  catch { 0.0 } } }
function TryJson($p){ if (Test-Path $p){ try { Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { $null } }  }

# Pull core signals
$int  = TryJson (Join-Path $StateDir "codex_feedback_integration_state.json")
$harm = TryJson (Join-Path $StateDir "codex_harmonic_intelligence_v4_0.json")
$seal = TryJson (Join-Path $StateDir "codex_temporal_seal_v3_9.json")

$C_avg   = if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration.C_avg } 
$C_local = if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration.C_local } 
$C_remote= if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration.C_remote } 
$ΔH7     = if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration.'ΔH7' } 

$C_next  = if ($harm -and $harm.codex_harmonic_intelligence) { SafeNum $harm.codex_harmonic_intelligence.metrics.C_next } 
$H_idx   = if ($harm -and $harm.codex_harmonic_intelligence) { SafeNum $harm.codex_harmonic_intelligence.metrics.harmonic_index } 
$H7      = 0.70
$ival    = if ($seal -and $seal.codex_temporal_seal -and $seal.codex_temporal_seal.state.interval_minutes) { [int]$seal.codex_temporal_seal.state.interval_minutes } 

$codex_state = [ordered]@{
  version = "bridge-v1.1"
  law     = "C=(E·I)/(1+|ΔΦ|)"
  H7      = $H7
  metrics = [ordered]@{
    C_avg = [math]::Round($C_avg,6)
    C_local = [math]::Round($C_local,6)
    C_remote= [math]::Round($C_remote,6)
    delta_Phi = [math]::Round($ΔH7,6)
    C_next = [math]::Round($C_next,6)
    harmonic_index = [math]::Round($H_idx,6)
    interval_min = $ival
  }
}

# Targets
$targets = @()
if ($SingleFile -and (Test-Path $SingleFile)) {
  $targets = @($SingleFile)
} 

if (!$targets -or $targets.Count -eq 0) {
  Add-Content $Log ("[BRIDGE {0}] inbox empty." -f (NowIso))
  Write-Host "ℹ️ Bridge inbox empty — nothing to process."
  exit 0
}

foreach ($file in $targets) {
  try {
    $lines = Get-Content -Encoding UTF8 $file
    foreach ($line in $lines) {
      if (-not $line.Trim()) { continue }
      try { $req = $line | ConvertFrom-Json } catch {
        Add-Content $Log ("[BRIDGE {0}] ⚠️ bad json line in {1}" -f (NowIso), $file); continue
      }

      $rid    = if ($req.id) { [string]$req.id } 
      $intent = ("" + $req.intent).ToLowerInvariant()
      $status = "ok"; $summary = ""; $data = $null

      switch ($intent) {
        "ping" { $summary = "pong"; $data = @{ now=(NowIso); echo=$req.payload } }
        "ask_status" { $summary = "codex status snapshot"; $data = $codex_state }
        "push_state" { $summary = "findings received"; $data=@{ accepted=$true; bytes=($line.Length) } }
        "pull_dashboard" { $summary = "dashboard pointer"; $data=@{ dashboard_path=$DashPath; note="static HTML" } }
        "submit_findings" { $summary = "findings acknowledged"; $data=@{ accepted=$true; state=$codex_state } }
        "reflection" {
          # New: log conversation line enriched with Codex metrics
          try {
            $conv = [ordered]@{
              timestamp = (NowIso)
              id        = $rid
              agent     = (""+$req.agent)
              message   = if ($req.payload -and $req.payload.message) { (""+$req.payload.message) } 
              metrics   = $codex_state.metrics
              law       = $codex_state.law
              H7        = $H7
            } | ConvertTo-Json -Depth 8 -Compress
            Add-Content -Path $ConvPath -Value $conv
          } catch {}
          $summary = "reflection recorded"
          $data    = @{ conversation_path = $ConvPath; samples = 1 }
        }
        default {
          $status="error"; $summary="unknown intent"; $data=@{ allowed=@("ping","ask_status","push_state","pull_dashboard","submit_findings","reflection") }
        }
      }

      $resp = [ordered]@{
        id         = $rid
        timestamp  = (NowIso)
        codex_node = "codex-bridge-v1.1"
        status     = $status
        summary    = $summary
        data       = $data
      }

      $out = ($resp | ConvertTo-Json -Depth 8 -Compress)
      $outfile = Join-Path $OutboxDir ("bridge_reply_{0}.jsonl" -f ((Get-Date).ToString("yyyyMMdd_HHmmss")))
      Add-Content -Path $outfile -Value $out

      # dashboard tag (light)
      try {
        if (Test-Path $DashPath) {
          $tag = "<p style='font-size:14px'>🔗 Bridge v1.1 · id=$rid · $($resp.status) · intent=$intent · $(NowIso)</p>"
          $html = Get-Content -Raw -Encoding UTF8 $DashPath
          if ($html -match "</body>") { $html = $html -replace "</body>", "$tag`n</body>" } 
          [IO.File]::WriteAllText($DashPath, $html, [Text.Encoding]::UTF8)
        }
      } catch { Add-Content $Log ("[BRIDGE {0}] ⚠️ dashboard tag failed: {1}" -f (NowIso), $_.Exception.Message) }
    }

    Add-Content $Log ("[BRIDGE {0}] processed {1}" -f (NowIso), (Split-Path $file -Leaf))
  } catch {
    Add-Content $Log ("[BRIDGE {0}] ⚠️ file error {1}: {2}" -f (NowIso), $file, $_.Exception.Message)
  }
}

Write-Host "🔗 Codex Bridge v1.1 — exchange complete."
