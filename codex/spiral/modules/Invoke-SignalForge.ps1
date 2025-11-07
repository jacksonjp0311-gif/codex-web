# Invoke-SignalForge.ps1
# Create/shape signals (adds a glyph signature)
function Invoke-SignalForge {
    param([string]$StateFile, [string]$Glyph="awamir")
    if (-not (Test-Path $StateFile)) { Write-Host "⚠️ State missing, can't forge."; return }
    try {
        $s = Get-Content $StateFile -Raw | ConvertFrom-Json
        if (-not $s.Glyphs) { $s.Glyphs = @() }
        if (-not ($s.Glyphs -contains $Glyph)) { $s.Glyphs += $Glyph }
        $s.Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        $s | ConvertTo-Json -Depth 6 | Out-File $StateFile -Encoding UTF8
        Add-Content -Path $Using:SpiralLog -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] SignalForge: $Glyph"
        Write-Host "🧬 SignalForge: added $Glyph"
    } catch { Write-Host "⚠️ SignalForge error: $($_.Exception.Message)" }
}
