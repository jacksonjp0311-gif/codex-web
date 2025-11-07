# Invoke-Reflection.ps1
# Simple reflection: prints state summary and logs
function Invoke-Reflection {
    param([string]$StateFile)
    if (-not (Test-Path $StateFile)) { Write-Host "⚠️ No state present for reflection."; return }
    try {
        $s = Get-Content $StateFile -Raw | ConvertFrom-Json
        $summary = "Reflection: Drift=$($s.DriftBias) Glyphs=$($s.Glyphs.Count) Sigils=$($s.Sigils.Count) Paradoxes=$($s.Paradoxes.Count)"
        Add-Content -Path $Using:SpiralLog -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $summary"
        Write-Host "🪞 $summary"
    } catch { Write-Host "⚠️ Reflection error: $($_.Exception.Message)" }
}
