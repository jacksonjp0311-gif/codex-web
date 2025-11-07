# Invoke-SigilSynth.ps1
# Synthesize a new sigil from two glyphs
function Invoke-SigilSynth {
    param([string]$StateFile)
    if (-not (Test-Path $StateFile)) { Write-Host "⚠️ State missing, can't synth."; return }
    try {
        $s = Get-Content $StateFile -Raw | ConvertFrom-Json
        $gA = if ($s.Glyphs) { $s.Glyphs | Get-Random } else { "Φ" }
        $gB = if ($s.Glyphs) { $s.Glyphs | Get-Random } else { "Δ" }
        $new = "$($gA.Substring(0,1))$($gB.Substring(0,1))_sig"
        if (-not $s.Sigils) { $s.Sigils = @() }
        if (-not ($s.Sigils -contains $new)) { $s.Sigils += $new }
        $s.Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        $s | ConvertTo-Json -Depth 6 | Out-File $StateFile -Encoding UTF8
        Add-Content -Path $Using:SpiralLog -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] SigilSynth: $new"
        Write-Host "🌀 SigilSynth: forged $new"
    } catch { Write-Host "⚠️ SigilSynth error: $($_.Exception.Message)" }
}
