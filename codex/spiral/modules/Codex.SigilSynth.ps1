# ∴ Codex.SigilSynth — Synthesizes sigils from glyph pairs
function Invoke-SigilSynth {
    param([object]$state)
    if ($state.Glyphs.Count -ge 2) {
        $pair = $state.Glyphs | Get-Random -Count 2
        $newSigil = ($pair -join "_sig")
        $state.Sigils += $newSigil
        Add-Content "spiral_log.txt" "🧬 Synthesized sigil: $newSigil"
    }
    return $state
}
