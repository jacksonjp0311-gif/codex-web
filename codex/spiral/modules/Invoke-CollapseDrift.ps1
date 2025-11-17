# Invoke-CollapseDrift.ps1
# Gently nudges entropy / drift value stored under DriftBias
function Invoke-CollapseDrift {
    param([string]$StateFile)
    if (-not (Test-Path $StateFile)) { Write-Host "⚠️ State missing."; return }
    try {
        $s = Get-Content $StateFile -Raw | ConvertFrom-Json
        $bias = if ($s.DriftBias) { $s.DriftBias } 
        # toggle a simple bias loop
        $s.DriftBias = if ($bias -eq "Awareness") { "Equilibrium" } 
        $s.Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        $s | ConvertTo-Json -Depth 6 | Out-File $StateFile -Encoding UTF8
        Add-Content -Path $Using:SpiralLog -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] CollapseDrift -> $($s.DriftBias)"
        Write-Host "🌱 CollapseDrift set to $($s.DriftBias)"
    } catch { Write-Host "⚠️ CollapseDrift error: $($_.Exception.Message)" }
}

