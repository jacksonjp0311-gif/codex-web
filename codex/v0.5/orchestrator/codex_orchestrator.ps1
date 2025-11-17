# @CodexAligned: ⚛🌀🔺♾️ (Auto-Aligned)
# ===============================================
# Codex Seal Ledger Registration â€” Orchestrator Script
# Author: James Paul Jackson
# ===============================================

# 1. Move to project root
Set-Location "C:\Users\jacks\OneDrive\Desktop\Codex Web"

# 2. Define paths
$sealPath = $env:CODEX_SEAL_PATH
$ledgerPath = "$root\codex\core\registry.json"

# 3. Ensure seal file exists
if (!(Test-Path $sealPath)) {
    Write-Host "âŒ Seal file not found at $sealPath"
    exit 1
}

# 4. Read seal and compute SHA-256
$bytes     = [System.IO.File]::ReadAllBytes($sealPath)
$sha       = [System.Security.Cryptography.SHA256]::Create()
$hashBytes = $sha.ComputeHash([byte[]]$bytes)
$sealHash  = [System.BitConverter]::ToString($hashBytes) -replace "-", ""
$sha.Dispose()

# 5. Construct new ledger entry
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$entry = @{
    timestamp  = $timestamp
    seal_path  = $sealPath
    seal_hash  = $sealHash
    status     = "verified"
    note       = "Codex Alignment Seal registration complete"
}

# 6. Load or initialize ledger
if (Test-Path $ledgerPath) {
    $ledgerJson = Get-Content $ledgerPath -Raw | ConvertFrom-Json
} 
}

# 6.5 Ensure ledger object exists before appending
if (-not ($ledgerJson) -or -not ($ledgerJson.PSObject.Properties.Name -contains "ledger")) {
    Write-Host "🧾 Initializing new ledger array..." -ForegroundColor DarkGray
    $ledgerJson = [PSCustomObject]@{ ledger = @() }
}
# 7. Append entry and save ledger
$ledgerJson.ledger += $entry
$ledgerJson | ConvertTo-Json -Depth 4 | Set-Content -Path $ledgerPath -Encoding UTF8

# 8. Create tag
$tagName = "v0.3-seal-" + (Get-Date -Format "yyyy-MM-dd-HH-mm-ss")

# 9. Output
Write-Host "✅ Codex Seal successfully registered.`n"
Write-Host "ðŸª¶ SHA256 Hash: $sealHash"
Write-Host "🏷️ Tag created: $tagName`n"
Write-Host "📜 Ledger updated: $ledgerPath`n"














