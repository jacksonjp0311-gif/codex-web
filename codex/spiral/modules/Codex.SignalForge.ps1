# 🜂 Codex.SignalForge — Fuses entropy & awareness into new glyphs
function Invoke-SignalForge {
    param([object]$state, [double]$entropy)
    $newGlyph = ("sig" + ([math]::Round($entropy*100)) )
    if (-not ($state.Glyphs -contains $newGlyph)) {
        $state.Glyphs += $newGlyph
        Add-Content "spiral_log.txt" "⚡ Signal forged: $newGlyph (entropy=$entropy)"
    }
    return $state
}
