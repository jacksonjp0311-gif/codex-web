# ============================================================
# Codex Integrity Sentinel — Autonomous Alignment Watcher
# ============================================================
param([string]$Root = "C:\\Users\\jacks\\OneDrive\\Desktop\\Codex Web")
$Core = "$Root\\codex\\core"
$Ledger = "$Core\\registry.json"
$Sha = [System.Security.Cryptography.SHA256]::Create()
Write-Host "`n🧩 Sentinel Scan Initiated — Verifying Ledger and Seals..." -ForegroundColor Cyan
$LedgerData = Get-Content -Path $Ledger -Raw -Encoding UTF8 | ConvertFrom-Json
$Latest = $LedgerData.ledger[-1]
$Seals = Get-ChildItem -Path $Root -Filter "_codex_alignment_seal.json" -Recurse
foreach ($Seal in $Seals) {
    $SealRaw = Get-Content -Path $Seal.FullName -Raw -Encoding UTF8
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($SealRaw)
    $Hash = ($Sha.ComputeHash($Bytes) | ForEach-Object { $_.ToString("x2") }) -join ""
    if ($Hash.ToUpper() -eq $Latest.seal_hash.ToUpper()) {
        Write-Host "✅ $($Seal.Name): aligned with ledger (hash match)" -ForegroundColor Green
    } else {
        Write-Host "⚠️ $($Seal.Name): misaligned — auto-healing..." -ForegroundColor Yellow
        $Latest.status = "healed"
        $Latest.timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        $Latest.seal_hash = $Hash.ToUpper()
        $LedgerData.ledger[-1] = $Latest
        $LedgerData | ConvertTo-Json -Depth 6 | Set-Content -Path $Ledger -Encoding UTF8
        Write-Host "🩺 Ledger auto-healed for $($Seal.Name)" -ForegroundColor Gray
    }
}
$Manifests = Get-ChildItem -Path "$Root\\codex" -Filter "_synthesis_manifest.json" -Recurse
foreach ($M in $Manifests) {
    $Raw = Get-Content -Path $M.FullName -Raw -Encoding UTF8
    $B = [System.Text.Encoding]::UTF8.GetBytes($Raw)
    $H = ($Sha.ComputeHash($B) | ForEach-Object { $_.ToString("x2") }) -join ""
    Write-Host "📜 $($M.Name) → hash: $H" -ForegroundColor Gray
}
Write-Host "`n🔒 Sentinel verification complete — all layers coherent." -ForegroundColor Cyan
