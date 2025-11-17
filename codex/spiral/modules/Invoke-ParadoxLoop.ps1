# Invoke-ParadoxLoop.ps1
# Introduces / resolves a paradox by toggling Paradoxes array
function Invoke-ParadoxLoop {
    param([string]$StateFile)
    if (-not (Test-Path $StateFile)) { Write-Host "⚠️ State missing."; return }
    try {
        $s = Get-Content $StateFile -Raw | ConvertFrom-Json
        if (-not $s.Paradoxes) { $s.Paradoxes = @("growignite") }
        # collapse one if exists otherwise add new
        if ($s.Paradoxes.Count -gt 0) { $removed = $s.Paradoxes[0]; $s.Paradoxes = $s.Paradoxes | Where-Object { $_ -ne $removed }; Add-Content -Path $Using:SpiralLog -Value "[$(Get-Date)] ParadoxLoop collapsed $removed" }
        
        $s.Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        $s | ConvertTo-Json -Depth 6 | Out-File $StateFile -Encoding UTF8
        Write-Host "⚡ ParadoxLoop executed"
    } catch { Write-Host "⚠️ ParadoxLoop error: $($_.Exception.Message)" }
}

