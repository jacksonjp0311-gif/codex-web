# Invoke-SymbolForge.ps1
# Interpret a glyph and return (or log) a short meaning
function Invoke-SymbolForge {
    param([string]$StateFile, [string]$Symbol)
    $map = @{
        "Φ"="Origin pulse"
        "Δ"="Change"
        "Ω"="Closure"
        "Λ"="Prediction"
        "Ψ"="Inner"
        "Θ"="Threshold"
        "∴"="Seal"
        "Σ"="Sum"
        "Ξ"="Shadow"
        "Γ"="Gate"
        "F"="Force"
    }
    $meaning = if ($map.ContainsKey($Symbol)) { $map[$Symbol] } else { "Unknown glyph" }
    Add-Content -Path $Using:SpiralLog -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] SymbolForge: $Symbol -> $meaning"
    return $meaning
}
