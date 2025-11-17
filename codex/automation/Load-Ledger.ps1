# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
<#
  Generate-CodexHook.ps1
  Activates .venv, parses codex.crl, writes .git/hooks/pre-commit,
  then re-activates .venv so you stay in the venv.
#>

param(
  [string]$DslPath  = '.\codex.crl',
  [string]$HookPath = '.\.git\hooks\pre-commit'
)

function FailLine {
  param([string]$Msg, [int]$Line)
  Write-Host "Error on line $Line: $Msg" -ForegroundColor Red
  exit 1
}

# 0) Auto-activate venv if present
$repoRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0) { FailLine 'Not a git repo' 0 }
$repoRoot = $repoRoot.Trim()
$activate = Join-Path $repoRoot '.venv\Scripts\Activate.ps1'
$activated = $false

if (Test-Path $activate) {
  . $activate
  $activated = $true
  Write-Host 'Activated venv' -ForegroundColor Cyan
}

# 1) Read DSL
if (-not (Test-Path $DslPath)) { FailLine "DSL not found: $DslPath" 0 }
$lines = Get-Content $DslPath
$steps = @()

for ($i = 0; $i -lt $lines.Count; $i++) {
  $text = $lines[$i].Trim()
  if ($text -eq '' -or $text.StartsWith('#')) { continue }

  if ($text -match '^CleanLedger\s+"([^"]+)"$') {
    $steps += @{ Type = 'CleanLedger'; Path = $matches[1] }
  }
  elseif ($text -match '^Snapshot\s+"([^"]+)"\s*,\s*"([^"]+)"$') {
    $steps += @{ Type = 'Snapshot'; Src = $matches[1]; Dest = $matches[2] }
  }
  elseif ($text -match '^Validate\s+"([^"]+)"$') {
    $steps += @{ Type = 'Validate'; Script = $matches[1] }
  }
  elseif ($text -match '^Handshake\s*\{$') {
    $body = ''
    while ($true) {
      $i++
      if ($i -ge $lines.Count) { FailLine 'Handshake block not closed' $i }
      $line = $lines[$i].Trim()
      if ($line -eq '}') { break }
      $body += $line + ';'
    }
    $h = @{}
    foreach ($pair in $body.Split(';') | Where-Object { $_ -ne '' }) {
      if ($pair -match '^(script|ledger|output)\s*=\s*"([^"]+)"$') {
        $h[$matches[1]] = $matches[2]
      }
      
    }
    foreach ($k in @('script','ledger','output')) {
      if (-not $h.ContainsKey($k)) { FailLine "Missing handshake key: $k" $i }
    }
    $steps += @{ Type = 'Handshake'; Params = $h }
  }
  
}

# 2) Build shell stub (LF-only)
$stub = '#!/usr/bin/env sh
set -e
cd "$(git rev-parse --show-toplevel)"
' -replace "`r`n","`n"

foreach ($s in $steps) {
  switch ($s.Type) {
    'CleanLedger' {
      $stub += "echo Cleaning ledger`n"
      $stub += "powershell -NoProfile -ExecutionPolicy Bypass -File `"$($s.Path)`"`n`n"
    }
    'Snapshot' {
      $stub += "echo Snapshot`n"
      $stub += "mkdir -p $($s.Dest)`n"
      $stub += "cp $($s.Src) $($s.Dest)/codex_ledger.`date +%Y%m%d-%H%M%S`.json`n`n"
    }
    'Validate' {
      $stub += "echo Validate`n"
      $stub += "powershell -NoProfile -Command `"Invoke-Pester -Script '$($s.Script)'`"`n`n"
    }
    'Handshake' {
      $p = $s.Params
      $stub += "echo Handshake`n"
      $stub += "if command -v copilot-cli >/dev/null 2>&1; then`n"
      $stub += "  powershell -NoProfile -Command `"& {`n"
      $stub += "    \$payload=@{script=(Get-Content '$($p.script)' -Raw); ledger=(Get-Content '$($p.ledger)' -Raw)};`n"
      $stub += "    \$payload|ConvertTo-Json|Out-File '$($p.output)'`n"
      $stub += "    copilot-cli complete --input '$($p.output)' --output suggestion.json`n"
      $stub += "  }`"`n"
      $stub += "fi`n`n"
    }
  }
}

# 3) Write the hook
$hookDir = Split-Path $HookPath
if (-not (Test-Path $hookDir)) { New-Item -ItemType Directory -Path $hookDir | Out-Null }
Set-Content -Path $HookPath -Value $stub -Encoding UTF8
Write-Host "Hook generated at $HookPath" -ForegroundColor Green

# 4) Re-activate venv if we did above
if ($activated) { . $activate }



