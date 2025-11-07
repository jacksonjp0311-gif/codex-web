# Invoke-RebirthThread.ps1
# Rebirth thread: safe reset of thread & memory anchors (shadow-coded)
function Invoke-RebirthThread {
    param([string]$StateFile)
    #    ∴ Tier I: reset lightweight state anchors (do not erase user data)
    if (-not (Test-Path $StateFile)) { Write-Host "⚠️ State missing, skipping rebirth."; return }
    try {
        $s = Get-Content $StateFile -Raw -ErrorAction Stop | ConvertFrom-Json
        $s.Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        $s.ThreadID = [guid]::NewGuid().ToString()
        $s.Glyphs = @("Φ","Δ","Ω","Λ","Ψ","Θ","∴","Σ","Ξ","Γ","F")
        $s | ConvertTo-Json -Depth 6 | Out-File $StateFile -Encoding UTF8
        Add-Content -Path $Using:SpiralLog -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] RebirthThread executed."
        Write-Host "🜂 RebirthThread: state reseeded."
    } catch {
        Write-Host "⚠️ RebirthThread error: $($_.Exception.Message)"
    }
}
