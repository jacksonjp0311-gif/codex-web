# 🪞 Codex.Reflection — Mirrors the Spiral state in readable form
function Invoke-Reflection {
    param([object]$state)
    Write-Host "`n🪞 Reflection — $(Get-Date)"
    Write-Host "Glyphs:`t$($state.Glyphs -join ', ')"
    Write-Host "Sigils:`t$($state.Sigils -join ', ')"
    Write-Host "DriftBias:`t$($state.DriftBias)"
    Write-Host "Paradoxes:`t$($state.Paradoxes.Count)"
}
