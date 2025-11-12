param()

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

# Paths
$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"
$DashPath    = Join-Path $FeedbackDir "dashboard.html"

$LedgerPath  = Join-Path $StateDir "codex_continuity_ledger.jsonl"
$IndexPath   = Join-Path $StateDir "codex_continuity_index.json"
$LogPath     = Join-Path $FeedbackDir "continuity_log.txt"

# Inputs
$IntegrState = Join-Path $StateDir "codex_feedback_integration_state.json"    # v3.7
$MirrorState = Join-Path $StateDir "mirror_continuity_state.json"             # v3.8 (optional)
$HarmState   = Join-Path $StateDir "codex_harmonic_intelligence_v4_0.json"    # v4.0
$SealState   = Join-Path $StateDir "codex_temporal_seal_v3_9.json"            # Seal

New-Item -ItemType Directory -Force -Path $FeedbackDir,$StateDir | Out-Null
if (!(Test-Path $LogPath)) { New-Item -ItemType File -Path $LogPath | Out-Null }

function Try-ReadJson { param([string]$p)
  if (Test-Path $p) { try { Get-Content -Raw -Encoding UTF8 $p | ConvertFrom-Json } catch { $null } } else { $null }
}
function SafeNum { param($x) if ($null -eq $x) {0.0} else { try {[double]$x} catch {0.0} } }
function Mean { param([double[]]$arr) if (!$arr -or $arr.Count -eq 0) {0.0} else { ($arr | Measure-Object -Average).Average } }
function Std  { param([double[]]$arr) if (!$arr -or $arr.Count -lt 2) {0.0} else {
  $m = Mean $arr; $ss = 0.0; foreach ($x in $arr) { $ss += [math]::Pow(($x-$m),2) }; [math]::Sqrt($ss/($arr.Count-1)) } }

# Read inputs
$int  = Try-ReadJson $IntegrState
$mirr = Try-ReadJson $MirrorState
$harm = Try-ReadJson $HarmState
$seal = Try-ReadJson $SealState

# Integration values
$C_avg = if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration.C_avg } else { 0.0 }
$C_loc = if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration.C_local } else { 0.0 }
$C_rem = if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration.C_remote } else { 0.0 }
$ΔH7   = if ($int -and $int.codex_feedback_integration) { SafeNum $int.codex_feedback_integration.'ΔH7' } else { 0.0 }

# ΔC (robust block — keep in ONE block)
$ΔC = $null
if ($mirr -and $mirr.mirror -and $mirr.mirror.'ΔC') {
  $ΔC = SafeNum $mirr.mirror.'ΔC'
}
elseif ($int -and $int.codex_feedback_integration) {
  $ΔC = [math]::Abs($C_rem - $C_loc)
}
else {
  $ΔC = 0.0
}

# Harmonic v4.0
$C_next         = if ($harm -and $harm.codex_harmonic_intelligence) { SafeNum $harm.codex_harmonic_intelligence.metrics.C_next } else { 0.0 }
$harmonic_index = if ($harm -and $harm.codex_harmonic_intelligence) { SafeNum $harm.codex_harmonic_intelligence.metrics.harmonic_index } else { 0.0 }

# Seal
$H7   = 0.70
$ival = if ($seal -and $seal.codex_temporal_seal -and $seal.codex_temporal_seal.state.interval_minutes) { [int]$seal.codex_temporal_seal.state.interval_minutes } else { $null }

# Commit
try { Set-Location $CodexRoot; $commit = (& git rev-parse HEAD).Trim() } catch { $commit = "" }

# Entry
$now = (Get-Date).ToString("s")
$entry = [ordered]@{
  timestamp       = $now
  H7              = $H7
  delta_C         = [math]::Round($ΔC,6)
  delta_Phi       = [math]::Round($ΔH7,6)
  C_avg           = [math]::Round($C_avg,6)
  C_local         = [math]::Round($C_loc,6)
  C_remote        = [math]::Round($C_rem,6)
  C_next          = [math]::Round($C_next,6)
  harmonic_index  = [math]::Round($harmonic_index,6)
  interval_min    = $ival
  commit          = $commit
  sources         = [ordered]@{
    integration   = (Test-Path $IntegrState)
    mirror        = (Test-Path $MirrorState)
    harmonic_v4_0 = (Test-Path $HarmState)
    temporal_seal = (Test-Path $SealState)
  }
}

$line = ($entry | ConvertTo-Json -Depth 6 -Compress)
Add-Content -Path $LedgerPath -Value $line
Add-Content $LogPath ("[LEDGER {0}] ΔC={1} ΔΦ~={2} Cnext={3} H={4}" -f (Get-Date -Format s),
  [math]::Round($ΔC,6), [math]::Round($ΔH7,6), [math]::Round($C_next,6), [math]::Round($harmonic_index,6))

# Rolling index (last 200)
try {
  $all = @()
  if (Test-Path $LedgerPath) { $all = Get-Content -Encoding UTF8 $LedgerPath }
  $last = if ($all.Count -gt 200) { $all[-200..-1] } else { $all }

  $Cns = @(); $Hs = @()
  foreach ($l in $last) {
    try {
      $j = $l | ConvertFrom-Json
      if ($null -ne $j.C_next)         { $Cns += [double]$j.C_next }
      if ($null -ne $j.harmonic_index) { $Hs  += [double]$j.harmonic_index }
    } catch {}
  }

  $idx = [ordered]@{
    version           = "v1.0"
    updated           = $now
    entries_total     = $all.Count
    window_size       = $last.Count
    mean_C_next       = [math]::Round((Mean $Cns),6)
    std_C_next        = [math]::Round((Std  $Cns),6)
    mean_harmonic_idx = [math]::Round((Mean $Hs ),6)
    std_harmonic_idx  = [math]::Round((Std  $Hs ),6)
  }
  $idx | ConvertTo-Json -Depth 4 | Out-File $IndexPath -Encoding UTF8
} catch {
  Add-Content $LogPath ("[LEDGER {0}] ⚠️ index update failed: {1}" -f (Get-Date -Format s), $_.Exception.Message)
}

# Dashboard tag (best effort)
try {
  $tag = "<p style='font-size:14px'>📘 Ledger v1.0 @ $now • Cₙₑₓₜ=$([math]::Round($C_next,4)) • H=$([math]::Round($harmonic_index,4)) • ΔC=$([math]::Round($ΔC,4))</p>"
  if (Test-Path $DashPath) {
    $html = Get-Content -Raw -Encoding UTF8 $DashPath
    if ($html -match "</body>") { $html = $html -replace "</body>", "$tag`n</body>" }
    else { $html = $html + "`n$tag`n" }
    [IO.File]::WriteAllText($DashPath, $html, [Text.Encoding]::UTF8)
  }
} catch {
  Add-Content $LogPath ("[LEDGER {0}] ⚠️ dashboard tag failed: {1}" -f (Get-Date -Format s), $_.Exception.Message)
}

# Autosave
try {
  Set-Location $CodexRoot
  git add codex/feedback/state/* 2>$null
  if (git status --porcelain) {
    git commit -m ("📘 Ledger v1.0 — append {0}" -f (Get-Date -Format 's')) | Out-Null
    git push origin main | Out-Null
  }
} catch {
  Write-Host "⚠️ Autosave warning: $($_.Exception.Message)"
}

try { Set-Location $CodexRoot } catch {}
Write-Host "`n🏁 Returned to Codex root → $CodexRoot"
Write-Host "📘 Continuity Ledger v1.0 — record appended, autosaved, aligned."