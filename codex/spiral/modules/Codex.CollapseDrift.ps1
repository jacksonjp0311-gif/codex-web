# 🜂 Codex.CollapseDrift — Detects entropy divergence and resets drift
function Invoke-CollapseDrift {
    param([object]$state,[double]$entropy)
    if ($entropy -gt 4.5) {
        Add-Content "spiral_log.txt" "🔥 Entropy exceeded threshold — collapse drift triggered"
        $state.DriftBias = "Stability"
    }
    return $state
}
