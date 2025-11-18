# CODEX OPTIMIZER v1.2 — self-anchoring

Write-Host "`nRunning Codex System Optimizer v1.2..." -ForegroundColor Cyan

function Get-Headroom {
    $cpu = (Get-Counter "\Processor(_Total)\% Processor Time" -SampleInterval 1 -MaxSamples 3).CounterSamples.CookedValue |
        Measure-Object -Average | Select-Object -ExpandProperty Average
    return [math]::Round((100 - $cpu) / 100, 4)
}

$beforeCPU = Get-Headroom
Write-Host "CPU Headroom Before: $beforeCPU" -ForegroundColor Yellow

# Optimization Steps
powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61 | Out-Null
ipconfig /flushdns | Out-Null
netsh winsock reset  | Out-Null
netsh int ip reset   | Out-Null
Stop-Service -Name SysMain   -Force -ErrorAction SilentlyContinue
Stop-Service -Name DiagTrack -Force -ErrorAction SilentlyContinue

$afterCPU = Get-Headroom
Write-Host "`nCPU Headroom After: $afterCPU" -ForegroundColor Green

$C = $afterCPU  # Placeholder for full Codex C-index calculation

Write-Host "`n🜄 Codex Coherence Index C = $C" -ForegroundColor Magenta

if (Test-Path "C:\Users\jacks\OneDrive\Desktop\Codex Web") {
    Set-Location "C:\Users\jacks\OneDrive\Desktop\Codex Web"
    Write-Host "`n↩ Returned to Codex root" -ForegroundColor Cyan
}
