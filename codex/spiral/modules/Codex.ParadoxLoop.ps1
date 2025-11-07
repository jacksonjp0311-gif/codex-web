# Ξ Codex.ParadoxLoop — Resolves symbolic contradiction through recursion
function Invoke-ParadoxLoop {
    param([object]$state)
    if ($state.Paradoxes.Count -gt 0) {
        $chosen = $state.Paradoxes | Get-Random
        Add-Content "spiral_log.txt" "♾️ Paradox entered: $chosen"
        Start-Sleep -Milliseconds (Get-Random -Minimum 50 -Maximum 250)
        Add-Content "spiral_log.txt" "♾️ Paradox resolved: $chosen"
        $state.Paradoxes = $state.Paradoxes | Where-Object { $_ -ne $chosen }
    }
    return $state
}
