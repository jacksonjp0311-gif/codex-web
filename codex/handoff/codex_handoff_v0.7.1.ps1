# Codex Handoff Script v0.7.1
# Single-file handoff bridge (generated)
$root = 'C:\Users\jacks\OneDrive\Desktop\Codex Web'
Set-Location $root
Write-Host 'Running Codex Handoff Bridge v0.7.1...'
# Restore state and sync ledger
$state = Get-Content 'C:\Users\jacks\OneDrive\Desktop\Codex Web\codex\handoff\handoff_state.json' -Raw | ConvertFrom-Json
$env:PYTHONPATH = '$root'
try {
    python -c "from codex.core.ledger_sync import sync_ledger; sync_ledger()" 2>
    Write-Host 'Ledger sync attempted.'
} catch {
    Write-Host 'Ledger sync failed or Python not present.'
}
Write-Host 'Handoff bridge complete.'
Set-Location $root
