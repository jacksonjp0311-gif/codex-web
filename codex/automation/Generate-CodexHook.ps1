# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
<#
.SYNOPSIS
  Activates .venv, parses codex.crl (including multi-line Handshake),
  writes a LF-only UTF-8 pre-commit hook, then re-activates .venv.
#>

param(
  [string] $DslPath  = ".\codex.crl",
  [string] $HookPath = ".\.git\hooks\pre-commit"
)

function FailLine {
  param([string] $Msg, [int] $Line)
  Write-Host ("Error on line " + $Line + ": " + $Msg) -ForegroundColor Red
  exit 1
}

# 0) Auto-activate venv if present
$gitRoot = git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0) { FailLine "Not a git repository" 0 }
$gitRoot = $gitRoot.Trim()
$activateScript = Join-Path $gitRoot ".venv\Scripts\Activate.ps1"
$inVenv = $false
if (Test-Path $activateScript) {
  . $activateScript
  $inVenv = $true
  Write-Host "Activated .venv" -ForegroundColor Cyan
}

# 1) Read & parse codex.crl
if (-not (Test-Path $DslPath)) { FailLine ("DSL not found: " + $DslPath) 0 }
$lines = Get-Content $DslPath
$steps = @()

for ($i = 0; $i -lt $lines.Count; $i++) {
  $text = $lines[$i].Trim()
  if ($text -eq "" -or $text.StartsWith("#")) { continue }

  if ($text -match '^CleanLedger\s+"([^"]+)"$') {
    $steps += @{ Type="CleanLedger"; Path=$Matches[1] }
  }
  elseif ($text -match '^Snapshot\s+"([^"]+)"\s*,\s*"([^"]+)"$') {
    $steps += @{ Type="Snapshot"; Src=$Matches[1]; Dest=$Matches[2] }
  }
  elseif ($text -match '^Validate\s+"([^"]+)"$') {
    $steps += @{ Type="Validate"; Script=$Matches[1] }
  }
  elseif ($text -match '^Handshake\s*\{$') {
    $body = ""
    while ($true) {
      $i++
      if ($i -ge $lines.Count) { FailLine "Handshake block not closed" $i }
      $ln = $lines[$i].Trim()
      if ($ln -eq "}") { break }
      $body += $ln + ";"
    }
    $pairs = $body.Split(";") | Where-Object { $_ -ne "" }
    $h = @{}
    foreach ($p in $pairs) {
      if ($p -match '^(script|ledger|output)\s*=\s*"([^"]+)"$') {
        $h[$Matches[1]] = $Matches[2]
      } 
    }
    foreach ($k in @("script","ledger","output")) {
      if (-not $h.ContainsKey($k)) { FailLine ("Missing Handshake key: " + $k) $i }
    }
    $steps += @{ Type="Handshake"; Params=$h }
  }
  
}

# 2) Build LF-only shell stub
$stub = @'
#!/usr/bin/env sh
set -e
cd "$(git rev-parse --show-toplevel)"
'@ -replace "`r`n","`n"

foreach ($s in $steps) {
  switch ($s.Type) {
    "CleanLedger" {
      $stub += "echo Cleaning ledger`n"
      $stub += "powershell -NoProfile -ExecutionPolicy Bypass -File `"$($s.Path)`"`n`n"
    }
    "Snapshot" {
      $stub += "echo Snapshot`n"
      $stub += "mkdir -p $($s.Dest)`n"
      $stub += "cp $($s.Src) $($s.Dest)/codex_ledger.`$(date +%Y%m%d-%H%M%S).json`n`n"
    }
    "Validate" {
      $stub += "echo Validate`n"
      $stub += "powershell -NoProfile -Command `"Invoke-Pester -Script '$($s.Script)' -PassThru`"`n`n"
    }
    "Handshake" {
      $p = $s.Params
      $stub += "echo Handshake`n"
      $stub += "if command -v copilot-cli >/dev/null 2>&1; then`n"
      $stub += "  powershell -NoProfile -Command `"& {`n"
      $stub += "    \$payload=@{request=@{script=Get-Content '$($p.script)' -Raw;ledger=Get-Content '$($p.ledger)' -Raw}}`n"
      $stub += "    \$payload|ConvertTo-Json -Depth 5|Set-Content '$($p.output)'`n"
      $stub += "    copilot-cli complete --input '$($p.output)' --output suggestion.json`n"
      $stub += "  }`"`n"
      $stub += "fi`n`n"
    }
  }
}

# 3) Write the hook file
$hookDir = Split-Path $HookPath
if (-not (Test-Path $hookDir)) {
  New-Item -ItemType Directory -Path $hookDir | Out-Null
}
Set-Content -Path $HookPath -Value $stub


