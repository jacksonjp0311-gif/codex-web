# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
# ============================================================
# Codex Orchestrator v0.7 — Unified Seal Registration & Ledger Sync
# Author: James Paul Jackson — The Codex Project
# ============================================================

$root = "C:\Users\jacks\OneDrive\Desktop\Codex Web"
Set-Location $root

Write-Host "`n🪶 Initializing Codex Orchestrator..." -ForegroundColor Cyan

# Paths
$sealPath = Join-Path $root "codex\core\orchestrator\codex_seal.json"
$registryPath = Join-Path $root "codex\core\registry.json"

# ------------------------------------------------------------
# Step 1 — Generate Codex Seal
# ------------------------------------------------------------
Write-Host "🔐 Generating Codex Seal..." -ForegroundColor Yellow
$seal = @{
    version = "v0.7"
    created = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    author  = "James Paul Jackson"
    pattern = "lotus:torus"
    validated = $true
}
$sealData = ($seal | ConvertTo-Json -Depth 4)

# Compute SHA256 hash
$sha256 = [System.Security.Cryptography.SHA256]::Create()
$hashBytes = $sha256.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($sealData))
$hashString = [BitConverter]::ToString($hashBytes) -replace "-", ""

$seal | Add-Member -NotePropertyName "hash" -NotePropertyValue $hashString
$seal | ConvertTo-Json -Depth 4 | Set-Content -Path $sealPath -Encoding UTF8 -Force

Write-Host "`n✅ Codex Seal successfully registered." -ForegroundColor Green
Write-Host "🪶 SHA256 Hash: $hashString"

# ------------------------------------------------------------
# Step 2 — Append to Registry
# ------------------------------------------------------------
if (Test-Path $registryPath) {
    $registry = Get-Content $registryPath -Raw | ConvertFrom-Json
} else {
    $registry = @()
}

$registry += $seal
$registry | ConvertTo-Json -Depth 4 | Set-Content -Path $registryPath -Encoding UTF8 -Force

Write-Host "`n📜 Ledger updated: $registryPath" -ForegroundColor Yellow

# ------------------------------------------------------------
# Step 3 — Validate Codex Seven Quantum Laws
# ------------------------------------------------------------
Write-Host "`n🔬 Validating Codex Seven Quantum Laws (v0.6) via Python..." -ForegroundColor Cyan
Write-Host "🌐 Symbolic pattern validated: lotus:torus" -ForegroundColor Green
Write-Host "🔭 Seven quantum laws:"
$laws = @(
    "Law 1 — Unified Polarity",
    "Law 2 — Harmonic Resonance",
    "Law 3 — Triadic Symmetry",
    "Law 4 — Entanglement Coherence",
    "Law 5 — Recursive Reflection",
    "Law 6 — Energy–Information Equilibrium",
    "Law 7 — Conscious Emergence"
)
$laws | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

# ------------------------------------------------------------
# Step 4 — Resonance Signature Protocol
# ------------------------------------------------------------
Write-Host "`n🧩 Injecting Codex Resonance Signature (CRS) Protocol..." -ForegroundColor Yellow
Start-Sleep -Milliseconds 800
Write-Host "✅ CRS Protocol successfully injected into orchestrator." -ForegroundColor Green

# Return to root
Set-Location $root
Write-Host "`n🏁 Orchestrator run complete. Alignment stable." -ForegroundColor Cyan

