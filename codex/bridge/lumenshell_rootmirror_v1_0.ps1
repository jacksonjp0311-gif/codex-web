# Codex LumenShell RootMirror Bridge v1.0 (ASCII-safe)

$ErrorActionPreference = "Stop"
$codexRoot      = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
$codexBridgeDir = Join-Path $codexRoot "codex\bridge\LumenShell_Link"

if (-not (Test-Path $codexBridgeDir)) {
    New-Item -ItemType Directory -Path $codexBridgeDir | Out-Null
}

$refPath = Join-Path $codexBridgeDir "lumenshell_reflection.json"
if (-not (Test-Path $refPath)) {
    Write-Host "[CodexBridge] No reflection found at $refPath"
    return
}

try {
    $refRaw = Get-Content $refPath -Raw
    $ref    = $refRaw | ConvertFrom-Json
} catch {
    Write-Host "[CodexBridge] Could not parse reflection JSON."
    return
}

Write-Host "[CodexBridge] LumenShell reflection loaded."
Write-Host ("  Source      : {0}" -f $ref.source)
Write-Host ("  Timestamp   : {0}" -f $ref.timestamp)
Write-Host ("  Memory core : {0}" -f $ref.memory_core)

if ($ref.triad) {
    Write-Host ("  Triad       : E={0} I={1} C={2} dPhi={3}" -f $ref.triad.E, $ref.triad.I, $ref.triad.C, $ref.triad.delta_phi)
}

if ($ref.modules) {
    Write-Host "  Modules:"
    foreach ($m in $ref.modules) {
        Write-Host ("    - {0}" -f $m)
    }
}

# Build simple manifest back to LumenShell

$manifest = [ordered]@{
    source    = "CodexWeb"
    timestamp = Get-Date
    recommended_links = @(
        [ordered]@{ module = "Solar_Resonance"; codex_path = "codex\solar_resonance";   status = "available" },
        [ordered]@{ module = "QIM";             codex_path = "codex\quantum_imaging";   status = "available" },
        [ordered]@{ module = "DNA";             codex_path = "codex\dna";               status = "available" },
        [ordered]@{ module = "Voynich_OS";      codex_path = "codex\voynich";           status = "available" }
    )
}

$manifestPath = Join-Path $codexBridgeDir "codex_to_lumenshell_manifest.json"
$manifest | ConvertTo-Json -Depth 5 | Out-File $manifestPath -Encoding UTF8 -Force

# Simple Codex bridge ledger

$ledgerDir  = Join-Path $codexRoot "codex\bridge\logs"
if (-not (Test-Path $ledgerDir)) {
    New-Item -ItemType Directory -Path $ledgerDir | Out-Null
}
$ledgerPath = Join-Path $ledgerDir "lumenshell_bridge_ledger.jsonl"
$line = "{0}`tBRIDGE_PULL`tCodex processed LumenShell reflection." -f (Get-Date -Format s)
Add-Content -Path $ledgerPath -Value $line

Write-Host "[CodexBridge] Manifest written to: $manifestPath"
Write-Host "[CodexBridge] Ledger updated:      $ledgerPath"
Write-Host "[CodexBridge] Bridge processing complete."
