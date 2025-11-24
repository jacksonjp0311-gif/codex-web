param(
    [string]$Intent = "oracle_phrase",
    [string]$Payload = ""
)

$ErrorActionPreference = "Stop"
$root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
Set-Location $root

$codexBridge = "C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\bridge\codex_bridge_v1_3.ps1"

# Call Codex bridge v1.3
if (Test-Path $codexBridge) {
    & $codexBridge -Intent $Intent -Payload $Payload
}

# Fallback empty JSON array on failure
if (-not (Test-Path $codexBridge)) {
    Write-Output "[]"
}
