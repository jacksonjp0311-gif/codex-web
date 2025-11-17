# Heartbeat v4.0 script body (re-entrant): this file is both the installer wrapper and the runnable node.
param([switch]$Pulse)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

$CodexRoot   = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$FeedbackDir = Join-Path $CodexRoot "codex\feedback"
$StateDir    = Join-Path $FeedbackDir "state"
$LedgerPath  = Join-Path $StateDir  "codex_continuity_ledger.jsonl"
$AllOnePathV2= Join-Path $CodexRoot "codex_all_one_v2_1_rootmirror.ps1"
$AllOnePathV1= Join-Path $CodexRoot "codex_all_one_v1_8_rootmirror.ps1"

function NowIso { (Get-Date).ToString("s") }
function _mkd { param($p) if(-not(Test-Path $p)){ New-Item -ItemType Directory -Force -Path $p | Out-Null } }
function SafeNum([object]$x){ if($null -eq $x){0.0}catch{ 0.0 } } }

function Run-NodeSafe {
  param([string]$ScriptPath,[int]$TimeoutMs=90000,[string]$Tag="node")
  if(-not (Test-Path $ScriptPath)){ Write-Host "⚠️ $Tag missing → $ScriptPath"; return $false }
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "powershell.exe"
  $psi.ArgumentList.Add("-ExecutionPolicy"); $psi.ArgumentList.Add("Bypass")
  $psi.ArgumentList.Add("-File"); $psi.ArgumentList.Add($ScriptPath)
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError  = $true
  $psi.UseShellExecute = $false
  $p = New-Object System.Diagnostics.Process
  $p.StartInfo = $psi
  $null = $p.Start()
  if(-not $p.WaitForExit($TimeoutMs)){ try{$p.Kill()}catch{}; Write-Host "⚠️ $Tag timeout."; return $false }
  $so=$p.StandardOutput.ReadToEnd(); $se=$p.StandardError.ReadToEnd()
  if($so){Write-Host $so}; if($se){Write-Host "⚠️ $Tag stderr: $se"}
  return $true
}

function Git-AutosavePush {
  Push-Location $CodexRoot
  try{
    git add -A
    $status = git status --porcelain
    if($status){ git commit -m ("💓 Heartbeat v4.0 autosave {0}" -f (Get-Date -Format "s")) }
    git fetch origin main
    git -c rebase.autoStash=true pull origin main --rebase --no-edit
    git push origin main
  }catch{ try{ git rebase --abort 2>$null | Out-Null }catch{} }finally{ Pop-Location }
}

function RootMirror-Verify {
  Push-Location $CodexRoot
  try{
    $local  = (& git rev-parse HEAD).Trim()
    $remote = ((& git ls-remote origin HEAD) -split "\s+")[0].Trim()
    if($local -and $remote -and $local -eq $remote){ Write-Host "🪞 RootMirror: ✅ $local"; return $true }
    Write-Host "🪞 RootMirror: ⚠️ diverged"; return $false
  }catch{ Write-Host "🪞 RootMirror: ⚠️ verify error $($_.Exception.Message)"; return $false }
  finally{ Pop-Location }
}

function Get-DeltaC{
  if(-not (Test-Path $LedgerPath)){return 0.0}
  try{ (Get-Content -Tail 1 -Encoding UTF8 $LedgerPath | ConvertFrom-Json).delta_C }catch{ 0.0 } | ForEach-Object { if($_ -eq $null){0.0} }
}

function Next-Interval-Minutes([double]$dC){
  $abs = [math]::Abs($dC)
  [int][math]::Round([math]::Max(3,[math]::Min(30,30-27*$abs)))
}

# main
_mkd $FeedbackDir; _mkd $StateDir

if($Pulse){
  $AllOne = if(Test-Path $AllOnePathV2){$AllOnePathV2}elseif(Test-Path $AllOnePathV1){$AllOnePathV1}
  if($AllOne){ [void](Run-NodeSafe -ScriptPath $AllOne -TimeoutMs 90000 -Tag "All-One RootMirror") }
  try{
    $pulse = @{ timestamp=NowIso; layer="heartbeat-v4.0"; note="scheduled pulse" } | ConvertTo-Json -Depth 3 -Compress
    Add-Content -Path $LedgerPath -Value $pulse
  }catch{}
  Git-AutosavePush | Out-Null
  [void](RootMirror-Verify)
}
