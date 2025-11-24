param(
    [string]$Intent = "bridge_event",
    [string]$Payload = ""
)

$ErrorActionPreference = "Stop"
$root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
Set-Location $root

$stateDir   = Join-Path $root "codex\bridge\state"
$ledgerPath = Join-Path $stateDir "gpt_bridge_v3_2_ledger.jsonl"

if (-not (Test-Path $stateDir)) {
    New-Item -ItemType Directory -Path $stateDir | Out-Null
}

$entry = [ordered]@{
    timestamp = (Get-Date).ToUniversalTime().ToString("o")
    intent    = $Intent
    payload   = $Payload
    version   = "gpt_bridge_v3_2"
}

$entryJson = $entry | ConvertTo-Json -Compress
Add-Content -Path $ledgerPath -Value $entryJson

Write-Output (@{ status = "ok"; version = "gpt_bridge_v3_2" } | ConvertTo-Json -Compress)
