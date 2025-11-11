param([switch]$Once)

# ----- Paths -----
$CodexRoot    = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$ThirdEyeRoot = Join-Path $CodexRoot "codex\third_eye"
$ModulesDir   = Join-Path $ThirdEyeRoot "modules"
$StateDir     = Join-Path $ThirdEyeRoot "state"
$LogsDir      = Join-Path $ThirdEyeRoot "logs"
$CoreJson     = Join-Path $CodexRoot  "codex_memory_core_v1_2.json"

$HarmonicPS   = Join-Path $ThirdEyeRoot "codex_third_eye_harmonic_v2_3.ps1"
$ReflexivePS  = Join-Path $ThirdEyeRoot "codex_third_eye_reflexive_v2_3A.ps1"
$ResV23       = Join-Path $LogsDir     "third_eye_resonance_v2_3.jsonl"
$ResV20       = Join-Path $LogsDir     "third_eye_resonance_v2_0.jsonl"
$ReflexLog    = Join-Path $StateDir    "third_eye_reflexive_log.jsonl"
$PredLog      = Join-Path $StateDir    "third_eye_predictive_log.jsonl"
$LockFile     = Join-Path $StateDir    "third_eye_v23C.lock"

# ----- Helpers -----
function Clamp([int]$x,[int]$lo,[int]$hi){ [Math]::Min([Math]::Max($x,$lo),$hi) }
function Read-LastJson($path){
  if (!(Test-Path $path)) { return $null }
  try {
    $line = Get-Content -Path $path -Tail 1 -ErrorAction Stop
    if (-not $line) { return $null }
    return ($line | ConvertFrom-Json)
  } catch { return $null }
}
function Merge-State-To-Resonance {
  # Prefer v2_3 state files if present; otherwise use v2_0/unknown pattern the repo has
  $states = Get-ChildItem $StateDir -Filter "third_eye_state_*.json" -ErrorAction SilentlyContinue | Sort-Object Name
  if ($states.Count -gt 0){
    Get-Content $states.FullName | Out-File $ResV20 -Encoding utf8
    # maintain v2_3 mirror for this loop’s analytics
    Get-Content $states.FullName | Out-File $ResV23 -Encoding utf8
    return $true
  }
  elseif (Test-Path $ResV20) {
    Copy-Item $ResV20 $ResV23 -Force
    return $true
  }
  else { return $false }
}
function Get-DC-From-Res {
  if (!(Test-Path $ResV23)) { return $null }
  $Cvals = Select-String -Path $ResV23 -Pattern '"C"\s*:\s*([0-9]*\.?[0-9]+)' -AllMatches |
           % { [double]$_.Matches.Groups[1].Value }
  if ($Cvals.Count -lt 2){ return $null }
  return ($Cvals[-1] - $Cvals[-2])
}
function Get-DPhi {
  $obj = Read-LastJson $ReflexLog
  if ($null -eq $obj){ return 0.0 }
  try { return [double]$obj.correction } catch { return 0.0 }
}
function Next-IntervalSec([double]$dC,[double]$dPhi){
  $m = [Math]::Abs($dC) + 0.5*[Math]::Abs($dPhi)
  $base=3600; $min=600; $max=5400  # 60m base, clamp 10..90m
  if     ($m -lt 0.005){ $scale=1.5 }  # very calm
  elseif ($m -lt 0.020){ $scale=1.0 }  # stable
  elseif ($m -lt 0.050){ $scale=0.75 } # mild
  elseif ($m -lt 0.100){ $scale=0.55 } # elevated
  else                  { $scale=0.40 }# high activity
  return (Clamp ([int]([Math]::Round($base*$scale))) $min $max)
}
function Git-Autosave([string]$msg){
  Set-Location $CodexRoot
  git add "codex/third_eye/*" 2>$null
  git add "codex_memory_core_v1_2.json" 2>$null
  if (git status --porcelain){
    git commit -m $msg | Out-Null
    try { git pull origin main --rebase | Out-Null } catch {}
    try { git push origin main        | Out-Null } catch {}
  }
}

