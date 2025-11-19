param([string]$Intent = "alignment_check")

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
Set-Location $root

$bridgeRoot = "C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\bridge\gpt_v2_1"
$stateDir   = "$bridgeRoot\state"
$ledgerDir  = "$bridgeRoot\ledger"
$glyphDir   = "$bridgeRoot\glyph"

$apiKey = $env:OPENAI_KEY
if (-not $apiKey) { Write-Host "ERROR: OPENAI_KEY not set."; return }

function Get-CodexGPTSnapshot {
    param([string]$IntentValue)
    $snap = [ordered]@{}
    $snap.intent = $IntentValue
    $snap.timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $snap.module = "Codex GPT Bridge v2.1"
    $snap.h_layers = "H1-H45 loaded"
    $snap.triad = @{E=0.70; I=0.70; C=0.70}
    return $snap
}

$snapshot = Get-CodexGPTSnapshot -IntentValue $Intent
$snapshotJson = $snapshot | ConvertTo-Json -Depth 12

function Invoke-CodexGPT {
    param([string]$Prompt)

    $body = @{
        model = "gpt-5.1"
        messages = @(
            @{ role="system"; content="Return ONLY JSON." }
            @{ role="user";   content=$Prompt }
        )
    } | ConvertTo-Json -Depth 12

    try {
        $res = Invoke-RestMethod `
            -Uri "https://api.openai.com/v1/chat/completions" `
            -Method Post `
            -Headers @{ "Authorization"="Bearer $apiKey" } `
            -ContentType "application/json" `
            -Body $body

        return $res.choices[0].message.content
    }
    catch {
        return ""
    }
}

$prompt = @"
{
  "reflection": "",
  "alignment_score": 0.0,
  "delta_phi_comment": "",
  "risk_level": "",
  "ward_glyph": "",
  "next_step": "",
  "notes": []
}

SNAPSHOT:
$snapshotJson
"@

$gptRaw = Invoke-CodexGPT -Prompt $prompt

try { $parsed = $gptRaw | ConvertFrom-Json }
catch { $parsed = $null }

$token = Get-Date -Format "yyyyMMdd_HHmmss"
$statePath  = Join-Path $stateDir  "gpt_bridge_state_$token.json"
$glyphPath  = Join-Path $glyphDir  "gpt_bridge_glyph.json"

$glyph = @{
    protocol="CodexTriadicGlyph";
    version="2.1";
    triad=@{
        energy=@{glyph="E"; value=0.70}
        information=@{glyph="I"; value=0.70}
        consciousness=@{glyph="C"; value=0.70}
    }
}

Set-Content $statePath -Value (([ordered]@{
    timestamp=$snapshot.timestamp
    intent=$Intent
    snapshot=$snapshot
    raw=$gptRaw
    parsed=$parsed
    glyph=$glyph
}) | ConvertTo-Json -Depth 20) -Encoding UTF8

Set-Content $glyphPath -Value ($glyph | ConvertTo-Json -Depth 10) -Encoding UTF8

$ledgerFile = Join-Path $ledgerDir "codex_gpt_bridge_ledger.jsonl"
Add-Content $ledgerFile -Value (([ordered]@{
    timestamp=$snapshot.timestamp
    intent=$Intent
    parsed=$parsed
}) | ConvertTo-Json -Compress -Depth 20)

Write-Host "[GPT BRIDGE v2.1] Cycle complete."
