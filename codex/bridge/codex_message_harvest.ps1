# ════════════════════════════════════════════════════════════════════════════════════
# ✉️  Write-CodexMessage — emit a structured reflection into Bridge inbox (PS5-safe)
# ════════════════════════════════════════════════════════════════════════════════════
param(
  [Parameter(Mandatory=$true)][string]$Message,
  [string]$Intent = "reflection",
  [string]$Agent  = "codex-core"
)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8

$CodexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$InboxDir  = Join-Path (Join-Path $CodexRoot "codex\bridge") "inbox"
New-Item -ItemType Directory -Force -Path $InboxDir | Out-Null

$msg = [ordered]@{
  id        = ([guid]::NewGuid().ToString())
  timestamp = (Get-Date).ToString("s")
  agent     = $Agent
  intent    = $Intent
  payload   = @{ message = $Message }
} | ConvertTo-Json -Depth 5 -Compress

Add-Content -Path (Join-Path $InboxDir "live_reflections.jsonl") -Value $msg
Write-Host "📡 Codex message emitted → Bridge inbox."