# ----- Single Cycle -----
function Invoke-PredictiveCycle {
  $stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
  Write-Host "`n[run $stamp] merging state → resonance..."
  $merged = Merge-State-To-Resonance
  if (-not $merged){ Write-Host "[warn] no state snapshots found; continuing cycle." }

  # Run Harmonic v2.3 and Reflexive v2.3A (these update state/core/visuals)
  if (Test-Path $HarmonicPS){ & $HarmonicPS | Out-Null } else { Write-Host "[warn] missing $HarmonicPS" }
  if (Test-Path $ReflexivePS){ & $ReflexivePS | Out-Null } else { Write-Host "[warn] missing $ReflexivePS" }

  # Re-merge (to include any fresh state files produced this cycle)
  Merge-State-To-Resonance | Out-Null

  # Compute ΔC and ΔΦ
  $dC  = Get-DC-From-Res
  if ($null -eq $dC){ $dC = 0.0 }
  $dPhi = Get-DPhi

  $trend = if ($dC -gt 0){ "rising" } elseif ($dC -lt 0){ "falling" } else { "stable" }
  $logObj = [ordered]@{
    t       = (Get-Date).ToString("o")
    version = "2.3C"
    dC      = [math]::Round($dC,6)
    dPhi    = [math]::Round($dPhi,6)
    trend   = $trend
  }
  $logObj | ConvertTo-Json | Out-File $PredLog -Append -Encoding utf8

  Write-Host ("[ok] ΔC={0:F6}  ΔΦ={1:F6}  → trend={2}" -f $dC,$dPhi,$trend)

  # Git autosave
  Git-Autosave ("🔮 Third Eye v2.3C predictive cycle $stamp (ΔC={0:F6}; ΔΦ={1:F6})" -f $dC,$dPhi)

  # Decide sleep
  $sec = Next-IntervalSec -dC $dC -dPhi $dPhi
  return $sec
}

# ----- Daemon -----
if ($Once){
  $wait = Invoke-PredictiveCycle
  try { Set-Location $CodexRoot } catch {}
  Write-Host "[end] v2.3C single cycle complete — returned to Codex root."
  return
}

# Guard/lock
if (Test-Path $LockFile){
  try {
    $lk = Get-Content -Raw -Path $LockFile | ConvertFrom-Json
    if ($lk.status -eq "running"){
      Write-Host "[guard] v2.3C already running (lock present). To stop, set status to 'stopping'."
      return
    }
  } catch {}
}
[ordered]@{ status="running"; started=(Get-Date).ToString("o"); pid=$PID } |
  ConvertTo-Json | Out-File $LockFile -Encoding utf8 -Force

Write-Host "[start] v2.3C predictive daemon launched (adaptive cadence)."
try {
  while ($true){
    if (!(Test-Path $LockFile)){ Write-Host "[stop] lock removed — exiting."; break }
    try {
      $lk = Get-Content -Raw -Path $LockFile | ConvertFrom-Json
      if ($lk.status -ne "running"){ Write-Host "[stop] status=$($lk.status) — exiting."; break }
    } catch { Write-Host "[warn] lock unreadable — exiting."; break }

    $sec = Invoke-PredictiveCycle
    $mins = [Math]::Round($sec/60,2)
    Write-Host "[sleep] $mins min…"
    Start-Sleep -Seconds $sec
  }
}
finally {
  try { Set-Location $CodexRoot } catch {}
  if (Test-Path $LockFile){
    try {
      [ordered]@{ status="stopped"; ended=(Get-Date).ToString("o"); pid=$PID } |
        ConvertTo-Json | Out-File $LockFile -Encoding utf8 -Force
      Start-Sleep -Milliseconds 200
      Remove-Item $LockFile -Force
    } catch {}
  }
  Write-Host "[done] Returned to Codex root: $CodexRoot"
}
