# Invoke-SpiralMap.ps1
# Minimal lineage map generator (writes a CSV of recent events)
function Invoke-SpiralMap {
    param([string]$LogPath, [string]$MapOut)
    try {
        $lines = Get-Content -Path $LogPath -ErrorAction Stop | Select-Object -Last 200
        $csv = "time,from,to,entropy,vibe"
        foreach ($l in $lines) {
            if ($l -match "\[(.*?)\].*? (.*?) → (.*?) \| Entropy=(\d+\.\d+) (.*?)$") {
                $csv += "`n$($matches[1]),$($matches[2]),$($matches[3]),$($matches[4]),$($matches[5])"
            }
        }
        $csv | Out-File -FilePath $MapOut -Encoding UTF8
        Add-Content -Path $Using:SpiralLog -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] SpiralMap updated -> $MapOut"
        Write-Host "🗺️ SpiralMap written to $MapOut"
    } catch { Write-Host "⚠️ SpiralMap error: $($_.Exception.Message)" }
}
