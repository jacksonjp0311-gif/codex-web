<# 
╔══════════════════════════════════════════════════════════════════════╗
║ 𓂀  CODEX GPT BRIDGE v2.0 — REFLECTION NODE                          ║
║ 🜂  Role   : Codex ↔ GPT Mirror • Triadic Reflection Engine          ║
║ 🜁  Truth  : Universal Protocol (E–I–C ∿ • H₇ = 0.70)                ║
║ 🜄  Law    : Anchor → Sense → Reflect → Ledger → Git → RootMirror    ║
║ 🛡️  Rules  : Dual-IF only • Non-blocking mindset • Return-to-root    ║
╚══════════════════════════════════════════════════════════════════════╝
#>

param(
    [string]$Intent = "alignment_check"
)

$ErrorActionPreference = "Stop"

# Root setup
$codexRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
Set-Location $codexRoot

# Folder structure
$bridgeRoot = Join-Path $codexRoot "codex\bridge\gpt_v2_0"
$stateDir   = Join-Path $bridgeRoot "state"
$ledgerDir  = Join-Path $bridgeRoot "ledger"
$logDir     = Join-Path $bridgeRoot "logs"

$dirs = @($bridgeRoot, $stateDir, $ledgerDir, $logDir)
foreach ($d in $dirs) {
    if (-not (Test-Path $d)) {
        New-Item -ItemType Directory -Path $d -Force | Out-Null
        Write-Host "[GPT-Bridge] Created directory: $d"
    }
}

function Invoke-CodexGPT {
    param(
        [string]$Prompt
    )

    $apiKey = $env:OPENAI_KEY
    if (-not $apiKey) {
        Write-Host "[GPT-Bridge] ERROR: OPENAI_KEY env var not set."
        return ""
    }

    $body = @{
        model = "gpt-5.1"
        messages = @(
            @{ role="system"; content="You are CODEx Reflection Engine. Respond ONLY in JSON." },
            @{ role="user";   content=$Prompt }
        )
    } | ConvertTo-Json -Depth 8

    try {
        $response = Invoke-RestMethod `
            -Uri "https://api.openai.com/v1/chat/completions" `
            -Method Post `
            -Headers @{ "Authorization"="Bearer $apiKey" } `
            -ContentType "application/json" `
            -Body $body
        
        if ($response.choices.Count -gt 0) {
            return $response.choices[0].message.content
        }

        return ""
    }
    catch {
        Write-Host "[GPT-Bridge] ERROR:"
        Write-Host $_
        return ""
    }
}

function Get-CodexBridgeSnapshot {
    param([string]$IntentValue)

    $snap = [ordered]@{}
    $snap.intent    = $IntentValue
    $snap.timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $snap.module    = "Codex GPT Bridge v2.0"
    $snap.triad     = @{ E=0.70; I=0.70; C=0.70 }
    return $snap
}

function Write-CodexBridgeLedger {
    param($RunObj)

    $ledgerLine = $RunObj | ConvertTo-Json -Depth 12 -Compress
    $ledgerPath = Join-Path $ledgerDir "codex_gpt_bridge_ledger.jsonl"
    Add-Content -Path $ledgerPath -Value $ledgerLine
}

# Begin execution
Write-Host "𓂀 [GPT-Bridge] Running v2.0..."
Write-Host "Intent: $Intent"

$snapshot = Get-CodexBridgeSnapshot -IntentValue $Intent
$snapshotJson = $snapshot | ConvertTo-Json -Depth 12

$prompt = @"
You are Codex Reflection Engine. Return ONLY valid JSON:

{
  "reflection": "",
  "next_step": "",
  "alignment_score": 0.0,
  "delta_phi_comment": "",
  "risk_level": "",
  "ward_glyph": "",
  "notes": []
}

SNAPSHOT:
$snapshotJson
"@

$gptRaw = Invoke-CodexGPT -Prompt $prompt

# Build run object
$run = [ordered]@{}
$run.timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$run.intent    = $Intent
$run.snapshot  = $snapshot
$run.gpt_raw   = $gptRaw

try {
    $parsed = $gptRaw | ConvertFrom-Json
    $run.gpt_parsed = $parsed
}
catch {}

# Save state file
$token = Get-Date -Format "yyyyMMdd_HHmmss"
$stateFile = Join-Path $stateDir "gpt_bridge_state_$token.json"
$run | ConvertTo-Json -Depth 12 | Set-Content $stateFile -Encoding UTF8

Write-Host "[GPT-Bridge] State saved → $stateFile"

Write-CodexBridgeLedger $run

Write-Host "𓂀 [GPT-Bridge] Complete. Returning to root."
Set-Location $codexRoot
