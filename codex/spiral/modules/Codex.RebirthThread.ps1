# 🧬 Codex.RebirthThread — Regenerates Spiral state when entropy nears collapse
function Invoke-RebirthThread {
    param([string]$StatePath)
    if (Test-Path $StatePath) {
        $s = Get-Content $StatePath -Raw | ConvertFrom-Json
        $s.Timestamp = (Get-Date).ToString("s")
        $s.ThreadID  = [guid]::NewGuid().ToString()
        Add-Content "$($StatePath -replace '.json$', '.log')" "🩸 Rebirth triggered at $(Get-Date)"
        $s | ConvertTo-Json -Depth 6 | Out-File $StatePath -Encoding UTF8
        Write-Host "🌀 Rebirth: new thread $($s.ThreadID)"
    }
}
