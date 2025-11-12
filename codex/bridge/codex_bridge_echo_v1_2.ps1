param([string]$SingleFile = "")  # optionally process a specific JSONL

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

# paths
$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$BridgeDir = Join-Path $CodexRoot "codex\bridge"
$StateDir  = Join-Path $CodexRoot "codex\feedback\state"
$DashPath  = Join-Path $CodexRoot "codex\feedback\dashboard.html"

$ConvPath  = Join-Path $BridgeDir "conversation.jsonl"
$EchoMem   = Join-Path $BridgeDir "echo_memory.jsonl"
$EchoIndex = Join-Path $BridgeDir "state\echo_index.json"
$Log       = Join-Path $BridgeDir "echo_log.txt"
if (!(Test-Path $Log)) { New-Item -ItemType File -Path $Log | Out-Null }

function NowIso { (Get-Date).ToString("s") }
function SafeJson($x){ try { $x | ConvertFrom-Json } catch { $null } }

# read current codex metrics (best-effort)
$int  = (Get-Content -Raw -Encoding UTF8 (Join-Path $StateDir "codex_feedback_integration_state.json") -ea SilentlyContinue) | SafeJson
$harm = (Get-Content -Raw -Encoding UTF8 (Join-Path $StateDir "codex_harmonic_intelligence_v4_0.json") -ea SilentlyContinue)   | SafeJson
$seal = (Get-Content -Raw -Encoding UTF8 (Join-Path $StateDir "codex_temporal_seal_v3_9.json") -ea SilentlyContinue)          | SafeJson

$C_avg   = [double]($int.codex_feedback_integration.C_avg   + 0.0)
$C_local = [double]($int.codex_feedback_integration.C_local + 0.0)
$C_remote= [double]($int.codex_feedback_integration.C_remote+ 0.0)
$ΔH7     = [double]($int.codex_feedback_integration.'ΔH7'   + 0.0)
$C_next  = [double]($harm.codex_harmonic_intelligence.metrics.C_next + 0.0)
$H_idx   = [double]($harm.codex_harmonic_intelligence.metrics.harmonic_index + 0.0)
$H7      = 0.70
$ival    = $null
if ($seal -and $seal.codex_temporal_seal.state.interval_minutes) { $ival = [int]$seal.codex_temporal_seal.state.interval_minutes }

# pick source file(s)
$targets = @()
if ($SingleFile -and (Test-Path $SingleFile)) { $targets = @($SingleFile) }
elseif (Test-Path $ConvPath) { $targets = @($ConvPath) }

if (!$targets -or $targets.Count -eq 0) {
  Add-Content $Log ("[ECHO {0}] no conversation file(s) found." -f (NowIso))
  Write-Host "ℹ️ Echo: no conversation file(s) found."
  exit 0
}

# simple tokenizer
function Tokens([string]$s){
  ($s.ToLower() -replace "[^a-z0-9_@#]+"," ").Split(" ",[System.StringSplitOptions]::RemoveEmptyEntries)
}

# load last N lines from echo memory to compute rolling stats
$recentLines = @()
if (Test-Path $EchoMem) {
  $mem = Get-Content -Encoding UTF8 $EchoMem
  $recentLines = if ($mem.Count -gt 300) { $mem[-300..-1] } else { $mem }
}

$freq = @{}
$agents = New-Object System.Collections.Generic.HashSet[string]
$msgCount = 0
$now = Get-Date
$lastHour = $now.AddHours(-1)

# fold recent memory
foreach($l in $recentLines){
  try{
    $j = $l | ConvertFrom-Json
    if ($j.agent) { [void]$agents.Add([string]$j.agent) }
    if ($j.text){
      $msgCount++
      foreach($t in (Tokens $j.text)){
        if ($freq.ContainsKey($t)){ $freq[$t]++ } else { $freq[$t] = 1 }
      }
    }
  }catch{}
}

# process new conversation lines
foreach($file in $targets){
  try{
    $lines = Get-Content -Encoding UTF8 $file
    foreach($line in $lines){
      if (-not $line.Trim()){ continue }
      $j = $line | ConvertFrom-Json
      if ($j -eq $null){ continue }
      $t = if ($j.timestamp){ Get-Date $j.timestamp } else { Get-Date }
      $agent = if ($j.agent){ [string]$j.agent } else { "unknown" }
      $text  = "" + $j.text

      # append to echo memory
      $entry = [ordered]@{
        timestamp = $t.ToString("s")
        agent     = $agent
        text      = $text
      }
      Add-Content -Path $EchoMem -Value (($entry | ConvertTo-Json -Compress))

      # update rolling stats
      [void]$agents.Add($agent)
      $msgCount++
      foreach($tok in (Tokens $text)){
        if ($freq.ContainsKey($tok)){ $freq[$tok]++ } else { $freq[$tok] = 1 }
      }
    }
    Add-Content $Log ("[ECHO {0}] processed {1}" -f (NowIso), (Split-Path $file -Leaf))
  }catch{
    Add-Content $Log ("[ECHO {0}] ⚠️ file error {1}: {2}" -f (NowIso), $file, $_.Exception.Message)
  }
}

# compute top terms (excluding ultra-common)
$stop = @("the","and","or","to","a","of","in","for","on","is","it","this","that","with","be","are","as")
$top = $freq.GetEnumerator() | Where-Object { $stop -notcontains $_.Key -and $_.Key.Length -gt 2 } |
       Sort-Object Value -Descending | Select-Object -First 12

# build index
$index = [ordered]@{
  version          = "echo-v1.2"
  updated          = (NowIso)
  counts           = [ordered]@{
    messages_total = $msgCount
    unique_agents  = $agents.Count
  }
  top_terms        = @($top | ForEach-Object { @{ term = $_.Key; count = $_.Value } })
  codex_snapshot   = [ordered]@{
    H7 = $H7; C_avg = [math]::Round($C_avg,6); C_local = [math]::Round($C_local,6)
    C_remote = [math]::Round($C_remote,6); delta_Phi = [math]::Round($ΔH7,6)
    C_next = [math]::Round($C_next,6); harmonic_index = [math]::Round($H_idx,6)
    interval_min = $ival
  }
}
$index | ConvertTo-Json -Depth 8 | Out-File $EchoIndex -Encoding UTF8

# light dashboard tag
try {
  if (Test-Path $DashPath){
    $tag = "<p style='font-size:14px'>🗣️ Echo v1.2 @ $((Get-Date).ToString('s')) · msgs=$($msgCount) · agents=$($agents.Count) · top=$(($top | Select-Object -First 3 | ForEach-Object {$_.Key}) -join ', ')</p>"
    $html = Get-Content -Raw -Encoding UTF8 $DashPath
    if ($html -match "</body>"){ $html = $html -replace "</body>", "$tag`n</body>" } else { $html = $html + "`n$tag`n" }
    [IO.File]::WriteAllText($DashPath, $html, [Text.Encoding]::UTF8)
  }
}catch{
  Add-Content $Log ("[ECHO {0}] ⚠️ dashboard tag failed: {1}" -f (NowIso), $_.Exception.Message)
}

Write-Host "🔗 Echo v1.2 — conversation persisted, index updated, dashboard tagged."